/**
 * Client-side map chase video export via MediaRecorder + canvas.
 * Map frames are copied synchronously; stats are drawn with canvas text
 * (no html-to-image) so overlays stay stable and the encode stays smooth.
 */

export const MAP_VIDEO_MAX_DURATION_MS = 20_000;
export const MAP_VIDEO_MAX_WIDTH = 1920;
/** Common phone share size (TikTok / Reels / Shorts Full HD vertical). */
export const MAP_VIDEO_PHONE_WIDTH = 1080;
export const MAP_VIDEO_PHONE_HEIGHT = 1920;
const TARGET_FPS = 24;

export type MapVideoSizeMode = 'native' | 'phone';

type MapFitRect = { x: number; y: number; w: number; h: number };

export class MapVideoUnsupportedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MapVideoUnsupportedError';
  }
}

export class MapVideoAbortedError extends Error {
  constructor() {
    super('Recording aborted');
    this.name = 'MapVideoAbortedError';
  }
}

export type MapVideoHrCurve = {
  d: number[];
  hr: (number | null)[];
};

export type MapVideoOverlayStats = {
  distanceKm: number;
  /** Rounded BPM, or null when no HR. */
  hrBpm: number | null;
  /** Preformatted clock, e.g. 12:34 */
  elapsedLabel: string | null;
  /** Preformatted pace, e.g. 5'42" */
  paceLabel: string | null;
  /** 0–1 along the route, used to clip the heart-rate sparkline. */
  progress: number;
  hrCurve: MapVideoHrCurve | null;
  /** HUD-matching labels (i18n). */
  labels: {
    time: string;
    pace: string;
    hr: string;
    km: string;
  };
};

export type MapVideoEndCard = {
  dateLabel: string;
  headline: string;
  distanceLabel: string;
  distanceUnit: string;
  rows: { label: string; value: string }[];
};

export type MapVideoMarkerPoints = {
  start: { x: number; y: number };
  end: { x: number; y: number };
  /** Map canvas CSS size the points were projected in. */
  cssWidth: number;
  cssHeight: number;
};

const END_CARD_MS = 3200;

/**
 * Phone cover of a large (fullscreen) map shows much more ground at the same
 * zoom. Extra is tuned so the 9:16 frame matches a ~420px-tall card, not the
 * current viewport.
 */
export function phoneChaseZoomOutExtra(cssW: number, cssH: number): number {
  const w = Math.max(cssW, 2);
  const h = Math.max(cssH, 2);
  const cover = Math.max(MAP_VIDEO_PHONE_WIDTH / w, MAP_VIDEO_PHONE_HEIGHT / h);
  const visibleH = MAP_VIDEO_PHONE_HEIGHT / cover;
  const refH = 420;
  // Lower extra = closer. ~1.2× the previous phone framing.
  const baseExtra = 1.2 - Math.log2(1.45 / 1.2);
  return baseExtra - Math.log2(visibleH / refH);
}
/**
 * Print/static-style credit (docs.mapbox.com/help/dive-deeper/attribution).
 * Must be legible; size/color may match the theme — not a large watermark.
 */
const MAP_VIDEO_ATTRIBUTION = '© Mapbox, © OpenStreetMap';

function pickMimeType(): string {
  if (typeof MediaRecorder === 'undefined') return '';
  const candidates = [
    'video/webm;codecs=vp9',
    'video/webm;codecs=vp8',
    'video/webm',
  ];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return '';
}

function drawHrSpark(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  series: MapVideoHrCurve,
  progress: number
) {
  const pts: { t: number; v: number }[] = [];
  let min = Infinity;
  let max = -Infinity;
  const n = Math.min(series.d.length, series.hr.length);
  if (n < 2) return;
  const d0 = series.d[0];
  const span = series.d[n - 1] - d0 || 1;
  for (let i = 0; i < n; i++) {
    const v = series.hr[i];
    if (v == null || v <= 0) continue;
    min = Math.min(min, v);
    max = Math.max(max, v);
    pts.push({ t: (series.d[i] - d0) / span, v });
  }
  if (pts.length < 2 || !Number.isFinite(min) || !Number.isFinite(max)) return;
  const pad = max === min ? 8 : (max - min) * 0.12;
  const yMin = min - pad;
  const yMax = max + pad;
  const X = (t: number) => x + t * w;
  const Y = (v: number) =>
    y + h - ((v - yMin) / (yMax - yMin || 1)) * (h - 2) - 1;

  const stroke = (until: number, alpha: number, widthPx: number) => {
    ctx.beginPath();
    let started = false;
    for (const p of pts) {
      if (p.t > until + 0.0001) break;
      const px = X(p.t);
      const py = Y(p.v);
      if (!started) {
        ctx.moveTo(px, py);
        started = true;
      } else ctx.lineTo(px, py);
    }
    if (!started) return;
    ctx.strokeStyle = '#ff8a65';
    ctx.globalAlpha = alpha;
    ctx.lineWidth = widthPx;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.globalAlpha = 1;
  };

  stroke(1, 0.28, 1.5);
  stroke(Math.min(1, Math.max(0, progress)), 1, 2);
}

