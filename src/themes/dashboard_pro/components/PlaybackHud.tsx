import { useEffect, useRef, useState } from 'react';
import { formatClock, formatPaceSeconds, loadSplits } from '@/core/splits';
import { useLocale } from '@/hooks/useLocale';
import type { PlaybackProgress, PlaybackSpeed } from '@/utils/mapChase3d';
import { setPlaybackPrefs, usePlaybackPrefs } from '@/utils/playbackPrefs';

export type HrSeries = { d: number[]; hr: (number | null)[] };
export type TimeSeries = { d: number[]; t: number[] };

export type PlaybackSeries = {
  hr: HrSeries | null;
  time: TimeSeries | null;
};

function interpolateHr(
  series: HrSeries | null,
  distanceKm: number
): number | null {
  if (!series || series.d.length === 0) return null;
  const { d, hr } = series;
  if (distanceKm <= d[0]) {
    const v = hr[0];
    return v != null && v > 0 ? v : null;
  }
  if (distanceKm >= d[d.length - 1]) {
    const v = hr[hr.length - 1];
    return v != null && v > 0 ? v : null;
  }
  let lo = 0;
  let hi = d.length - 1;
  while (lo + 1 < hi) {
    const mid = (lo + hi) >> 1;
    if (d[mid] <= distanceKm) lo = mid;
    else hi = mid;
  }
  const a = hr[lo];
  const b = hr[hi];
  if (a == null || a <= 0) return b != null && b > 0 ? b : null;
  if (b == null || b <= 0) return a;
  const span = d[hi] - d[lo];
  const t = span > 0 ? (distanceKm - d[lo]) / span : 0;
  return a + (b - a) * t;
}

function buildHrPath(
  series: HrSeries,
  progress: number,
  width: number,
  height: number
): { full: string; played: string } | null {
  const pts: { x: number; y: number }[] = [];
  let min = Infinity;
  let max = -Infinity;
  for (let i = 0; i < series.hr.length; i++) {
    const v = series.hr[i];
    if (v == null || v <= 0) continue;
    min = Math.min(min, v);
    max = Math.max(max, v);
    const x =
      series.d.length > 1
        ? ((series.d[i] - series.d[0]) /
            (series.d[series.d.length - 1] - series.d[0] || 1)) *
          width
        : 0;
    pts.push({ x, y: v });
  }
  if (pts.length < 2 || !Number.isFinite(min) || !Number.isFinite(max)) {
    return null;
  }
  const pad = max === min ? 10 : (max - min) * 0.12;
  const yMin = min - pad;
  const yMax = max + pad;
  const toY = (v: number) =>
    height - ((v - yMin) / (yMax - yMin || 1)) * (height - 2) - 1;
  const full = pts
    .map(
      (p, idx) =>
        `${idx === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${toY(p.y).toFixed(1)}`
    )
    .join(' ');
  const cutX = progress * width;
  const playedPts = pts.filter((p) => p.x <= cutX);
  if (playedPts.length === 0) return { full, played: '' };
  const last = playedPts[playedPts.length - 1];
  const next = pts.find((p) => p.x > cutX);
  if (next) {
    const t = (cutX - last.x) / (next.x - last.x || 1);
    playedPts.push({ x: cutX, y: last.y + (next.y - last.y) * t });
  }
  const played = playedPts
    .map(
      (p, idx) =>
        `${idx === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${toY(p.y).toFixed(1)}`
    )
    .join(' ');
  return { full, played };
}

export const PLAYBACK_SPEEDS: PlaybackSpeed[] = [1, 2, 4];

export function nextPlaybackSpeed(current: PlaybackSpeed): PlaybackSpeed {
  const i = PLAYBACK_SPEEDS.indexOf(current);
  return PLAYBACK_SPEEDS[(i + 1) % PLAYBACK_SPEEDS.length];
}

function interpolateNumber(
  d: number[],
  values: number[],
  distanceKm: number
): number | null {
  const n = Math.min(d.length, values.length);
  if (n === 0) return null;
  if (distanceKm <= d[0]) return values[0];
  if (distanceKm >= d[n - 1]) return values[n - 1];
  let lo = 0;
  let hi = n - 1;
  while (lo + 1 < hi) {
    const mid = (lo + hi) >> 1;
    if (d[mid] <= distanceKm) lo = mid;
    else hi = mid;
  }
  const span = d[hi] - d[lo];
  const t = span > 0 ? (distanceKm - d[lo]) / span : 0;
  return values[lo] + (values[hi] - values[lo]) * t;
}

