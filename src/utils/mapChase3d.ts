import mapboxgl from 'mapbox-gl';
import { haversine, type Coordinate } from './routeAnimation';

export function calculateBearing(start: Coordinate, end: Coordinate): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const lat1 = toRad(start[1]);
  const lon1 = toRad(start[0]);
  const lat2 = toRad(end[1]);
  const lon2 = toRad(end[0]);
  const dLon = lon2 - lon1;
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

/** DEM mesh height multiplier. 1 = real-ish elevation; pitch stays ~75. */
const TERRAIN_EXAGGERATION = 1;
/** Light hillshade (Mapbox 0-1). Slope cue without heavy shading. */
const HILLSHADE_EXAGGERATION = 0.2;
const HILLSHADE_LAYER = 'terrain-hillshade';

/**
 * Terrain DEM + light hillshade + extruded buildings. Only for Mapbox streets
 * styles that expose the `composite` source. CARTO / blank styles skip this so a
 * missing DEM token cannot black out the canvas; pitch/orbit still work.
 */
export function injectMapTerrain(
  m: mapboxgl.Map,
  isDark: boolean,
  enabled = true
): void {
  if (!enabled) return;
  try {
    if (!m.getSource('composite')) return;
    if (!m.getSource('mapbox-dem')) {
      m.addSource('mapbox-dem', {
        type: 'raster-dem',
        url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
        tileSize: 512,
        maxzoom: 14,
      });
    }
    // Always re-apply so toggling 3D picks up the current exaggeration.
    m.setTerrain({ source: 'mapbox-dem', exaggeration: TERRAIN_EXAGGERATION });

    if (!m.getLayer(HILLSHADE_LAYER)) {
      const layers = m.getStyle().layers ?? [];
      const beforeId = layers.find((l) => l.type === 'symbol')?.id;
      m.addLayer(
        {
          id: HILLSHADE_LAYER,
          type: 'hillshade',
          source: 'mapbox-dem',
          paint: {
            'hillshade-exaggeration': HILLSHADE_EXAGGERATION,
            'hillshade-shadow-color': isDark ? '#000000' : '#473B24',
            'hillshade-highlight-color': '#FFFFFF',
            'hillshade-accent-color': isDark ? '#111111' : '#473B24',
          },
        },
        beforeId
      );
    } else {
      m.setPaintProperty(
        HILLSHADE_LAYER,
        'hillshade-exaggeration',
        HILLSHADE_EXAGGERATION
      );
      m.setPaintProperty(
        HILLSHADE_LAYER,
        'hillshade-shadow-color',
        isDark ? '#000000' : '#473B24'
      );
      m.setPaintProperty(
        HILLSHADE_LAYER,
        'hillshade-accent-color',
        isDark ? '#111111' : '#473B24'
      );
    }

    if (!m.getLayer('3d-buildings')) {
      m.addLayer({
        id: '3d-buildings',
        source: 'composite',
        'source-layer': 'building',
        filter: ['==', 'extrude', 'true'],
        type: 'fill-extrusion',
        minzoom: 14,
        paint: {
          'fill-extrusion-color': isDark ? '#1C1C1E' : '#eaeaf1',
          'fill-extrusion-height': ['get', 'height'],
          'fill-extrusion-base': ['get', 'min_height'],
          'fill-extrusion-opacity': 0.6,
        },
      });
    } else {
      m.setPaintProperty(
        '3d-buildings',
        'fill-extrusion-color',
        isDark ? '#1C1C1E' : '#eaeaf1'
      );
    }

    // Soft depth cue (upstairs-style); cheap on Mapbox GL JS 3.x mercator.
    m.setFog({
      range: [0.8, 8],
      color: isDark ? '#0b0b10' : '#ffffff',
      'high-color': isDark ? '#1a2030' : '#87b0de',
      'horizon-blend': 0.08,
      'space-color': isDark ? '#0a0a0f' : '#dce6f5',
      'star-intensity': isDark ? 0.2 : 0,
    });
  } catch (e) {
    console.warn('3D terrain unavailable, falling back to 2D', e);
  }
}

export function clearMapTerrain(m: mapboxgl.Map): void {
  if (m.getLayer(HILLSHADE_LAYER)) {
    try {
      m.removeLayer(HILLSHADE_LAYER);
    } catch {
      /* ignore */
    }
  }
  if (m.getLayer('3d-buildings')) {
    try {
      m.removeLayer('3d-buildings');
    } catch {
      /* ignore */
    }
  }
  if (m.getTerrain()) {
    try {
      m.setTerrain(null);
    } catch {
      /* ignore */
    }
  }
  try {
    m.setFog(null);
  } catch {
    /* ignore */
  }
}

/** In-place orbit around a fitted track (koobai / upstairs pattern).
 * Pitch/zoom tuned so terrain + buildings read as 3D without hugging the ground.
 */
export const ORBIT_PITCH = 75;
export const ORBIT_PITCH_WOBBLE = 3;
export const ORBIT_ZOOM_WOBBLE = 0.2;
export const ORBIT_DURATION_MS = 36000;
export const ORBIT_FIT_PADDING = 28;
export const ORBIT_FIT_MAX_ZOOM = 17;

function coordsExtent(
  coords: Coordinate[]
): [[number, number], [number, number]] | null {
  if (coords.length === 0) return null;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of coords) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  return [
    [minX, minY],
    [maxX, maxY],
  ];
}

type OrbitStartArgs = {
  map: mapboxgl.Map;
  coords: Coordinate[];
  isDark: boolean;
};

/**
 * Fits the track, pitches to ~75°, then slowly spins in place.
 * Pointer / wheel / drag / zoom-control cancels the spin and leaves the pitched camera.
 */