function drawStatsOverlay(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  stats: MapVideoOverlayStats,
  typeScale = 1
) {
  const distBase = Math.max(
    26,
    Math.min(Math.round(width * 0.046), Math.round(height * 0.14))
  );
  const metaBase = Math.max(
    13,
    Math.min(Math.round(width * 0.022), Math.round(distBase * 0.46))
  );
  const distSize = Math.round(distBase * typeScale);
  const metaSize = Math.round(metaBase * typeScale);
  const labelSize = Math.max(10, Math.round(metaSize * 0.72));
  const padX = Math.round(width * 0.04);
  const padBottom = Math.max(14, Math.round(height * 0.04));
  const rowGap = Math.max(10, Math.round(distSize * 0.28));

  const valueBaseline = height - padBottom;
  const labelBaseline = valueBaseline - metaSize - 6;
  const distBaseline = labelBaseline - labelSize - rowGap;

  const blockTop = distBaseline - Math.round(distSize * 0.82);
  const gradTop = Math.max(0, blockTop - Math.round(height * 0.06));
  const grad = ctx.createLinearGradient(0, gradTop, 0, height);
  grad.addColorStop(0, 'rgba(0,0,0,0)');
  grad.addColorStop(0.35, 'rgba(0,0,0,0.45)');
  grad.addColorStop(1, 'rgba(0,0,0,0.78)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, gradTop, width, height - gradTop);

  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#f5f5f7';
  ctx.font = `700 ${distSize}px system-ui, -apple-system, sans-serif`;
  const distText = stats.distanceKm.toFixed(2);
  ctx.fillText(distText, padX, distBaseline);
  const distW = ctx.measureText(distText).width;
  ctx.font = `500 ${Math.round(distSize * 0.38)}px system-ui, sans-serif`;
  ctx.fillStyle = 'rgba(245,245,247,0.72)';
  ctx.fillText(stats.labels.km, padX + distW + 8, distBaseline);

  const sparkW = Math.round(Math.min(Math.max(120, width * 0.26), 280));
  const sparkX = width - padX - sparkW;
  const textLimit = stats.hrCurve ? sparkX - 16 : width - padX;

  let x = padX;
  const gap = Math.round(width * 0.045);
  const paintMeta = (label: string, value: string) => {
    ctx.font = `600 ${labelSize}px system-ui, sans-serif`;
    const labelW = ctx.measureText(label).width;
    ctx.font = `600 ${metaSize}px system-ui, sans-serif`;
    const valueW = ctx.measureText(value).width;
    const colW = Math.max(labelW, valueW);
    if (x + colW > textLimit) return;
    ctx.fillStyle = 'rgba(245,245,247,0.55)';
    ctx.font = `600 ${labelSize}px system-ui, sans-serif`;
    ctx.fillText(label, x, labelBaseline);
    ctx.fillStyle = '#f5f5f7';
    ctx.font = `600 ${metaSize}px system-ui, sans-serif`;
    ctx.fillText(value, x, valueBaseline);
    x += colW + gap;
  };

  if (stats.elapsedLabel) paintMeta(stats.labels.time, stats.elapsedLabel);
  if (stats.paceLabel) paintMeta(stats.labels.pace, `${stats.paceLabel}/km`);
  if (stats.hrBpm != null) paintMeta(stats.labels.hr, `${stats.hrBpm} bpm`);

  if (stats.hrCurve) {
    drawHrSpark(
      ctx,
      sparkX,
      blockTop,
      sparkW,
      Math.max(36, valueBaseline - blockTop),
      stats.hrCurve,
      stats.progress
    );
  }
}

function drawMarker(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  color: string
) {
  ctx.beginPath();
  ctx.arc(x, y, 7, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#fff';
  ctx.stroke();
}

function mapPointToOutput(
  markers: MapVideoMarkerPoints,
  fit: MapFitRect,
  point: { x: number; y: number }
): { x: number; y: number } {
  return {
    x: fit.x + (point.x / markers.cssWidth) * fit.w,
    y: fit.y + (point.y / markers.cssHeight) * fit.h,
  };
}

/**
 * Compact corner credit — Mapbox only requires legible text (+ logo on live
 * maps). Heavy boxes / oversized type are not required.
 */
function drawMapAttribution(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number
) {
  const shortSide = Math.min(width, height);
  const fontSize = Math.max(9, Math.min(11, Math.round(shortSide * 0.009)));
  const padX = Math.max(8, Math.round(fontSize * 1.1));
  const padY = Math.max(6, Math.round(fontSize * 0.9));
  ctx.save();
  ctx.font = `500 ${fontSize}px system-ui, -apple-system, sans-serif`;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'bottom';
  const text = MAP_VIDEO_ATTRIBUTION;
  const x = width - padX;
  const y = height - padY;
  // Soft shadow for contrast; no solid plaque.
  ctx.shadowColor = 'rgba(0,0,0,0.65)';
  ctx.shadowBlur = 3;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 1;
  ctx.fillStyle = 'rgba(255,255,255,0.88)';
  ctx.fillText(text, x, y);
  ctx.restore();
}

function drawEndCard(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  card: MapVideoEndCard,
  markers: MapVideoMarkerPoints | null,
  mapFit: MapFitRect
) {
  if (markers && markers.cssWidth > 1 && markers.cssHeight > 1) {
    const start = mapPointToOutput(markers, mapFit, markers.start);
    const end = mapPointToOutput(markers, mapFit, markers.end);
    drawMarker(ctx, start.x, start.y, '#3ddc84');
    drawMarker(ctx, end.x, end.y, '#ff5a5f');
  }

  const scrimW = Math.round(width * 0.56);
  const grad = ctx.createLinearGradient(0, 0, scrimW, 0);
  grad.addColorStop(0, 'rgba(0,0,0,0.62)');
  grad.addColorStop(0.72, 'rgba(0,0,0,0.28)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, scrimW, height);

  // Cap by both axes so tall/narrow frames (e.g. 1080×1920) don't inflate type.
  // Nudge copy right of the left edge so it sits clearer over the route.
  const pad = Math.max(
    28,
    Math.round(Math.min(width, height) * 0.048) + Math.round(width * 0.028)
  );
  const dateSize = Math.max(
    12,
    Math.min(Math.round(width * 0.028), Math.round(height * 0.02))
  );
  const headSize = Math.max(
    15,
    Math.min(Math.round(width * 0.036), Math.round(height * 0.026))
  );
  const distSize = Math.max(
    34,
    Math.min(Math.round(width * 0.09), Math.round(height * 0.07))
  );
  const rowSize = Math.max(
    14,
    Math.min(Math.round(width * 0.032), Math.round(height * 0.024))
  );
  const labelSize = Math.max(
    10,
    Math.min(Math.round(width * 0.022), Math.round(height * 0.016))
  );
  const afterLabel = Math.max(4, Math.round(labelSize * 0.35));
  const afterValue = Math.max(12, Math.round(rowSize * 0.7));

  let y = Math.round(height * 0.14);
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';

  y += dateSize;
  ctx.fillStyle = 'rgba(255,255,255,0.78)';
  ctx.font = `500 ${dateSize}px system-ui, -apple-system, sans-serif`;
  ctx.fillText(card.dateLabel, pad, y);

  y += Math.round(headSize * 0.55) + headSize;
  ctx.fillStyle = '#fff';
  ctx.font = `600 ${headSize}px system-ui, -apple-system, sans-serif`;
  ctx.fillText(card.headline, pad, y);

  y += Math.round(distSize * 0.5) + distSize;
  ctx.font = `700 ${distSize}px system-ui, -apple-system, sans-serif`;
  ctx.fillText(card.distanceLabel, pad, y);
  const distW = ctx.measureText(card.distanceLabel).width;
  ctx.font = `500 ${Math.round(distSize * 0.34)}px system-ui, sans-serif`;
  ctx.fillStyle = 'rgba(255,255,255,0.82)';
  ctx.fillText(card.distanceUnit, pad + distW + 8, y - 4);

  y += Math.round(rowSize * 0.85);
  for (const row of card.rows) {
    y += labelSize;
    ctx.fillStyle = 'rgba(255,255,255,0.62)';
    ctx.font = `600 ${labelSize}px system-ui, sans-serif`;
    ctx.fillText(row.label, pad, y);
    y += afterLabel + rowSize;
    ctx.fillStyle = '#fff';
    ctx.font = `600 ${rowSize}px system-ui, sans-serif`;
    ctx.fillText(row.value, pad, y);
    y += afterValue;
  }
}

/** Scale map to fill the frame (crop overflow) — no letterbox bars. */
function fitCover(
  srcW: number,
  srcH: number,
  outW: number,
  outH: number
): MapFitRect {
  const scale = Math.max(outW / srcW, outH / srcH);
  const w = evenSize(srcW * scale);
  const h = evenSize(srcH * scale);
  return {
    x: Math.round((outW - w) / 2),
    y: Math.round((outH - h) / 2),
    w,
    h,
  };
}

function evenSize(n: number): number {
  return Math.max(2, Math.round(n / 2) * 2);
}

export type MapVideoCapturePhase = 'live' | 'ending';

export type StartMapVideoCaptureOptions = {
  mapCanvas: HTMLCanvasElement;
  /** When true, draw stats from getOverlayStats each frame. */
  includeHud?: boolean;
  getOverlayStats?: () => MapVideoOverlayStats | null;
  /** Zoom the map out to the full route before the closing still. */
  prepareEndCard?: () => Promise<void>;
  getEndCard?: () => MapVideoEndCard | null;
  /** Start / finish dots in map CSS pixels. Read each end-card frame. */
  getMarkerPoints?: () => MapVideoMarkerPoints | null;
  /** native = map CSS size; phone = 1080×1920 (9:16), cover-cropped. */
  sizeMode?: MapVideoSizeMode;
  maxDurationMs?: number;
  maxWidth?: number;
  /** Fires when leaving live chase for pullback + end-card stills. */
  onPhaseChange?: (phase: MapVideoCapturePhase) => void;
  /**
   * Cover scale from map CSS box → output (≥1). Hosts should thin Mapbox
   * line/circle paints by ~1/scale so strokes don't look oversized on phone.
   */
  onCoverScale?: (scale: number) => void;
};

export type MapVideoCapture = {
  readonly done: Promise<Blob>;
  stop: () => void;
  abort: () => void;
};

/**
 * Start capturing the map WebGL canvas (optionally composite canvas-drawn stats).
 */
export function startMapVideoCapture(
  opts: StartMapVideoCaptureOptions
): MapVideoCapture {
  const mimeType = pickMimeType();
  if (!mimeType || typeof MediaRecorder === 'undefined') {
    throw new MapVideoUnsupportedError('MediaRecorder / WebM not supported');
  }

  const src = opts.mapCanvas;
  const maxDurationMs = opts.maxDurationMs ?? MAP_VIDEO_MAX_DURATION_MS;
  const maxWidth = opts.maxWidth ?? MAP_VIDEO_MAX_WIDTH;
  const sizeMode = opts.sizeMode ?? 'native';
  const includeStats = Boolean(opts.includeHud && opts.getOverlayStats);

  // Match the on-screen map box. The WebGL buffer is pixelRatio-scaled and
  // can be a taller aspect than the CSS box, which made exports look narrower.
  const cssW = src.clientWidth || src.width;
  const cssH = src.clientHeight || src.height;
  if (cssW < 2 || cssH < 2) {
    throw new MapVideoUnsupportedError('Map canvas has no size');
  }

  let outW: number;
  let outH: number;
  let mapFit: MapFitRect;
  let coverScale: number;
  if (sizeMode === 'phone') {
    outW = MAP_VIDEO_PHONE_WIDTH;
    outH = MAP_VIDEO_PHONE_HEIGHT;
    mapFit = fitCover(cssW, cssH, outW, outH);
    coverScale = Math.max(outW / cssW, outH / cssH);
  } else {
    // Keep the WebGL buffer's pixels (retina) up to 1920px wide. Encoding the
    // CSS size threw away that detail and looked soft.
    const bufW = src.width || cssW;
    const limited = Math.min(bufW, maxWidth);
    const scale = limited / cssW;
    outW = evenSize(cssW * scale);
    outH = evenSize(cssH * scale);
    mapFit = { x: 0, y: 0, w: outW, h: outH };
    coverScale = 1;
  }
  opts.onCoverScale?.(coverScale);

  const composite = document.createElement('canvas');
  composite.width = outW;
  composite.height = outH;
  const ctx = composite.getContext('2d', { alpha: false });
  if (!ctx) {
    throw new MapVideoUnsupportedError('2D canvas unavailable');
  }
  ctx.fillStyle = '#0b0d10';
  ctx.fillRect(0, 0, outW, outH);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const stream = composite.captureStream(TARGET_FPS);
  const pixelRate = outW * outH * TARGET_FPS;
  const bits = Math.round(
    Math.min(24_000_000, Math.max(10_000_000, pixelRate * 0.42))
  );
  const chunks: Blob[] = [];
  const recorder = new MediaRecorder(stream, {
    mimeType,
    videoBitsPerSecond: bits,
  });

  recorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };

  let raf = 0;
  let active = true;
  let mode: 'live' | 'pullback' | 'card' = 'live';
  let endStarted = false;
  const startedAt = performance.now();
  let cardStarted = 0;
  let lastPaintAt = 0;
  const minFrameMs = 1000 / TARGET_FPS;
  let rejectDone: ((err: Error) => void) | null = null;
  let aborted = false;
  let endCard: MapVideoEndCard | null = null;

  const done = new Promise<Blob>((resolve, reject) => {
    rejectDone = reject;
    recorder.onerror = () => reject(new Error('MediaRecorder error'));
    recorder.onstop = () => {
      if (aborted) {
        reject(new MapVideoAbortedError());
        return;
      }
      const blob = new Blob(chunks, {
        type: mimeType.split(';')[0] || 'video/webm',
      });
      if (blob.size < 64) {
        reject(new Error('Recording produced an empty file'));
        return;
      }
      resolve(blob);
    };
  });

  const teardownTracks = () => {
    stream.getTracks().forEach((t) => t.stop());
  };

  const finalizeRecorder = () => {
    if (!active) return;
    active = false;
    cancelAnimationFrame(raf);
    if (recorder.state !== 'inactive') recorder.stop();
    teardownTracks();
  };

  const paintMap = () => {
    if (sizeMode === 'phone') {
      ctx.fillStyle = '#0b0d10';
      ctx.fillRect(0, 0, outW, outH);
    }
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(src, mapFit.x, mapFit.y, mapFit.w, mapFit.h);
  };

  const paintLive = () => {
    paintMap();
    if (includeStats && opts.getOverlayStats) {
      const stats = opts.getOverlayStats();
      if (stats)
        drawStatsOverlay(
          ctx,
          outW,
          outH,
          stats,
          sizeMode === 'phone' ? 1.32 : 1
        );
    }
    // Live frames also need credit — DOM logo/ⓘ never enter the WebGL buffer.
    drawMapAttribution(ctx, outW, outH);
  };

  const paintEnd = () => {
    paintMap();
    if (endCard) {
      drawEndCard(
        ctx,
        outW,
        outH,
        endCard,
        opts.getMarkerPoints?.() ?? null,
        mapFit
      );
    }
    drawMapAttribution(ctx, outW, outH);
  };

  const beginEndCard = () => {
    if (endStarted || !active) return;
    endStarted = true;
    mode = 'pullback';
    opts.onPhaseChange?.('ending');
    void (async () => {
      try {
        await Promise.race([
          opts.prepareEndCard?.() ?? Promise.resolve(),
          new Promise<void>((resolve) => {
            window.setTimeout(resolve, 2200);
          }),
        ]);
      } catch (err) {
        console.error(err);
      }
      if (!active) return;
      endCard = opts.getEndCard?.() ?? null;
      cardStarted = performance.now();
      mode = 'card';
    })();
  };

  const tick = (ts: number) => {
    if (!active) return;
    if (mode === 'live' && performance.now() - startedAt >= maxDurationMs) {
      beginEndCard();
    }
    if (mode === 'card' && performance.now() - cardStarted >= END_CARD_MS) {
      finalizeRecorder();
      return;
    }
    if (ts - lastPaintAt >= minFrameMs - 0.5) {
      lastPaintAt = ts;
      if (mode === 'live') paintLive();
      else if (mode === 'card') paintEnd();
      else {
        paintMap();
        drawMapAttribution(ctx, outW, outH);
      }
    }
    raf = requestAnimationFrame(tick);
  };

  recorder.start(250);
  paintLive();
  raf = requestAnimationFrame(tick);

  return {
    done,
    stop: () => beginEndCard(),
    abort: () => {
      aborted = true;
      cancelAnimationFrame(raf);
      active = false;
      if (recorder.state !== 'inactive') recorder.stop();
      else rejectDone?.(new MapVideoAbortedError());
      teardownTracks();
    },
  };
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 4_000);
}

export function defaultMapVideoFilename(): string {
  return `run-playback-${new Date()
    .toISOString()
    .slice(0, 19)
    .replace(/[:T]/g, '-')}.webm`;
}