/** Elapsed seconds at this distance. Chart timer time, else moving time × progress. */
export function playbackElapsedSec(
  time: TimeSeries | null,
  distanceKm: number,
  progress: number,
  movingTimeSec: number
): number | null {
  if (time && time.t.length > 0) {
    const sec = interpolateNumber(time.d, time.t, distanceKm);
    if (sec != null && sec >= 0) return sec;
  }
  if (movingTimeSec > 0) return movingTimeSec * progress;
  return null;
}

/** Average pace so far (s/km). Falls back to the activity average near 0 km. */
export function playbackAvgPaceSec(
  elapsedSec: number | null,
  distanceKm: number,
  averageSpeedMs: number
): number | null {
  if (distanceKm >= 0.05 && elapsedSec != null && elapsedSec > 0) {
    return elapsedSec / distanceKm;
  }
  if (averageSpeedMs > 0) return 1000 / averageSpeedMs;
  return null;
}

/** Load chart series for a run. HR and timer time are independent. */
export function usePlaybackSeries(
  active: boolean,
  runId: number | null
): PlaybackSeries | null {
  const [entry, setEntry] = useState<{
    runId: number;
    series: PlaybackSeries;
  } | null>(null);
  useEffect(() => {
    if (!active || runId == null) return;
    let cancelled = false;
    void loadSplits(runId).then((data) => {
      if (cancelled) return;
      const chart = data?.chart;
      const hasHr = Boolean(
        chart?.hr?.length &&
        chart.d?.length &&
        chart.hr.some((v) => v != null && v > 0)
      );
      const hasTime = Boolean(
        chart?.t?.length &&
        chart.d?.length &&
        chart.t.some((v) => v != null && v >= 0)
      );
      setEntry({
        runId,
        series: {
          hr: hasHr && chart ? { d: chart.d, hr: chart.hr! } : null,
          time: hasTime && chart?.t ? { d: chart.d, t: chart.t } : null,
        },
      });
    });
    return () => {
      cancelled = true;
    };
  }, [active, runId]);
  if (!active || runId == null || entry?.runId !== runId) return null;
  return entry.series;
}

function HrBpmStat({ label, bpm }: { label: string; bpm: number }) {
  return (
    <div className="route-playback-hud__stat">
      <span className="route-playback-hud__label">{label}</span>
      <span className="route-playback-hud__stat-value">
        {Math.round(bpm)}
        <span className="route-playback-hud__unit">bpm</span>
      </span>
    </div>
  );
}