export function createMapOrbitController() {
  let animToken = 0;
  let raf: number | null = null;
  let timeout: ReturnType<typeof setTimeout> | null = null;
  let running = false;
  let map: mapboxgl.Map | null = null;

  const stop = (opts?: { keepCameraMotion?: boolean }) => {
    animToken += 1;
    if (raf != null) {
      cancelAnimationFrame(raf);
      raf = null;
    }
    if (timeout != null) {
      clearTimeout(timeout);
      timeout = null;
    }
    // NavigationControl zoomIn/Out starts an easeTo that shares this path via
    // zoomstart+originalEvent; map.stop() would cancel that ease mid-flight.
    if (running && !opts?.keepCameraMotion) map?.stop();
    running = false;
  };

  /** Pointer / wheel / drag: cancel orbit (same as before). */
  const handleUserInput = (event: { originalEvent?: Event }) => {
    if (!running || !event.originalEvent) return;
    stop();
  };

  /**
   * Zoom +/- buttons call map.zoomIn/Out({}, { originalEvent }), which never
   * hits map mousedown/wheel. Listen on zoomstart and soft-stop so the ease
   * continues (wheel already stops via the wheel listener above).
   */
  const handleUserZoom = (event: { originalEvent?: Event }) => {
    if (!running || !event.originalEvent) return;
    stop({ keepCameraMotion: true });
  };

  const detach = () => {
    if (!map) return;
    map.off('mousedown', handleUserInput);
    map.off('touchstart', handleUserInput);
    map.off('wheel', handleUserInput);
    map.off('dragstart', handleUserInput);
    map.off('zoomstart', handleUserZoom);
  };

  const attach = (next: mapboxgl.Map) => {
    if (map === next) return;
    detach();
    map = next;
    next.on('mousedown', handleUserInput);
    next.on('touchstart', handleUserInput);
    next.on('wheel', handleUserInput);
    next.on('dragstart', handleUserInput);
    next.on('zoomstart', handleUserZoom);
  };

  const start = ({ map: m, coords, isDark }: OrbitStartArgs) => {
    stop();
    const extent = coordsExtent(coords);
    if (!extent) return;

    attach(m);
    injectMapTerrain(m, isDark, true);
    animToken += 1;
    const token = animToken;
    running = true;

    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const cam = m.cameraForBounds(extent, {
      padding: ORBIT_FIT_PADDING,
      maxZoom: ORBIT_FIT_MAX_ZOOM,
      pitch: ORBIT_PITCH,
    });
    const center = cam?.center ?? [
      (extent[0][0] + extent[1][0]) / 2,
      (extent[0][1] + extent[1][1]) / 2,
    ];
    const zoom = cam?.zoom ?? m.getZoom();
    let spinStarted = false;

    const beginSpin = () => {
      if (spinStarted || animToken !== token) return;
      spinStarted = true;
      if (timeout != null) {
        clearTimeout(timeout);
        timeout = null;
      }
      if (reduce) {
        running = false;
        return;
      }
      const spinCenter = m.getCenter();
      const baseZoom = m.getZoom();
      const baseBearing = m.getBearing();
      const startTs = performance.now();
      const tick = (ts: number) => {
        if (animToken !== token) return;
        const turn = ((ts - startTs) / ORBIT_DURATION_MS) % 1;
        m.jumpTo({
          center: spinCenter,
          bearing: (baseBearing + turn * 360) % 360,
          pitch:
            ORBIT_PITCH + ORBIT_PITCH_WOBBLE * Math.sin(turn * Math.PI * 2),
          zoom: baseZoom + ORBIT_ZOOM_WOBBLE * Math.sin(turn * Math.PI * 4),
        });
        raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    };

    m.easeTo({
      center,
      zoom,
      pitch: ORBIT_PITCH,
      duration: reduce ? 200 : 1200,
      essential: true,
    });
    m.once('moveend', beginSpin);
    timeout = setTimeout(beginSpin, reduce ? 280 : 1600);
  };

  const dispose = () => {
    stop();
    detach();
    map = null;
  };

  return {
    start,
    stop,
    dispose,
    isAnimating: () => running,
  };
}

export type MapOrbitController = ReturnType<typeof createMapOrbitController>;

/** Prefer `.route-map-fs-root` so HUD siblings stay visible in fullscreen. */
function fullscreenRoot(map: mapboxgl.Map): HTMLElement {
  const container = map.getContainer();
  const wrap = container.closest('.route-map-fs-root');
  return (wrap as HTMLElement) || container;
}

export function isMapFullscreen(map: mapboxgl.Map | null): boolean {
  if (!map || typeof document === 'undefined') return false;
  const doc = document as Document & { webkitFullscreenElement?: Element };
  const fs = document.fullscreenElement ?? doc.webkitFullscreenElement;
  if (!fs) return false;
  const root = fullscreenRoot(map);
  return fs === root || root.contains(fs) || fs.contains(root);
}

const HIGHLIGHT_SOURCE = 'chase-highlight';
const HIGHLIGHT_LAYER = 'chase-highlight';
const LEAD_SOURCE = 'chase-lead';
const LEAD_LAYER = 'chase-lead';
const LEAD_PULSE_LAYER = 'chase-lead-pulse';

export type PlaybackCameraMode = '2d' | '3d';
export type PlaybackSpeed = 1 | 2 | 4;

export type PlaybackProgress = {
  progress: number;
  distanceKm: number;
  coord: Coordinate;
  paused: boolean;
  speed: PlaybackSpeed;
};

const CHASE_LINE_WIDTH = 4;
const LEAD_RADIUS = 5.5;
const LEAD_STROKE = 2.5;
const LEAD_PULSE_BASE = 10;
const LEAD_PULSE_AMP = 8;

export function setChaseHighlightLine(
  m: mapboxgl.Map,
  coords: Coordinate[],
  color: string,
  lineWidth = CHASE_LINE_WIDTH
): void {
  const data = {
    type: 'Feature' as const,
    properties: {},
    geometry: {
      type: 'LineString' as const,
      coordinates: coords.length >= 2 ? coords : [],
    },
  };
  if (m.getSource(HIGHLIGHT_SOURCE)) {
    (m.getSource(HIGHLIGHT_SOURCE) as mapboxgl.GeoJSONSource).setData(data);
    if (m.getLayer(HIGHLIGHT_LAYER)) {
      m.setPaintProperty(HIGHLIGHT_LAYER, 'line-width', lineWidth);
    }
    return;
  }
  m.addSource(HIGHLIGHT_SOURCE, { type: 'geojson', data });
  m.addLayer({
    id: HIGHLIGHT_LAYER,
    type: 'line',
    source: HIGHLIGHT_SOURCE,
    layout: {
      'line-cap': 'round',
      'line-join': 'round',
    },
    paint: {
      'line-color': color,
      'line-width': lineWidth,
      'line-opacity': 1,
    },
  });
}

function setLeadPoint(
  m: mapboxgl.Map,
  coord: Coordinate,
  color: string,
  strokeScale = 1
): void {
  const data = {
    type: 'Feature' as const,
    properties: {},
    geometry: { type: 'Point' as const, coordinates: coord },
  };
  if (m.getSource(LEAD_SOURCE)) {
    (m.getSource(LEAD_SOURCE) as mapboxgl.GeoJSONSource).setData(data);
    if (m.getLayer(LEAD_LAYER)) {
      m.setPaintProperty(
        LEAD_LAYER,
        'circle-radius',
        LEAD_RADIUS * strokeScale
      );
      m.setPaintProperty(
        LEAD_LAYER,
        'circle-stroke-width',
        LEAD_STROKE * strokeScale
      );
    }
    return;
  }
  m.addSource(LEAD_SOURCE, { type: 'geojson', data });
  m.addLayer({
    id: LEAD_PULSE_LAYER,
    type: 'circle',
    source: LEAD_SOURCE,
    paint: {
      'circle-radius': 14 * strokeScale,
      'circle-color': color,
      'circle-opacity': 0.28,
      'circle-blur': 0.4,
    },
  });
  m.addLayer({
    id: LEAD_LAYER,
    type: 'circle',
    source: LEAD_SOURCE,
    paint: {
      'circle-radius': LEAD_RADIUS * strokeScale,
      'circle-color': '#ffffff',
      'circle-stroke-width': LEAD_STROKE * strokeScale,
      'circle-stroke-color': color,
      'circle-opacity': 1,
    },
  });
}

function pulseLeadPoint(m: mapboxgl.Map, t: number, strokeScale = 1): void {
  if (!m.getLayer(LEAD_PULSE_LAYER)) return;
  const wave = 0.5 + 0.5 * Math.sin(t * 0.006);
  m.setPaintProperty(
    LEAD_PULSE_LAYER,
    'circle-radius',
    (LEAD_PULSE_BASE + wave * LEAD_PULSE_AMP) * strokeScale
  );
  m.setPaintProperty(LEAD_PULSE_LAYER, 'circle-opacity', 0.12 + wave * 0.22);
}

function removeLeadPoint(m: mapboxgl.Map): void {
  if (m.getLayer(LEAD_LAYER)) m.removeLayer(LEAD_LAYER);
  if (m.getLayer(LEAD_PULSE_LAYER)) m.removeLayer(LEAD_PULSE_LAYER);
  if (m.getSource(LEAD_SOURCE)) m.removeSource(LEAD_SOURCE);
}

export function removeChaseHighlight(m: mapboxgl.Map): void {
  removeLeadPoint(m);
  if (m.getLayer(HIGHLIGHT_LAYER)) m.removeLayer(HIGHLIGHT_LAYER);
  if (m.getSource(HIGHLIGHT_SOURCE)) m.removeSource(HIGHLIGHT_SOURCE);
}

export const CHASE_LAYER_IDS = new Set([
  HIGHLIGHT_LAYER,
  LEAD_LAYER,
  LEAD_PULSE_LAYER,
  '3d-buildings',
  HILLSHADE_LAYER,
]);

type ChaseCallbacks = {
  onStart?: () => void;
  onEnd?: () => void;
  onProgress?: (p: PlaybackProgress) => void;
  /** Fired when compass lock toggles during playback. */
  onBearingLockChange?: (locked: boolean) => void;
};

type ChaseStartArgs = {
  map: mapboxgl.Map;
  coords: Coordinate[];
  color: string;
  distanceKm: number;
  runId: string;
  isDark: boolean;
  cameraMode?: PlaybackCameraMode;
  /** Dim overview layer while chasing (e.g. all-routes / routes). */
  overviewLayerId?: string;
  overviewDimOpacity?: number;
  /**
   * Camera after the chase finishes. Read at end time so a 3D toggle during
   * playback can return to orbit (`keep`) instead of flattening.
   */
  getEndView?: () => 'flat' | 'keep';
  /** Accessible titles for start / end pins (icons only; no visible text). */
  endpointTitles?: { start: string; end: string };
  /** Show play/stop endpoint pins. Default true. */
  showEndpoints?: boolean;
  /** Compass button copy while playback is running. */
  compassTitles?: { lock: string; follow: string };
  /** Start with bearing frozen (from playback prefs). Default false. */
  lockOrientation?: boolean;
};

type PlaybackSession = {
  map: mapboxgl.Map;
  coords: Coordinate[];
  color: string;
  cumulative: Float32Array;
  totalMeters: number;
  durationMs: number;
  runId: string;
  isDark: boolean;
  getEndView?: () => 'flat' | 'keep';
  endpointTitles: { start: string; end: string };
  showEndpoints: boolean;
  token: number;
};

function shortestAngleDelta(from: number, to: number): number {
  return ((to - from + 540) % 360) - 180;
}

/** Heading over a long stretch so short GPS wiggles don't spin the map. */
function stableHeading(
  s: { sample: (meters: number) => Coordinate },
  along: number,
  fallback: number
): number {
  const origin = s.sample(along);
  for (const aheadM of [80, 140, 220]) {
    const ahead = s.sample(along + aheadM);
    if (haversine(origin, ahead) >= 40) {
      return calculateBearing(origin, ahead);
    }
  }
  return fallback;
}

/**
 * Imperative track playback controller shared by TrackMap / RouteMap.
 * Supports 2D top-down follow and 3D chase-behind; pause / seek / speed.
 * Call stop() on unmount, selection clear, or style teardown.
 */
export function createMapChaseController() {
  let animToken = 0;
  let chaseRaf: number | null = null;
  let chaseTimeout: ReturnType<typeof setTimeout> | null = null;
  let running = false;
  let paused = false;
  let speed: PlaybackSpeed = 1;
  let progress = 0;
  let cameraMode: PlaybackCameraMode = '3d';
  let currentBearing = 0;
  /** Compass click during playback: freeze current bearing (no route-follow yaw). */
  let bearingLocked = false;
  let compassBtn: HTMLButtonElement | null = null;
  /** Mapbox puts the tooltip on the icon span (`title`), label on the button. */
  let compassIdleLabel = '';
  let compassTitlesLive: { lock: string; follow: string } | null = null;
  let onCompassClick: ((event: Event) => void) | null = null;
  let currentZoom = 16.5;
  let currentPitch = ORBIT_PITCH;
  /** Extra zoom-out (positive = farther). Phone 9:16 cover reads closer. */
  let zoomOutExtra = 0;
  /** <1 thins route/dot paints so cover-upscale doesn't look oversized. */
  let strokeScale = 1;

  const zoom2dTarget = () => 13.9 - zoomOutExtra;
  const zoom2dInit = () => 13.8 - zoomOutExtra;
  const zoom2dIntro = () => 13.6 - zoomOutExtra;
  let session: PlaybackSession | null = null;
  let lastTs: number | null = null;
  let finishing = false;
  let callbacks: ChaseCallbacks = {};
  let endpointMarkers: mapboxgl.Marker[] = [];

  const clearEndpoints = () => {
    for (const marker of endpointMarkers) marker.remove();
    endpointMarkers = [];
  };

  const addEndpointMarker = (
    map: mapboxgl.Map,
    coord: Coordinate,
    kind: 'start' | 'end',
    title: string
  ) => {
    const el = document.createElement('div');
    el.className = `route-endpoint route-endpoint--${kind}`;
    el.title = title;
    el.setAttribute('aria-label', title);
    el.appendChild(
      kind === 'start' ? createEndpointPlayIcon(10) : createEndpointStopIcon(10)
    );
    const marker = new mapboxgl.Marker({ element: el, anchor: 'center' })
      .setLngLat(coord)
      .addTo(map);
    marker.getElement().style.pointerEvents = 'none';
    endpointMarkers.push(marker);
  };

  /** Start pin only — finish pin waits until playback completes. */
  const showStartEndpoint = (
    map: mapboxgl.Map,
    coords: Coordinate[],
    titles: { start: string; end: string }
  ) => {
    clearEndpoints();
    addEndpointMarker(map, coords[0], 'start', titles.start);
  };

  const showEndEndpoint = (
    map: mapboxgl.Map,
    coords: Coordinate[],
    titles: { start: string; end: string }
  ) => {
    if (
      endpointMarkers.some((m) =>
        m.getElement().classList.contains('route-endpoint--end')
      )
    ) {
      return;
    }
    addEndpointMarker(map, coords[coords.length - 1], 'end', titles.end);
  };

  const clearTimers = () => {
    if (chaseRaf != null) {
      cancelAnimationFrame(chaseRaf);
      chaseRaf = null;
    }
    if (chaseTimeout != null) {
      clearTimeout(chaseTimeout);
      chaseTimeout = null;
    }
  };

  const sampleAt = (
    s: PlaybackSession,
    p: number
  ): { coord: Coordinate; idx: number; distanceKm: number } => {
    const clamped = Math.min(Math.max(p, 0), 1);
    const targetDist = clamped * s.totalMeters;
    const totalPoints = s.coords.length;
    let l = 0;
    let r = totalPoints - 1;
    let idx = 0;
    while (l <= r) {
      const mid = (l + r) >> 1;
      if (s.cumulative[mid] <= targetDist) {
        idx = mid;
        l = mid + 1;
      } else {
        r = mid - 1;
      }
    }
    if (idx >= totalPoints - 1) {
      return {
        coord: s.coords[totalPoints - 1],
        idx: totalPoints - 2,
        distanceKm: s.totalMeters / 1000,
      };
    }
    const segLen = s.cumulative[idx + 1] - s.cumulative[idx];
    const remainder =
      segLen > 0 ? (targetDist - s.cumulative[idx]) / segLen : 0;
    const coord: Coordinate = [
      s.coords[idx][0] + (s.coords[idx + 1][0] - s.coords[idx][0]) * remainder,
      s.coords[idx][1] + (s.coords[idx + 1][1] - s.coords[idx][1]) * remainder,
    ];
    return { coord, idx, distanceKm: targetDist / 1000 };
  };

  const pointAtDistance = (s: PlaybackSession, meters: number): Coordinate => {
    const target = Math.min(Math.max(meters, 0), s.totalMeters);
    const { coord } = sampleAt(s, target / s.totalMeters);
    return coord;
  };

  const setCompassTooltip = (label: string) => {
    if (!compassBtn) return;
    compassBtn.setAttribute('aria-label', label);
    compassBtn.title = label;
    const icon = compassBtn.firstElementChild;
    if (icon instanceof HTMLElement) icon.title = label;
  };

  const syncCompassLock = (titles?: { lock: string; follow: string }) => {
    if (!compassBtn) return;
    const t = titles ?? compassTitlesLive;
    compassBtn.classList.toggle('is-bearing-locked', bearingLocked);
    if (t) {
      setCompassTooltip(bearingLocked ? t.lock : t.follow);
    }
  };

  const unbindCompass = () => {
    if (compassBtn && onCompassClick) {
      compassBtn.removeEventListener('click', onCompassClick, true);
      compassBtn.classList.remove('is-bearing-locked');
      if (compassIdleLabel) setCompassTooltip(compassIdleLabel);
    }
    compassBtn = null;
    onCompassClick = null;
    compassIdleLabel = '';
    compassTitlesLive = null;
    bearingLocked = false;
  };

  const bindCompass = (
    map: mapboxgl.Map,
    titles: { lock: string; follow: string }
  ) => {
    unbindCompass();
    const btn = map
      .getContainer()
      .querySelector('.mapboxgl-ctrl-compass') as HTMLButtonElement | null;
    if (!btn) return;
    compassBtn = btn;
    compassTitlesLive = titles;
    compassIdleLabel =
      btn.getAttribute('aria-label') ||
      (btn.firstElementChild instanceof HTMLElement
        ? btn.firstElementChild.title
        : '') ||
      btn.title ||
      '';
    onCompassClick = (event) => {
      if (!running) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      bearingLocked = !bearingLocked;
      if (bearingLocked) {
        // Freeze whatever bearing the chase currently has — do not snap to north.
        // Do not disable map dragRotate: idle Ctrl/right-drag orbit must keep working
        // after playback ends, and jumpTo already holds bearing while chase runs.
        map.stop();
        if (session) applyFrame(session, progress, { instant: true });
      }
      syncCompassLock(titles);
      callbacks.onBearingLockChange?.(bearingLocked);
    };
    btn.addEventListener('click', onCompassClick, true);
    syncCompassLock(titles);
  };

  /**
   * 2D and 3D share one bearing. Center stays on the runner — offsetting the
   * camera along a noisy heading is what made the line appear to shake.
   * Compass click freezes the current bearing (no route-follow yaw).
   */
  const applyFrame = (
    s: PlaybackSession,
    p: number,
    _opts?: { instant?: boolean }
  ) => {
    const { coord, idx, distanceKm } = sampleAt(s, p);
    const lineCoords =
      p >= 1 ? s.coords : [...s.coords.slice(0, idx + 1), coord];
    setChaseHighlightLine(
      s.map,
      lineCoords,
      s.color,
      CHASE_LINE_WIDTH * strokeScale
    );
    setLeadPoint(s.map, coord, s.color, strokeScale);
    pulseLeadPoint(s.map, performance.now(), strokeScale);

    const along = p * s.totalMeters;
    const heading = stableHeading(
      { sample: (meters) => pointAtDistance(s, meters) },
      along,
      currentBearing
    );
    if (!bearingLocked) {
      const delta = shortestAngleDelta(currentBearing, heading);
      if (Math.abs(delta) > 4) currentBearing += delta * 0.07;
    }
    // When locked, currentBearing stays frozen at the value from lock time.

    if (cameraMode === '3d') {
      const far = stableHeading(
        {
          sample: (meters) => pointAtDistance(s, meters + 120),
        },
        along,
        heading
      );
      const turn = Math.min(1, Math.abs(shortestAngleDelta(heading, far)) / 70);
      const targetZoom = 16.8 - turn * 0.45;
      const targetPitch = ORBIT_PITCH - turn * 6;
      currentZoom += (targetZoom - currentZoom) * 0.04;
      currentPitch += (targetPitch - currentPitch) * 0.04;
    } else {
      currentPitch += (0 - currentPitch) * 0.12;
      // Wider framing — user can't zoom during chase.
      currentZoom += (zoom2dTarget() - currentZoom) * 0.12;
    }

    s.map.jumpTo({
      center: coord,
      bearing: currentBearing,
      pitch: currentPitch,
      zoom: currentZoom,
    });

    callbacks.onProgress?.({
      progress: p,
      distanceKm,
      coord,
      paused,
      speed,
    });
  };

  const finishPlayback = (s: PlaybackSession) => {
    if (finishing || animToken !== s.token) return;
    finishing = true;
    clearTimers();
    applyFrame(s, 1, { instant: true });
    if (s.showEndpoints) {
      showEndEndpoint(s.map, s.coords, s.endpointTitles);
    }
    chaseTimeout = setTimeout(() => {
      if (animToken !== s.token) return;
      removeLeadPoint(s.map);
      const endView = s.getEndView?.() ?? 'flat';
      // Only flatten pitch/bearing here. Bounds fit belongs to the host after
      // any playback card-height transition + map.resize() (otherwise the
      // camera is computed for the tall playing size and clips the route).
      if (endView === 'flat') {
        s.map.easeTo({ pitch: 0, bearing: 0, duration: 700 });
      }
      // Unbind before clearing session so compass lock UI does not stick around.
      unbindCompass();
      running = false;
      session = null;
      finishing = false;
      callbacks.onEnd?.();
    }, 900);
  };

  const tick = (ts: number) => {
    const s = session;
    if (!s || animToken !== s.token || !running) return;
    if (paused) {
      lastTs = null;
      chaseRaf = requestAnimationFrame(tick);
      pulseLeadPoint(s.map, ts, strokeScale);
      return;
    }
    if (lastTs == null) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;
    progress = Math.min(progress + (dt * speed) / s.durationMs, 1);
    applyFrame(s, progress);
    if (progress >= 1) {
      finishPlayback(s);
      return;
    }
    chaseRaf = requestAnimationFrame(tick);
  };

  const startLoop = () => {
    clearTimers();
    lastTs = null;
    chaseRaf = requestAnimationFrame(tick);
  };

  const applyCameraMode = (
    mode: PlaybackCameraMode,
    map: mapboxgl.Map,
    isDark: boolean
  ) => {
    cameraMode = mode;
    if (mode === '3d') {
      injectMapTerrain(map, isDark, true);
    } else {
      clearMapTerrain(map);
    }
  };

  const stop = (opts?: { silent?: boolean }) => {
    animToken += 1;
    clearTimers();
    const wasRunning = running;
    const map = session?.map;
    running = false;
    paused = false;
    finishing = false;
    session = null;
    lastTs = null;
    progress = 0;
    speed = 1;
    unbindCompass();
    clearEndpoints();
    if (map) removeChaseHighlight(map);
    if (wasRunning && !opts?.silent) callbacks.onEnd?.();
  };

  const isAnimating = () => running;

  const isPaused = () => paused;

  const getProgress = () => progress;

  /** Live frame sample for video export overlays (sync, no DOM). */
  const getSnapshot = (): PlaybackProgress | null => {
    if (!session || !running) return null;
    const { distanceKm, coord } = sampleAt(session, progress);
    return { progress, distanceKm, coord, paused, speed };
  };

  /** Pause the chase and draw the whole route for an export end card. */
  const showFullRoute = () => {
    if (!session || !running) return;
    paused = true;
    lastTs = null;
    setChaseHighlightLine(
      session.map,
      session.coords,
      session.color,
      CHASE_LINE_WIDTH * strokeScale
    );
    removeLeadPoint(session.map);
  };

  const getSpeed = () => speed;

  const getCameraMode = () => cameraMode;

  const pause = () => {
    if (!running || paused || finishing) return;
    paused = true;
    lastTs = null;
    if (session) {
      callbacks.onProgress?.({
        progress,
        distanceKm: sampleAt(session, progress).distanceKm,
        coord: sampleAt(session, progress).coord,
        paused: true,
        speed,
      });
    }
  };

  const resume = () => {
    if (!running || !paused || finishing) return;
    paused = false;
    lastTs = null;
    if (session) {
      callbacks.onProgress?.({
        progress,
        distanceKm: sampleAt(session, progress).distanceKm,
        coord: sampleAt(session, progress).coord,
        paused: false,
        speed,
      });
    }
  };

  const setSpeed = (next: PlaybackSpeed) => {
    speed = next;
    if (session) {
      callbacks.onProgress?.({
        progress,
        distanceKm: sampleAt(session, progress).distanceKm,
        coord: sampleAt(session, progress).coord,
        paused,
        speed,
      });
    }
  };

  const setShowEndpoints = (show: boolean) => {
    const s = session;
    if (!s) return;
    s.showEndpoints = show;
    if (!show) {
      clearEndpoints();
      return;
    }
    showStartEndpoint(s.map, s.coords, s.endpointTitles);
    if (progress >= 1) {
      showEndEndpoint(s.map, s.coords, s.endpointTitles);
    }
  };

  const setBearingLocked = (locked: boolean) => {
    if (!running || bearingLocked === locked) return;
    bearingLocked = locked;
    if (bearingLocked && session) {
      session.map.stop();
      applyFrame(session, progress, { instant: true });
    }
    syncCompassLock();
    callbacks.onBearingLockChange?.(bearingLocked);
  };

  const seek = (p: number) => {
    if (!session || !running) return;
    progress = Math.min(Math.max(p, 0), 1);
    lastTs = null;
    if (progress >= 1) {
      finishPlayback(session);
      return;
    }
    finishing = false;
    applyFrame(session, progress, { instant: true });
  };

  const setCameraMode = (mode: PlaybackCameraMode) => {
    if (!session || !running) {
      cameraMode = mode;
      return;
    }
    if (cameraMode === mode) return;
    applyCameraMode(mode, session.map, session.isDark);
    if (mode === '3d') {
      currentZoom = 16.6;
      currentPitch = ORBIT_PITCH;
    } else {
      currentZoom = zoom2dInit();
      currentPitch = 0;
    }
    applyFrame(session, progress, { instant: true });
  };

  const setZoomOutExtra = (extra: number) => {
    zoomOutExtra = Math.max(0, extra);
    if (!session || !running) return;
    if (cameraMode === '2d') {
      currentZoom = zoom2dInit();
      applyFrame(session, progress, { instant: true });
    }
  };

  /** Compensate Mapbox stroke size when export cover-scales the canvas. */
  const setStrokeScale = (scale: number) => {
    strokeScale = Math.min(1, Math.max(0.2, scale));
    if (!session || !running) return;
    applyFrame(session, progress, { instant: true });
  };

  const start = (args: ChaseStartArgs, cb: ChaseCallbacks = {}) => {
    const {
      map: m,
      coords,
      color,
      distanceKm,
      runId,
      isDark,
      cameraMode: mode = '3d',
      overviewLayerId,
      overviewDimOpacity = 0.15,
      getEndView,
      endpointTitles = { start: '起点', end: '终点' },
      showEndpoints = true,
      lockOrientation = false,
      compassTitles = {
        lock: '朝向已锁定（点击跟随路线）',
        follow: '锁定朝向',
      },
    } = args;

    if (coords.length < 2) return;

    stop({ silent: true });
    callbacks = cb;
    applyCameraMode(mode, m, isDark);
    animToken += 1;
    const token = animToken;
    running = true;
    paused = false;
    finishing = false;
    progress = 0;
    speed = 1;
    callbacks.onStart?.();

    if (overviewLayerId && m.getLayer(overviewLayerId)) {
      m.setPaintProperty(overviewLayerId, 'line-opacity', overviewDimOpacity);
    }

    const cumulative = new Float32Array(coords.length);
    cumulative[0] = 0;
    for (let i = 1; i < coords.length; i++) {
      cumulative[i] = cumulative[i - 1] + haversine(coords[i - 1], coords[i]);
    }
    const totalMeters = cumulative[coords.length - 1] || 1;
    // ~280 m of route per wall-clock second at 1x (was 850, which finished a 10k in ~12s).
    const PLAYBACK_METERS_PER_SEC = 280;
    const durationMs = Math.min(
      Math.max(
        14000,
        ((distanceKm || 5) * 1000 * 1000) / PLAYBACK_METERS_PER_SEC
      ),
      72000
    );

    currentBearing = calculateBearing(
      coords[0],
      coords[Math.min(5, coords.length - 1)]
    );
    currentZoom = mode === '3d' ? 16.6 : zoom2dInit();
    currentPitch = mode === '3d' ? ORBIT_PITCH : 0;

    session = {
      map: m,
      coords,
      color,
      cumulative,
      totalMeters,
      durationMs,
      runId,
      isDark,
      getEndView,
      endpointTitles,
      showEndpoints,
      token,
    };

    setChaseHighlightLine(m, [], color, CHASE_LINE_WIDTH * strokeScale);
    setLeadPoint(m, coords[0], color, strokeScale);
    if (showEndpoints) {
      showStartEndpoint(m, coords, endpointTitles);
    }
    bindCompass(m, compassTitles);
    if (lockOrientation) {
      bearingLocked = true;
      syncCompassLock(compassTitles);
    }
    callbacks.onProgress?.({
      progress: 0,
      distanceKm: 0,
      coord: coords[0],
      paused: false,
      speed: 1,
    });

    let begun = false;
    const beginPlayback = () => {
      if (begun || animToken !== token) return;
      begun = true;
      clearTimers();
      startLoop();
    };

    const introPitch = mode === '3d' ? ORBIT_PITCH : 0;
    const introBearing = currentBearing;
    m.flyTo({
      center: coords[0],
      bearing: introBearing,
      pitch: introPitch,
      zoom: mode === '3d' ? 16.5 : zoom2dIntro(),
      duration: 1600,
      essential: true,
    });

    m.once('moveend', () => {
      if (animToken !== token) return;
      m.once('idle', beginPlayback);
      chaseTimeout = setTimeout(beginPlayback, 900);
    });
  };

  return {
    start,
    stop,
    isAnimating,
    isPaused,
    getProgress,
    getSnapshot,
    showFullRoute,
    getSpeed,
    getCameraMode,
    pause,
    resume,
    setSpeed,
    seek,
    setCameraMode,
    setZoomOutExtra,
    setStrokeScale,
    setShowEndpoints,
    setBearingLocked,
  };
}

export type MapChaseController = ReturnType<typeof createMapChaseController>;

function createStrokeSvg(size: number, paths: string[]): SVGElement {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', String(size));
  svg.setAttribute('height', String(size));
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '2');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('aria-hidden', 'true');
  svg.style.display = 'block';
  for (const d of paths) {
    const path = document.createElementNS(ns, 'path');
    path.setAttribute('d', d);
    svg.appendChild(path);
  }
  return svg;
}