export function PlaybackHudView({
  snap,
  hrSeries,
  timeSeries = null,
  movingTimeSec = 0,
  averageSpeedMs = 0,
  fullscreen = false,
  dark = true,
  exporting = false,
  exportEnding = false,
  exportMessage = null,
  onTogglePause,
  onCycleSpeed,
  onSeek,
  onExport,
  onShowEndpointsChange,
  onHeightChange,
}: {
  snap: PlaybackProgress;
  hrSeries: HrSeries | null;
  timeSeries?: TimeSeries | null;
  /** Activity moving time, used when the chart has no timer series. */
  movingTimeSec?: number;
  /** Activity average speed (m/s), used until pace-so-far is meaningful. */
  averageSpeedMs?: number;
  /** Expanded metrics: time / pace also shown. HR bpm shows in both modes. */
  fullscreen?: boolean;
  dark?: boolean;
  exporting?: boolean;
  /** True while pullback + end-card stills are encoding. */
  exportEnding?: boolean;
  exportMessage?: string | null;
  onTogglePause: () => void;
  onCycleSpeed: () => void;
  onSeek: (p: number) => void;
  /** Start export with chosen mode, or stop if already exporting. */
  onExport?: (opts: {
    includeHud: boolean;
    sizeMode: 'native' | 'phone';
  }) => void;
  /** Live start/finish pins. Persisted preference is applied by the caller. */
  onShowEndpointsChange?: (show: boolean) => void;
  onHeightChange?: (heightPx: number) => void;
}) {
  const { t } = useLocale();
  const prefs = usePlaybackPrefs();
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const exportWrapRef = useRef<HTMLDivElement>(null);
  const settingsWrapRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);
  const barRef = useRef<HTMLDivElement>(null);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [exportSizeMode, setExportSizeMode] = useState<'native' | 'phone'>(
    'native'
  );
  const hrNow = interpolateHr(hrSeries, snap.distanceKm);
  const sparkW = fullscreen ? 140 : 72;
  const sparkH = fullscreen ? 32 : 22;
  const spark = hrSeries
    ? buildHrPath(hrSeries, snap.progress, sparkW, sparkH)
    : null;
  const hasHr = hrSeries != null;
  const elapsed = playbackElapsedSec(
    timeSeries,
    snap.distanceKm,
    snap.progress,
    movingTimeSec
  );
  const avgPace = playbackAvgPaceSec(elapsed, snap.distanceKm, averageSpeedMs);

  useEffect(() => {
    if (!exportMenuOpen && !settingsOpen) return;
    const onDoc = (e: PointerEvent) => {
      if (!(e.target instanceof Node)) return;
      if (
        exportMenuOpen &&
        exportWrapRef.current &&
        !exportWrapRef.current.contains(e.target)
      ) {
        setExportMenuOpen(false);
      }
      if (
        settingsOpen &&
        settingsWrapRef.current &&
        !settingsWrapRef.current.contains(e.target)
      ) {
        setSettingsOpen(false);
      }
    };
    document.addEventListener('pointerdown', onDoc);
    return () => document.removeEventListener('pointerdown', onDoc);
  }, [exportMenuOpen, settingsOpen]);

  useEffect(() => {
    const el = rootRef.current;
    if (!el || !onHeightChange) return;
    const report = () => onHeightChange(el.getBoundingClientRect().height);
    report();
    const ro = new ResizeObserver(report);
    ro.observe(el);
    return () => ro.disconnect();
  }, [
    onHeightChange,
    fullscreen,
    exportMessage,
    exportMenuOpen,
    settingsOpen,
    prefs.showStats,
  ]);

  const ratioFromEvent = (clientX: number) => {
    const el = barRef.current;
    if (!el) return 0;
    const rect = el.getBoundingClientRect();
    return (clientX - rect.left) / (rect.width || 1);
  };

  return (
    <div
      ref={rootRef}
      className={`route-playback-hud ${dark ? 'is-dark' : 'is-light'} ${
        fullscreen ? 'is-expanded' : 'is-compact'
      }`}
    >
      <div
        ref={panelRef}
        className="route-playback-hud__panel"
        data-playback-hud-panel
      >
        {prefs.showStats ? (
          <div
            className="route-playback-hud__metrics"
            data-playback-hud-metrics
          >
            <div className="route-playback-hud__distance">
              <span className="route-playback-hud__value">
                {snap.distanceKm.toFixed(2)}
              </span>
              <span className="route-playback-hud__unit">km</span>
            </div>

            {/* While exporting stats, show the same expanded metrics as fullscreen. */}
            {fullscreen || exporting ? (
              <div className="route-playback-hud__extras">
                {elapsed != null && (
                  <div className="route-playback-hud__stat">
                    <span className="route-playback-hud__label">
                      {t('timeLabel')}
                    </span>
                    <span className="route-playback-hud__stat-value">
                      {formatClock(elapsed)}
                    </span>
                  </div>
                )}
                {avgPace != null && (
                  <div className="route-playback-hud__stat">
                    <span className="route-playback-hud__label">
                      {t('avgPace')}
                    </span>
                    <span className="route-playback-hud__stat-value">
                      {formatPaceSeconds(avgPace)}
                      <span className="route-playback-hud__unit">/km</span>
                    </span>
                  </div>
                )}
                {hasHr && hrNow != null && (
                  <HrBpmStat label={t('hr')} bpm={hrNow} />
                )}
              </div>
            ) : hasHr && hrNow != null ? (
              <div className="route-playback-hud__extras route-playback-hud__extras--compact">
                <HrBpmStat label={t('hr')} bpm={hrNow} />
              </div>
            ) : null}

            {hasHr && spark ? (
              <div className="route-playback-hud__spark" aria-hidden="true">
                <svg
                  viewBox={`0 0 ${sparkW} ${sparkH}`}
                  width={sparkW}
                  height={sparkH}
                >
                  <path
                    d={spark.full}
                    fill="none"
                    stroke="currentColor"
                    strokeOpacity="0.25"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                  {spark.played ? (
                    <path
                      d={spark.played}
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.75"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                    />
                  ) : null}
                </svg>
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="route-playback-hud__controls">
          <button
            type="button"
            className="route-playback-hud__btn"
            onClick={onTogglePause}
            title={snap.paused ? t('playbackResume') : t('playbackPause')}
            aria-label={snap.paused ? t('playbackResume') : t('playbackPause')}
          >
            {snap.paused ? (
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path fill="currentColor" d="M5 3l14 9-14 9V3z" />
              </svg>
            ) : (
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <rect
                  x="6"
                  y="4"
                  width="4"
                  height="16"
                  rx="1"
                  fill="currentColor"
                />
                <rect
                  x="14"
                  y="4"
                  width="4"
                  height="16"
                  rx="1"
                  fill="currentColor"
                />
              </svg>
            )}
          </button>
          <button
            type="button"
            className="route-playback-hud__btn route-playback-hud__speed"
            onClick={onCycleSpeed}
            title={t('playbackSpeed')}
            aria-label={`${t('playbackSpeed')} ${snap.speed}x`}
          >
            {snap.speed}x
          </button>
          <div
            ref={barRef}
            className="route-playback-hud__scrub"
            role="slider"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(snap.progress * 100)}
            tabIndex={0}
            onPointerDown={(e) => {
              draggingRef.current = true;
              (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
              onSeek(ratioFromEvent(e.clientX));
            }}
            onPointerMove={(e) => {
              if (!draggingRef.current) return;
              onSeek(ratioFromEvent(e.clientX));
            }}
            onPointerUp={() => {
              draggingRef.current = false;
            }}
            onPointerCancel={() => {
              draggingRef.current = false;
            }}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft') onSeek(snap.progress - 0.02);
              if (e.key === 'ArrowRight') onSeek(snap.progress + 0.02);
            }}
          >
            <div
              className="route-playback-hud__scrub-fill"
              style={{ width: `${snap.progress * 100}%` }}
            />
          </div>
          <div
            className="route-playback-hud__export-wrap"
            ref={settingsWrapRef}
          >
            {settingsOpen ? (
              <div
                className="route-playback-hud__export-menu"
                role="dialog"
                aria-label={t('playbackSettings')}
              >
                <p className="route-playback-hud__export-menu-title">
                  {t('playbackSettings')}
                </p>
                <button
                  type="button"
                  className="route-playback-hud__setting"
                  aria-pressed={prefs.showEndpoints}
                  onClick={() => {
                    const next = !prefs.showEndpoints;
                    setPlaybackPrefs({ showEndpoints: next });
                    onShowEndpointsChange?.(next);
                  }}
                >
                  <span>{t('playbackShowEndpoints')}</span>
                  <span
                    className="route-playback-hud__switch"
                    aria-hidden="true"
                  />
                </button>
                <button
                  type="button"
                  className="route-playback-hud__setting"
                  aria-pressed={prefs.showStats}
                  onClick={() =>
                    setPlaybackPrefs({ showStats: !prefs.showStats })
                  }
                >
                  <span>{t('playbackShowStats')}</span>
                  <span
                    className="route-playback-hud__switch"
                    aria-hidden="true"
                  />
                </button>
              </div>
            ) : null}
            <button
              type="button"
              className={`route-playback-hud__btn route-playback-hud__settings${
                settingsOpen ? 'is-open' : ''
              }`}
              onClick={() => {
                setExportMenuOpen(false);
                setSettingsOpen((open) => !open);
              }}
              title={t('playbackSettings')}
              aria-label={t('playbackSettings')}
              aria-expanded={settingsOpen}
              aria-haspopup="dialog"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  fill="currentColor"
                  d="M19.14 12.94a7.4 7.4 0 000-1.88l2.03-1.58a.5.5 0 00.12-.64l-1.92-3.32a.5.5 0 00-.6-.22l-2.39.96a7.2 7.2 0 00-1.63-.94l-.36-2.54a.5.5 0 00-.49-.42h-3.84a.5.5 0 00-.49.42l-.36 2.54c-.59.22-1.14.54-1.63.94l-2.39-.96a.5.5 0 00-.6.22L2.71 8.84a.5.5 0 00.12.64l2.03 1.58a7.4 7.4 0 000 1.88l-2.03 1.58a.5.5 0 00-.12.64l1.92 3.32c.13.22.39.31.6.22l2.39-.96c.49.4 1.04.72 1.63.94l.36 2.54c.05.24.26.42.49.42h3.84c.23 0 .44-.18.49-.42l.36-2.54c.59-.22 1.14-.54 1.63-.94l2.39.96c.22.09.47 0 .6-.22l1.92-3.32a.5.5 0 00-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1112 8.5a3.5 3.5 0 010 7z"
                />
              </svg>
            </button>
          </div>
          {onExport ? (
            <div
              className="route-playback-hud__export-wrap"
              ref={exportWrapRef}
              data-export-chrome
            >
              {exportMenuOpen && !exporting ? (
                <div
                  className="route-playback-hud__export-menu"
                  role="dialog"
                  aria-label={t('exportVideoChoose')}
                >
                  <p className="route-playback-hud__export-menu-title">
                    {t('exportVideoChoose')}
                  </p>
                  <button
                    type="button"
                    className="route-playback-hud__export-menu-btn"
                    onClick={() => {
                      setExportMenuOpen(false);
                      onExport({
                        includeHud: false,
                        sizeMode: exportSizeMode,
                      });
                    }}
                  >
                    {t('exportVideoMapOnly')}
                  </button>
                  <button
                    type="button"
                    className="route-playback-hud__export-menu-btn"
                    onClick={() => {
                      setExportMenuOpen(false);
                      onExport({
                        includeHud: true,
                        sizeMode: exportSizeMode,
                      });
                    }}
                  >
                    {t('exportVideoWithBar')}
                  </button>
                  <div
                    className="route-playback-hud__export-size"
                    role="group"
                    aria-label={t('exportVideoSize')}
                  >
                    <span className="route-playback-hud__export-menu-title">
                      {t('exportVideoSize')}
                    </span>
                    <div className="route-playback-hud__export-size-toggle">
                      <button
                        type="button"
                        className={`route-playback-hud__export-size-btn${
                          exportSizeMode === 'native' ? ' is-active' : ''
                        }`}
                        aria-pressed={exportSizeMode === 'native'}
                        onClick={() => setExportSizeMode('native')}
                      >
                        {t('exportVideoSizeNative')}
                      </button>
                      <button
                        type="button"
                        className={`route-playback-hud__export-size-btn${
                          exportSizeMode === 'phone' ? ' is-active' : ''
                        }`}
                        aria-pressed={exportSizeMode === 'phone'}
                        onClick={() => setExportSizeMode('phone')}
                      >
                        {t('exportVideoSizePhone')}
                      </button>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="route-playback-hud__export-menu-btn is-muted"
                    onClick={() => setExportMenuOpen(false)}
                  >
                    {t('exportVideoCancel')}
                  </button>
                </div>
              ) : null}
              <button
                type="button"
                className={`route-playback-hud__btn route-playback-hud__export${
                  exporting ? 'is-recording' : ''
                }${exportMenuOpen ? 'is-open' : ''}`}
                onClick={() => {
                  if (exporting) {
                    onExport({
                      includeHud: false,
                      sizeMode: exportSizeMode,
                    });
                    return;
                  }
                  setSettingsOpen(false);
                  setExportMenuOpen((open) => !open);
                }}
                title={exporting ? t('exportVideoStop') : t('exportVideo')}
                aria-label={exporting ? t('exportVideoStop') : t('exportVideo')}
                aria-expanded={exportMenuOpen}
                aria-haspopup="dialog"
              >
                {exporting ? (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <rect
                      x="6"
                      y="6"
                      width="12"
                      height="12"
                      rx="1.5"
                      fill="currentColor"
                    />
                  </svg>
                ) : (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      fill="currentColor"
                      d="M12 3a1 1 0 011 1v8.59l2.3-2.3a1 1 0 111.4 1.42l-4 4a1 1 0 01-1.4 0l-4-4a1 1 0 111.4-1.42L11 12.59V4a1 1 0 011-1zM5 18a1 1 0 011-1h12a1 1 0 110 2H6a1 1 0 01-1-1z"
                    />
                  </svg>
                )}
              </button>
            </div>
          ) : null}
        </div>
        {exportMessage ? (
          <p
            className="route-playback-hud__status"
            role="status"
            data-export-chrome
          >
            {exportMessage}
          </p>
        ) : exporting ? (
          <p
            className="route-playback-hud__status"
            role="status"
            data-export-chrome
          >
            {t(exportEnding ? 'exportVideoEnding' : 'exportVideoRecording')}
          </p>
        ) : null}
      </div>
    </div>
  );
}

/** Canvas-friendly stats for video burn-in (no DOM snapshot). */
export function buildMapVideoOverlayStats(args: {
  progress: number;
  distanceKm: number;
  hr: HrSeries | null;
  time: TimeSeries | null;
  movingTimeSec: number;
  averageSpeedMs: number;
  labels: { time: string; pace: string; hr: string; km: string };
}): {
  distanceKm: number;
  hrBpm: number | null;
  elapsedLabel: string | null;
  paceLabel: string | null;
  progress: number;
  hrCurve: HrSeries | null;
  labels: { time: string; pace: string; hr: string; km: string };
} {
  const elapsed = playbackElapsedSec(
    args.time,
    args.distanceKm,
    args.progress,
    args.movingTimeSec
  );
  const pace = playbackAvgPaceSec(
    elapsed,
    args.distanceKm,
    args.averageSpeedMs
  );
  const hr = interpolateHr(args.hr, args.distanceKm);
  return {
    distanceKm: args.distanceKm,
    hrBpm: hr != null ? Math.round(hr) : null,
    elapsedLabel: elapsed != null ? formatClock(elapsed) : null,
    paceLabel: pace != null ? formatPaceSeconds(pace) : null,
    progress: args.progress,
    hrCurve: args.hr,
    labels: args.labels,
  };
}

function endCardPeriod(hour: number, locale: 'zh' | 'en'): string {
  if (locale === 'en') {
    if (hour < 12) return 'Morning';
    if (hour < 18) return 'Afternoon';
    return 'Evening';
  }
  if (hour < 12) return '上午';
  if (hour < 18) return '下午';
  return '晚上';
}

function endCardSport(type: string, locale: 'zh' | 'en'): string {
  if (type === 'Ride') return locale === 'en' ? 'Ride' : '骑行';
  if (type && type !== 'Run') return type;
  return locale === 'en' ? 'Run' : '跑步';
}

function endCardDistanceLabel(meters: number): string {
  const km = meters / 1000;
  const rounded = Math.round(km * 10) / 10;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
}

function endCardDateLabel(startDateLocal: string): string {
  const match = startDateLocal.match(
    /(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/
  );
  if (!match) return startDateLocal;
  return `${match[1]}/${match[2]}/${match[3]} ${match[4]}:${match[5]}`;
}

/** Closing still: full-route summary, not the live chase numbers. */
export function buildMapVideoEndCard(args: {
  locale: 'zh' | 'en';
  startDateLocal: string;
  sport: string;
  distanceMeters: number;
  movingTimeSec: number;
  averageSpeedMs: number;
  hrBpm: number | null;
  calories: number | null;
}): {
  dateLabel: string;
  headline: string;
  distanceLabel: string;
  distanceUnit: string;
  rows: { label: string; value: string }[];
} {
  const zh = args.locale !== 'en';
  const hour = Number(args.startDateLocal.slice(11, 13));
  const period = endCardPeriod(Number.isFinite(hour) ? hour : 8, args.locale);
  const sport = endCardSport(args.sport, args.locale);
  const pace =
    args.averageSpeedMs > 0
      ? formatPaceSeconds(1000 / args.averageSpeedMs)
      : null;
  const rows: { label: string; value: string }[] = [
    {
      label: zh ? '用时' : 'Time',
      value: formatClock(args.movingTimeSec),
    },
  ];
  if (pace && pace !== '--') {
    rows.push({ label: zh ? '配速' : 'Pace', value: pace });
  }
  if (args.calories != null && args.calories > 0) {
    rows.push({
      label: zh ? '消耗' : 'Calories',
      value: zh
        ? `${Math.round(args.calories)} 千卡`
        : `${Math.round(args.calories)} kcal`,
    });
  }
  if (args.hrBpm != null && args.hrBpm > 0) {
    rows.push({
      label: zh ? '心率' : 'HR',
      value: zh ? `${args.hrBpm} 次/分` : `${args.hrBpm} bpm`,
    });
  }
  return {
    dateLabel: endCardDateLabel(args.startDateLocal),
    headline: `${period} ${sport}`,
    distanceLabel: endCardDistanceLabel(args.distanceMeters),
    distanceUnit: zh ? '公里' : 'km',
    rows,
  };
}