/** Match Mapbox zoom/compass glyph visual weight inside 32×32 ctrl cells. */
const CTRL_ICON_SIZE = 20;

/** Lucide play triangle (inline; no lucide dependency). */
export function createPlaySvgEl(size = CTRL_ICON_SIZE): SVGElement {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = createStrokeSvg(size, []);
  const path = document.createElementNS(ns, 'path');
  path.setAttribute('d', 'M5 3l14 9-14 9V3z');
  path.setAttribute('fill', 'currentColor');
  path.setAttribute('stroke', 'none');
  svg.appendChild(path);
  return svg;
}

/** Compact play glyph for the start pin. */
function createEndpointPlayIcon(size = 10): SVGElement {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', String(size));
  svg.setAttribute('height', String(size));
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(ns, 'path');
  // Nudge right so the triangle optically centers in the circle.
  path.setAttribute('d', 'M8 5l12 7-12 7V5z');
  path.setAttribute('fill', 'currentColor');
  svg.appendChild(path);
  return svg;
}

/** Compact stop glyph for the finish pin. */
function createEndpointStopIcon(size = 10): SVGElement {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', String(size));
  svg.setAttribute('height', String(size));
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  const rect = document.createElementNS(ns, 'rect');
  rect.setAttribute('x', '6');
  rect.setAttribute('y', '6');
  rect.setAttribute('width', '12');
  rect.setAttribute('height', '12');
  rect.setAttribute('rx', '1.5');
  rect.setAttribute('fill', 'currentColor');
  svg.appendChild(rect);
  return svg;
}

/** Stop square (inline) — chase control toggles play / stop. */
export function createStopSvgEl(size = CTRL_ICON_SIZE): SVGElement {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = createStrokeSvg(size, []);
  const rect = document.createElementNS(ns, 'rect');
  rect.setAttribute('x', '6');
  rect.setAttribute('y', '6');
  rect.setAttribute('width', '12');
  rect.setAttribute('height', '12');
  rect.setAttribute('rx', '1.5');
  rect.setAttribute('fill', 'currentColor');
  rect.setAttribute('stroke', 'none');
  svg.appendChild(rect);
  return svg;
}

/** @deprecated use createPlaySvgEl — kept for any lingering imports */
export function createRouteSvgEl(size = 16): SVGElement {
  return createPlaySvgEl(size);
}

/** Mapbox-native square control button chrome (zoom / compass siblings). */
function createCtrlIconButton(className: string): HTMLButtonElement {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = className;
  const icon = document.createElement('span');
  icon.className = 'mapboxgl-ctrl-icon';
  icon.setAttribute('aria-hidden', 'true');
  btn.appendChild(icon);
  return btn;
}

export function createChaseControlButton(): HTMLButtonElement {
  const btn = createCtrlIconButton('route-map-play-btn');
  const icon = btn.querySelector('.mapboxgl-ctrl-icon');
  if (icon) icon.appendChild(createPlaySvgEl(CTRL_ICON_SIZE));
  return btn;
}

export function updateChaseControlButton(
  btn: HTMLButtonElement,
  state: { visible: boolean; chasing: boolean; title: string }
): void {
  btn.classList.toggle('is-hidden', !state.visible);
  btn.classList.toggle('is-chasing', state.chasing);
  btn.title = state.title;
  btn.setAttribute('aria-label', state.title);
  const icon = btn.querySelector('.mapboxgl-ctrl-icon');
  if (icon) {
    icon.replaceChildren(
      state.chasing
        ? createStopSvgEl(CTRL_ICON_SIZE)
        : createPlaySvgEl(CTRL_ICON_SIZE)
    );
  }
}

export function create3dToggleButton(): HTMLButtonElement {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'route-map-3d-btn';
  btn.textContent = '3D';
  return btn;
}

export function update3dToggleButton(
  btn: HTMLButtonElement,
  state: { visible: boolean; active: boolean; title: string }
): void {
  btn.classList.toggle('is-hidden', !state.visible);
  btn.classList.toggle('is-active', state.active);
  btn.setAttribute('aria-pressed', state.active ? 'true' : 'false');
  btn.title = state.title;
  btn.setAttribute('aria-label', state.title);
}

/** Lucide maximize-2 — enter fullscreen. */
function createEnterFullscreenSvgEl(size = CTRL_ICON_SIZE): SVGElement {
  return createStrokeSvg(size, [
    'M15 3h6v6',
    'm21 3-7 7',
    'm3 21 7-7',
    'M9 21H3v-6',
  ]);
}

/** Lucide minimize-2 — exit fullscreen. */
function createExitFullscreenSvgEl(size = CTRL_ICON_SIZE): SVGElement {
  return createStrokeSvg(size, [
    'M4 14h6v6',
    'm3 21 7-7',
    'M20 10h-6V4',
    'm21 3-7 7',
  ]);
}

export function createFullscreenButton(): HTMLButtonElement {
  const btn = createCtrlIconButton('route-map-fullscreen-btn');
  const icon = btn.querySelector('.mapboxgl-ctrl-icon');
  if (icon) icon.appendChild(createEnterFullscreenSvgEl());
  return btn;
}

export function updateFullscreenButton(
  btn: HTMLButtonElement,
  state: { visible: boolean; active: boolean; title: string }
): void {
  btn.classList.toggle('is-hidden', !state.visible);
  btn.classList.toggle('is-active', state.active);
  btn.title = state.title;
  btn.setAttribute('aria-label', state.title);
  btn.setAttribute('aria-pressed', state.active ? 'true' : 'false');
  const icon = btn.querySelector('.mapboxgl-ctrl-icon');
  if (icon) {
    icon.replaceChildren(
      state.active ? createExitFullscreenSvgEl() : createEnterFullscreenSvgEl()
    );
  }
}

export function toggleMapFullscreen(map: mapboxgl.Map): void {
  const root = fullscreenRoot(map);
  const doc = document as Document & {
    webkitFullscreenElement?: Element;
    webkitExitFullscreen?: () => void;
  };
  if (isMapFullscreen(map)) {
    if (document.exitFullscreen) void document.exitFullscreen();
    else doc.webkitExitFullscreen?.();
    return;
  }
  const el = root as HTMLElement & { webkitRequestFullscreen?: () => void };
  if (root.requestFullscreen) void root.requestFullscreen();
  else el.webkitRequestFullscreen?.();
}

export type MapModeControlHandles = {
  fullscreenButton: HTMLButtonElement | null;
  chaseButton: HTMLButtonElement | null;
};

/**
 * Add play / fullscreen as separate Mapbox control groups under zoom.
 * 3D lives in the React top-left toolbar beside Overview / locate.
 * Call after `addControl(new NavigationControl())`.
 */
export function attachMapModeButtons(
  map: mapboxgl.Map,
  opts: {
    onToggleChase: () => void;
  },
  handles: MapModeControlHandles
): () => void {
  const makeSoloControl = (button: HTMLButtonElement): mapboxgl.IControl => {
    const root = document.createElement('div');
    root.className = 'mapboxgl-ctrl mapboxgl-ctrl-group route-map-mode-ctrl';
    root.appendChild(button);
    return {
      onAdd: () => root,
      onRemove: () => {
        root.remove();
      },
    };
  };

  const chase = createChaseControlButton();
  chase.addEventListener('click', (event) => {
    event.preventDefault();
    opts.onToggleChase();
  });

  const fs = createFullscreenButton();
  fs.addEventListener('click', (event) => {
    event.preventDefault();
    toggleMapFullscreen(map);
  });

  // Hidden until React syncs visibility (GPS gate).
  chase.classList.add('is-hidden');
  fs.classList.add('is-hidden');

  const controls = [makeSoloControl(chase), makeSoloControl(fs)];
  for (const control of controls) {
    map.addControl(control, 'top-right');
  }

  handles.chaseButton = chase;
  handles.fullscreenButton = fs;

  return () => {
    for (const control of controls) {
      try {
        map.removeControl(control);
      } catch {
        /* map already removed */
      }
    }
    handles.fullscreenButton = null;
    handles.chaseButton = null;
  };
}
