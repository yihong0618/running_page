import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
} from 'react';
import { useMapChromeIdle } from '@/hooks/useMapChromeIdle';
import { toPng } from 'html-to-image';
import * as polyline from '@mapbox/polyline';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Activity } from '@/types';
import {
  getAvailableYears,
  formatDistance,
  parseMovingTime,
  formatPace,
} from '@/hooks/useActivities';
import { useLocale } from '@/hooks/useLocale';
import { MAPBOX_TOKEN } from '@/config';
import {
  blankMapStyle,
  basemapStyleUrl,
  initialBasemapProvider,
  isMapboxAuthError,
  mapboxControlLocale,
  mapLabelLanguage,
  MAP_STYLE_LOAD_TIMEOUT_MS,
  type BasemapProvider,
} from '@/core/mapStyle';
import type { Coordinate } from '@/utils/routeAnimation';
import {
  CHASE_LAYER_IDS,
  attachMapModeButtons,
  clearMapTerrain,
  createMapChaseController,
  createMapOrbitController,
  isMapFullscreen,
  removeChaseHighlight,
  setChaseHighlightLine,
  updateChaseControlButton,
  updateFullscreenButton,
  type MapModeControlHandles,
  type PlaybackProgress,
} from '@/utils/mapChase3d';
import {
  fitMapToEndCard,
  fitMapToSelectedRoute,
  fitTrackMapOverview,
  overviewOrbitCoords,
  waitForMapIdle,
} from '@/utils/mapRouteFit';
import {
  buildMapVideoEndCard,
  buildMapVideoOverlayStats,
  nextPlaybackSpeed,
  PlaybackHudView,
  usePlaybackSeries,
} from './PlaybackHud';
import { loadSplits } from '@/core/splits';
import { getPlaybackPrefs } from '@/utils/playbackPrefs';
import {
  defaultMapVideoFilename,
  downloadBlob,
  MapVideoAbortedError,
  MapVideoUnsupportedError,
  phoneChaseZoomOutExtra,
  startMapVideoCapture,
  type MapVideoCapture,
} from '@/utils/exportMapVideo';
import './RouteMap.css';

type SportType = 'Run';

interface TracksPageProps {
  activities: Activity[];
  /** Reserved for parent sport filter; Tracks manages its own sport tabs. */
  filter?: string;
  onBack: () => void;
  onSelectActivity?: (a: Activity | null) => void;
  getTitle?: (a: Activity) => string;
  lightsOff?: boolean;
  dark?: boolean;
}

function renderTrackSVG(summaryPolyline: string, size = 80): string {
  try {
    const coords = polyline.decode(summaryPolyline);
    if (coords.length < 2) return '';
    const lats = coords.map((c) => c[0]);
    const lngs = coords.map((c) => c[1]);
    const minLat = Math.min(...lats),
      maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs),
      maxLng = Math.max(...lngs);
    const latRange = maxLat - minLat || 0.001;
    const lngRange = maxLng - minLng || 0.001;
    const scale = Math.min((size - 8) / lngRange, (size - 8) / latRange);
    const offsetX = (size - lngRange * scale) / 2;
    const offsetY = (size - latRange * scale) / 2;
    return coords
      .map(([lat, lng]) => {
        const x = (lng - minLng) * scale + offsetX;
        const y = size - ((lat - minLat) * scale + offsetY);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  } catch {
    return '';
  }
}

function TrackThumb({
  activity,
  color,
  selected,
  onClick,
  title,
}: {
  activity: Activity;
  color: string;
  selected: boolean;
  onClick: () => void;
  title?: string;
}) {
  const size = 80;
  const points = activity.summary_polyline
    ? renderTrackSVG(activity.summary_polyline, size)
    : '';
  if (!points) return null;
  const label =
    title ?? `${activity.name} — ${(activity.distance / 1000).toFixed(1)} km`;
  return (
    <div
      className={`group relative h-[72px] w-[72px] cursor-pointer rounded transition-all md:h-[80px] md:w-[80px] ${selected ? 'ring-2 ring-[var(--color-accent)] ring-offset-1 ring-offset-[var(--color-bg)]' : ''}`}
      onClick={onClick}
      title={label}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        className={`transition-opacity ${selected ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}
      >
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth={selected ? '2' : '1.5'}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function TrackMap({
  activity,
  activities,
  dark,
  lightsOff = false,
  onPlaybackChange,
}: {
  activity: Activity | null;
  activities: Activity[];
  dark?: boolean;
  lightsOff?: boolean;
  onPlaybackChange?: (playing: boolean) => void;
}) {
  const { locale, t } = useLocale();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const mapReady = useRef(false);
  const activityRef = useRef(activity);
  const activitiesRef = useRef(activities);
  const lightsOffRef = useRef(lightsOff);
  const chaseRef = useRef(createMapChaseController());
  const orbitRef = useRef(createMapOrbitController());
  const selectedCoordsRef = useRef<Coordinate[] | null>(null);
  const styleIdleRef = useRef(false);
  const refitViewRef = useRef<() => void>(() => {});
  const [needsRecenter, setNeedsRecenter] = useState(false);
  const animKeyRef = useRef<string | null>(null);
  /** Non-null while a chase for this run_id should show as active in the UI. */
  const [chaseRunId, setChaseRunId] = useState<string | null>(null);
  const [playbackSnap, setPlaybackSnap] = useState<PlaybackProgress | null>(
    null
  );
  const [view3d, setView3d] = useState(false);
  const view3dRef = useRef(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hudHeight, setHudHeight] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportEnding, setExportEnding] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const fsRootRef = useRef<HTMLDivElement>(null);
  const [chromeRoot, setChromeRoot] = useState<HTMLDivElement | null>(null);
  const bindFsRoot = useCallback((el: HTMLDivElement | null) => {
    fsRootRef.current = el;
    setChromeRoot(el);
  }, []);
  useMapChromeIdle(chromeRoot);
  const videoCaptureRef = useRef<MapVideoCapture | null>(null);
  const chasing =
    chaseRunId != null &&
    activity != null &&
    String(activity.run_id) === chaseRunId;
  const playbackSeries = usePlaybackSeries(chasing, activity?.run_id ?? null);
  const playbackSeriesRef = useRef(playbackSeries);
  const exportMetaRef = useRef({
    movingTimeSec: 0,
    averageSpeedMs: 0,
    startDateLocal: '',
    sport: 'Run',
    distanceMeters: 0,
    hrBpm: null as number | null,
  });
  const caloriesRef = useRef<{ runId: number | null; kcal: number | null }>({
    runId: null,
    kcal: null,
  });
  useEffect(() => {
    playbackSeriesRef.current = playbackSeries;
    exportMetaRef.current = {
      movingTimeSec: activity ? parseMovingTime(activity.moving_time) : 0,
      averageSpeedMs: activity?.average_speed ?? 0,
      startDateLocal: activity?.start_date_local ?? '',
      sport: activity?.type ?? 'Run',
      distanceMeters: activity?.distance ?? 0,
      hrBpm:
        activity?.average_heartrate != null && activity.average_heartrate > 0
          ? Math.round(activity.average_heartrate)
          : null,
    };
  }, [playbackSeries, activity]);

  useEffect(() => {
    onPlaybackChange?.(chasing);
  }, [chasing, onPlaybackChange]);
  const modeHandlesRef = useRef<MapModeControlHandles>({
    fullscreenButton: null,
    chaseButton: null,
  });
  const toggleChaseRef = useRef<() => void>(() => {});
  const [provider, setProvider] = useState<BasemapProvider>(
    initialBasemapProvider
  );
  const useBlank = lightsOff;
  // Orbit / DEM / buildings are best-effort in injectMapTerrain (no-op on CARTO).
  const can3d = !lightsOff;
  const hasOwnGps = Boolean(
    activity?.summary_polyline && activity.summary_polyline.length > 20
  );
  /** 3D stays available in overview; only privacy blanks it. */
  const canOffer3d = can3d;
  /** Chase playback works on the blank privacy basemap; 3D does not. */
  const canOfferPlayback = hasOwnGps;
  const bg = dark !== false ? '#0b0d10' : '#f4f5f7';
  const style = useBlank
    ? blankMapStyle(bg)
    : basemapStyleUrl(provider, dark !== false);
  const ROUTE_LAYER_IDS = new Set([
    'selected',
    'all-routes',
    'animated-run',
    'highlight-run',
    ...CHASE_LAYER_IDS,
  ]);

  const stopAnimations = () => {
    chaseRef.current.stop({ silent: true });
    orbitRef.current.stop();
  };

  const flattenView = (m: mapboxgl.Map) => {
    orbitRef.current.stop();
    if (!chaseRef.current.isAnimating()) {
      clearMapTerrain(m);
      m.easeTo({ pitch: 0, bearing: 0, duration: 600 });
    }
  };

  const startOrbitIfNeeded = (m: mapboxgl.Map, coords: Coordinate[]) => {
    if (!view3dRef.current || !can3d || coords.length < 2) {
      flattenView(m);
      return;
    }
    if (chaseRef.current.isAnimating()) return;
    orbitRef.current.start({
      map: m,
      coords,
      isDark: dark !== false,
    });
  };

  const removeRouteLayers = (m: mapboxgl.Map) => {
    for (const id of [
      'selected',
      'all-routes',
      'animated-run',
      'highlight-run',
    ]) {
      if (m.getLayer(id)) m.removeLayer(id);
      if (m.getSource(id)) m.removeSource(id);
    }
    removeChaseHighlight(m);
  };

  const applyLightsOff = (m: mapboxgl.Map, off: boolean) => {
    const styleJson = m.getStyle();
    if (!styleJson?.layers) return;
    for (const layer of styleJson.layers) {
      if (ROUTE_LAYER_IDS.has(layer.id) || layer.id === 'background') {
        m.setLayoutProperty(layer.id, 'visibility', 'visible');
        continue;
      }
      m.setLayoutProperty(layer.id, 'visibility', off ? 'none' : 'visible');
    }
  };

  useEffect(() => {
    activityRef.current = activity;
    activitiesRef.current = activities;
    lightsOffRef.current = lightsOff;
  });

  const updateRoutesRef = useRef<() => void>(() => {});
  useLayoutEffect(() => {
    updateRoutesRef.current = () => {
      const m = map.current;
      if (!m || !mapReady.current) return;
      const act = activityRef.current;
      const acts = activitiesRef.current;
      const privacy = lightsOffRef.current;

      if (act?.summary_polyline && act.summary_polyline.length > 20) {
        const runId = String(act.run_id);
        const animKey = `${runId}|${privacy ? 1 : 0}|${useBlank ? 1 : 0}`;
        // Keep camera/layers if same selection and chase/orbit already running
        if (
          animKeyRef.current === animKey &&
          (chaseRef.current.isAnimating() || orbitRef.current.isAnimating())
        ) {
          return;
        }

        stopAnimations();
        removeRouteLayers(m);

        const coords = polyline
          .decode(act.summary_polyline)
          .map(([lat, lng]) => [lng, lat] as Coordinate);
        const color = getColor(act);
        animKeyRef.current = animKey;
        selectedCoordsRef.current = coords;

        const features = acts
          .filter((a) => a.summary_polyline)
          .map((a) => ({
            type: 'Feature' as const,
            properties: { type: a.type, color: getColor(a) },
            geometry: {
              type: 'LineString' as const,
              coordinates: polyline
                .decode(a.summary_polyline!)
                .map(([lat, lng]) => [lng, lat]),
            },
          }));
        if (features.length) {
          m.addSource('all-routes', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features },
          });
          m.addLayer({
            id: 'all-routes',
            type: 'line',
            source: 'all-routes',
            paint: {
              'line-color': ['get', 'color'],
              'line-width': privacy ? 2 : 1.2,
              'line-opacity': privacy ? 0.35 : 0.2,
            },
          });
        }

        setChaseHighlightLine(m, coords, color);
        if (view3dRef.current && !privacy) {
          startOrbitIfNeeded(m, coords);
        } else {
          flattenView(m);
          fitMapToSelectedRoute(m, coords, privacy);
        }
        applyLightsOff(m, privacy);
        return;
      }

      animKeyRef.current = null;
      selectedCoordsRef.current = null;
      stopAnimations();
      removeRouteLayers(m);

      const features = acts
        .filter((a) => a.summary_polyline)
        .map((a) => ({
          type: 'Feature' as const,
          properties: { type: a.type, color: getColor(a) },
          geometry: {
            type: 'LineString' as const,
            coordinates: polyline
              .decode(a.summary_polyline!)
              .map(([lat, lng]) => [lng, lat]),
          },
        }));
      if (!features.length) {
        flattenView(m);
        applyLightsOff(m, privacy);
        return;
      }
      m.addSource('all-routes', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features },
      });
      m.addLayer({
        id: 'all-routes',
        type: 'line',
        source: 'all-routes',
        paint: {
          'line-color': ['get', 'color'],
          'line-width': privacy ? 2 : 1.2,
          'line-opacity': privacy ? 0.85 : 0.5,
        },
      });
      const orbitCoords = overviewOrbitCoords(acts);
      if (view3dRef.current && !privacy && orbitCoords.length > 0) {
        startOrbitIfNeeded(m, orbitCoords);
      } else {
        flattenView(m);
        fitTrackMapOverview(m, acts, privacy);
      }
      applyLightsOff(m, privacy);
    };
  });

  useEffect(() => {
    refitViewRef.current = () => {
      const m = map.current;
      if (!m?.isStyleLoaded() || !mapReady.current) return;
      const act = activityRef.current;
      const coords = selectedCoordsRef.current;
      const privacy = lightsOffRef.current;
      if (act && coords && coords.length > 0) {
        setChaseHighlightLine(m, coords, getColor(act));
        if (view3dRef.current && !privacy) {
          startOrbitIfNeeded(m, coords);
        } else {
          fitMapToSelectedRoute(m, coords, privacy);
        }
      } else if (view3dRef.current && !privacy) {
        const orbitCoords = overviewOrbitCoords(activitiesRef.current);
        if (orbitCoords.length > 0) startOrbitIfNeeded(m, orbitCoords);
        else {
          flattenView(m);
          fitTrackMapOverview(m, activitiesRef.current, privacy);
        }
      } else {
        flattenView(m);
        fitTrackMapOverview(m, activitiesRef.current, privacy);
      }
      setNeedsRecenter(false);
    };
  });

  const restoreOverviewLine = (m: mapboxgl.Map) => {
    if (m.getLayer('all-routes')) {
      m.setPaintProperty(
        'all-routes',
        'line-opacity',
        lightsOffRef.current ? 0.35 : 0.2
      );
    }
  };

  const restoreSelectedHighlight = (m: mapboxgl.Map) => {
    const act = activityRef.current;
    const coords = selectedCoordsRef.current;
    if (act && coords && coords.length >= 2) {
      setChaseHighlightLine(m, coords, getColor(act));
    }
  };

  const resolveOrbitCoords = (): Coordinate[] | null => {
    const selected = selectedCoordsRef.current;
    if (selected && selected.length >= 2) return selected;
    const overview = overviewOrbitCoords(activitiesRef.current);
    return overview.length > 0 ? overview : null;
  };

  const handleToggle3d = () => {
    const m = map.current;
    const coords = resolveOrbitCoords();
    if (!m || !coords || !canOffer3d) return;
    const next = !view3dRef.current;
    view3dRef.current = next;
    setView3d(next);
    if (chaseRef.current.isAnimating()) {
      chaseRef.current.setCameraMode(next ? '3d' : '2d');
      return;
    }
    if (next) {
      startOrbitIfNeeded(m, coords);
      return;
    }
    flattenView(m);
    if (selectedCoordsRef.current && selectedCoordsRef.current.length >= 2) {
      fitMapToSelectedRoute(m, selectedCoordsRef.current, lightsOffRef.current);
    } else {
      fitTrackMapOverview(m, activitiesRef.current, lightsOffRef.current);
    }
  };

  const handleToggleChase = () => {
    const m = map.current;
    const act = activityRef.current;
    const coords = selectedCoordsRef.current;
    if (!m || !act || !coords || !canOfferPlayback) return;

    if (chaseRef.current.isAnimating()) {
      videoCaptureRef.current?.abort();
      videoCaptureRef.current = null;
      setExporting(false);
      setExportEnding(false);
      chaseRef.current.setZoomOutExtra(0);
      chaseRef.current.setStrokeScale(1);
      chaseRef.current.stop({ silent: true });
      setChaseRunId(null);
      setPlaybackSnap(null);
      restoreOverviewLine(m);
      restoreSelectedHighlight(m);
      if (view3dRef.current) {
        startOrbitIfNeeded(m, coords);
      } else {
        flattenView(m);
        fitMapToSelectedRoute(m, coords, lightsOffRef.current);
      }
      return;
    }

    orbitRef.current.stop();
    const runId = String(act.run_id);
    chaseRef.current.start(
      {
        map: m,
        coords,
        color: getColor(act),
        distanceKm: act.distance / 1000,
        runId,
        isDark: dark !== false,
        cameraMode: can3d && view3dRef.current ? '3d' : '2d',
        showEndpoints: getPlaybackPrefs().showEndpoints,
        endpointTitles:
          locale === 'en'
            ? { start: 'Start', end: 'Finish' }
            : { start: '起点', end: '终点' },
        compassTitles: {
          lock: t('bearingLock'),
          follow: t('bearingFollow'),
        },
        overviewLayerId: 'all-routes',
        getEndView: () => (view3dRef.current ? 'keep' : 'flat'),
      },
      {
        onStart: () => setChaseRunId(runId),
        onProgress: (p) => setPlaybackSnap(p),
        onEnd: () => {
          if (videoCaptureRef.current) {
            videoCaptureRef.current.stop();
            return;
          }
          setChaseRunId(null);
          setPlaybackSnap(null);
          restoreOverviewLine(m);
          restoreSelectedHighlight(m);
          if (!view3dRef.current) clearMapTerrain(m);
          // Orbit / fitBounds wait until card height + resize settle (chasing effect).
        },
      }
    );
  };

  const handleExportVideo = async (opts: {
    includeHud: boolean;
    sizeMode: 'native' | 'phone';
  }) => {
    if (exporting && videoCaptureRef.current) {
      videoCaptureRef.current.stop();
      return;
    }
    const m = map.current;
    if (!m || !chasing) return;
    try {
      const canvas = m.getCanvas();
      chaseRef.current.setZoomOutExtra(
        opts.sizeMode === 'phone'
          ? phoneChaseZoomOutExtra(canvas.clientWidth, canvas.clientHeight)
          : 0
      );
      chaseRef.current.seek(0);
      if (chaseRef.current.isPaused()) chaseRef.current.resume();
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      });
      const runId = activity?.run_id;
      if (runId != null && caloriesRef.current.runId !== runId) {
        caloriesRef.current = { runId, kcal: null };
        void loadSplits(runId).then((data) => {
          if (caloriesRef.current.runId !== runId) return;
          const kcal = data?.summary?.calories;
          caloriesRef.current.kcal = kcal != null && kcal > 0 ? kcal : null;
        });
      }
      const capture = startMapVideoCapture({
        mapCanvas: m.getCanvas(),
        includeHud: opts.includeHud,
        sizeMode: opts.sizeMode,
        getOverlayStats: () => {
          const snap = chaseRef.current.getSnapshot();
          if (!snap) return null;
          const series = playbackSeriesRef.current;
          const meta = exportMetaRef.current;
          return buildMapVideoOverlayStats({
            progress: snap.progress,
            distanceKm: snap.distanceKm,
            hr: series?.hr ?? null,
            time: series?.time ?? null,
            movingTimeSec: meta.movingTimeSec,
            averageSpeedMs: meta.averageSpeedMs,
            labels: {
              time: t('timeLabel'),
              pace: t('avgPace'),
              hr: t('hr'),
              km: 'km',
            },
          });
        },
        prepareEndCard: async () => {
          const live = map.current;
          const coords = selectedCoordsRef.current;
          if (!live || !coords || coords.length < 2) return;
          chaseRef.current.showFullRoute();
          fitMapToEndCard(live, coords, { sizeMode: opts.sizeMode });
          await waitForMapIdle(live);
        },
        getEndCard: () => {
          const meta = exportMetaRef.current;
          if (!meta.startDateLocal || meta.distanceMeters <= 0) return null;
          return buildMapVideoEndCard({
            locale: locale === 'en' ? 'en' : 'zh',
            startDateLocal: meta.startDateLocal,
            sport: meta.sport,
            distanceMeters: meta.distanceMeters,
            movingTimeSec: meta.movingTimeSec,
            averageSpeedMs: meta.averageSpeedMs,
            hrBpm: meta.hrBpm,
            calories: caloriesRef.current.kcal,
          });
        },
        getMarkerPoints: () => {
          const live = map.current;
          const coords = selectedCoordsRef.current;
          const canvas = live?.getCanvas();
          if (!live || !coords || coords.length < 2 || !canvas) return null;
          const start = live.project(coords[0]);
          const end = live.project(coords[coords.length - 1]);
          return {
            start: { x: start.x, y: start.y },
            end: { x: end.x, y: end.y },
            cssWidth: canvas.clientWidth || 1,
            cssHeight: canvas.clientHeight || 1,
          };
        },
        onPhaseChange: (phase) => {
          setExportEnding(phase === 'ending');
        },
        onCoverScale: (scale) => {
          chaseRef.current.setStrokeScale(scale > 1 ? 1.45 / scale : 1);
        },
      });
      videoCaptureRef.current = capture;
      setExporting(true);
      setExportEnding(false);
      setExportMessage(null);
      const blob = await capture.done;
      const filename = defaultMapVideoFilename();
      downloadBlob(blob, filename);
    } catch (err) {
      if (err instanceof MapVideoAbortedError) {
        /* cancelled */
      } else if (err instanceof MapVideoUnsupportedError) {
        setExportMessage(t('exportVideoUnsupported'));
      } else {
        console.error('Video export failed:', err);
        setExportMessage(t('exportVideoFailed'));
      }
    } finally {
      const hadCapture = videoCaptureRef.current != null;
      videoCaptureRef.current = null;
      setExporting(false);
      setExportEnding(false);
      chaseRef.current.setZoomOutExtra(0);
      chaseRef.current.setStrokeScale(1);
      window.setTimeout(() => setExportMessage(null), 4000);
      if (hadCapture) {
        const live = map.current;
        chaseRef.current.stop({ silent: true });
        setChaseRunId(null);
        setPlaybackSnap(null);
        if (live) {
          restoreOverviewLine(live);
          restoreSelectedHighlight(live);
          if (!view3dRef.current) clearMapTerrain(live);
        }
      }
    }
  };

  useEffect(() => {
    return () => {
      videoCaptureRef.current?.abort();
      videoCaptureRef.current = null;
    };
  }, []);

  // Parent card height grows/shrinks with playback — resize, then re-fit when ending.
  const wasChasingRef = useRef(false);
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const ending = wasChasingRef.current && !chasing;
    wasChasingRef.current = chasing;
    const tick = () => m.resize();
    tick();
    const t1 = window.setTimeout(tick, 80);
    const t2 = window.setTimeout(() => {
      tick();
      if (!ending) return;
      const coords = selectedCoordsRef.current;
      if (!coords || coords.length < 2) return;
      if (view3dRef.current) {
        startOrbitIfNeeded(m, coords);
      } else {
        fitMapToSelectedRoute(m, coords, lightsOffRef.current);
      }
    }, 360);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [chasing]);

  useEffect(() => {
    toggleChaseRef.current = handleToggleChase;
  });

  useEffect(() => {
    const { fullscreenButton, chaseButton } = modeHandlesRef.current;
    if (fullscreenButton) {
      updateFullscreenButton(fullscreenButton, {
        visible: canOfferPlayback,
        active: isFullscreen,
        title: isFullscreen ? t('exitFullscreen') : t('enterFullscreen'),
      });
    }
    if (chaseButton) {
      updateChaseControlButton(chaseButton, {
        visible: canOfferPlayback,
        chasing,
        title: chasing ? t('stopChase') : t('startChase'),
      });
    }
  }, [chasing, isFullscreen, canOfferPlayback, t]);

  useEffect(() => {
    if (!mapContainer.current) return;
    if (MAPBOX_TOKEN) mapboxgl.accessToken = MAPBOX_TOKEN;

    mapReady.current = false;
    styleIdleRef.current = false;
    animKeyRef.current = null;
    videoCaptureRef.current?.abort();
    videoCaptureRef.current = null;
    setExporting(false);
    chaseRef.current.stop({ silent: true });
    const mapInstance = new mapboxgl.Map({
      container: mapContainer.current,
      style,
      center: [108, 35],
      zoom: 3,
      pitch: 0,
      maxPitch: 85,
      attributionControl: false,
      /** Needed so WebGL frames remain readable for MediaRecorder export. */
      preserveDrawingBuffer: true,
      language: mapLabelLanguage(locale),
      locale: mapboxControlLocale(t),
    });
    map.current = mapInstance;

    if (!useBlank) {
      mapInstance.addControl(
        new mapboxgl.AttributionControl({ compact: true }),
        'bottom-right'
      );
    }

    mapInstance.addControl(new mapboxgl.NavigationControl(), 'top-right');

    const detachModeButtons = attachMapModeButtons(
      mapInstance,
      {
        onToggleChase: () => toggleChaseRef.current(),
      },
      modeHandlesRef.current
    );
    {
      const { fullscreenButton, chaseButton } = modeHandlesRef.current;
      if (fullscreenButton) {
        updateFullscreenButton(fullscreenButton, {
          visible: canOfferPlayback,
          active: false,
          title: t('enterFullscreen'),
        });
      }
      if (chaseButton) {
        updateChaseControlButton(chaseButton, {
          visible: canOfferPlayback,
          chasing: false,
          title: t('startChase'),
        });
      }
    }

    const syncFullscreen = () => {
      const next = isMapFullscreen(mapInstance);
      setIsFullscreen(next);
      requestAnimationFrame(() => mapInstance.resize());
    };
    document.addEventListener('fullscreenchange', syncFullscreen);
    document.addEventListener(
      'webkitfullscreenchange' as 'fullscreenchange',
      syncFullscreen
    );

    let settled = false;
    let timedOut = false;
    let styleSettled = false;

    const fallBackFromMapbox = (reason: string) => {
      if (settled || provider !== 'mapbox' || lightsOff) return;
      settled = true;
      console.warn(reason);
      setProvider('carto');
    };

    const timer = window.setTimeout(() => {
      if (
        timedOut ||
        styleSettled ||
        !map.current ||
        map.current !== mapInstance
      )
        return;
      if (mapInstance.isStyleLoaded()) return;
      timedOut = true;
      if (provider === 'mapbox' && !lightsOff) {
        fallBackFromMapbox(
          'Track map style load timed out; falling back to CARTO basemap'
        );
      } else if (!lightsOff) {
        console.warn(
          'Track map CARTO style load timed out; falling back to blank basemap'
        );
        mapInstance.setStyle(blankMapStyle(bg));
      }
    }, MAP_STYLE_LOAD_TIMEOUT_MS);

    const onError = (event: mapboxgl.ErrorEvent) => {
      if (map.current !== mapInstance) return;
      if (isMapboxAuthError(event.error)) {
        fallBackFromMapbox('Mapbox auth failed; falling back to CARTO basemap');
      }
    };
    mapInstance.on('error', onError);

    const onUserCameraChange = (event: { originalEvent?: Event }) => {
      if (!event.originalEvent) return;
      if (chaseRef.current.isAnimating() || orbitRef.current.isAnimating())
        return;
      if (map.current !== mapInstance) return;
      try {
        if (
          mapInstance.getLayer('all-routes') ||
          mapInstance.getLayer('selected')
        ) {
          setNeedsRecenter(true);
        }
      } catch {
        /* style not ready */
      }
    };

    mapInstance.on('style.load', () => {
      if (map.current !== mapInstance) return;
      if (!timedOut) {
        styleSettled = true;
        settled = true;
        window.clearTimeout(timer);
      }
      mapReady.current = true;
      styleIdleRef.current = false;
      // Blank privacy styles can already be idle inside this event, so draw now.
      updateRoutesRef.current();
      mapInstance.once('idle', () => {
        if (map.current !== mapInstance) return;
        styleIdleRef.current = true;
        updateRoutesRef.current();
      });
    });
    mapInstance.on('dragend', onUserCameraChange);
    mapInstance.on('zoomend', onUserCameraChange);
    mapInstance.on('rotateend', onUserCameraChange);
    mapInstance.on('pitchend', onUserCameraChange);

    const chase = chaseRef.current;
    const orbit = orbitRef.current;
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener('fullscreenchange', syncFullscreen);
      document.removeEventListener(
        'webkitfullscreenchange' as 'fullscreenchange',
        syncFullscreen
      );
      detachModeButtons?.();
      chase.stop({ silent: true });
      orbit.dispose();
      mapInstance.off('error', onError);
      mapInstance.off('dragend', onUserCameraChange);
      mapInstance.off('zoomend', onUserCameraChange);
      mapInstance.off('rotateend', onUserCameraChange);
      mapInstance.off('pitchend', onUserCameraChange);
      mapInstance.remove();
      if (map.current === mapInstance) {
        map.current = null;
      }
      mapReady.current = false;
      styleIdleRef.current = false;
      animKeyRef.current = null;
    };
  }, [dark, lightsOff, provider, locale, t]);

  useEffect(() => {
    setNeedsRecenter(false);
    if (mapReady.current && styleIdleRef.current) {
      updateRoutesRef.current();
    }
  }, [activity, activities]);

  useEffect(() => {
    if (!map.current?.isStyleLoaded()) return;
    applyLightsOff(map.current, lightsOff);
    if (map.current.getLayer('all-routes') && !activityRef.current) {
      map.current.setPaintProperty(
        'all-routes',
        'line-width',
        lightsOff ? 2 : 1.2
      );
      map.current.setPaintProperty(
        'all-routes',
        'line-opacity',
        lightsOff ? 0.85 : 0.5
      );
    }
  }, [lightsOff]);

  return (
    <div
      ref={bindFsRoot}
      className={`route-map-hover-ctrls route-map-fs-root relative h-full w-full${
        chasing ? 'is-playing' : ''
      }`}
      style={
        {
          ...(lightsOff ? { backgroundColor: bg } : null),
          ...(chasing ? { '--playback-hud-height': `${hudHeight}px` } : null),
        } as CSSProperties
      }
    >
      {canOffer3d || needsRecenter ? (
        <div className="route-map-top-left absolute top-3 left-3 z-10 flex items-center gap-2">
          {canOffer3d ? (
            <button
              type="button"
              className={`route-map-toolbar-3d${view3d ? 'is-active' : ''}`}
              aria-pressed={view3d}
              aria-label={view3d ? t('disable3d') : t('enable3d')}
              title={view3d ? t('disable3d') : t('enable3d')}
              onClick={handleToggle3d}
            >
              3D
            </button>
          ) : null}
          {needsRecenter ? (
            <button
              type="button"
              className="route-map-recenter"
              aria-label={t('locateTrack')}
              title={t('locateTrack')}
              onClick={() => refitViewRef.current()}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 2v4m0 12v4M2 12h4m12 0h4M12 8a4 4 0 100 8 4 4 0 000-8z"
                />
              </svg>
            </button>
          ) : null}
        </div>
      ) : null}
      <div ref={mapContainer} className="h-full w-full" />
      {chasing && playbackSnap ? (
        <PlaybackHudView
          snap={playbackSnap}
          hrSeries={playbackSeries?.hr ?? null}
          timeSeries={playbackSeries?.time ?? null}
          movingTimeSec={activity ? parseMovingTime(activity.moving_time) : 0}
          averageSpeedMs={activity?.average_speed ?? 0}
          fullscreen={isFullscreen}
          dark={dark !== false}
          exporting={exporting}
          exportEnding={exportEnding}
          exportMessage={exportMessage}
          onTogglePause={() => {
            if (chaseRef.current.isPaused()) chaseRef.current.resume();
            else chaseRef.current.pause();
          }}
          onCycleSpeed={() => {
            chaseRef.current.setSpeed(
              nextPlaybackSpeed(chaseRef.current.getSpeed())
            );
          }}
          onSeek={(p) => chaseRef.current.seek(p)}
          onShowEndpointsChange={(show) =>
            chaseRef.current.setShowEndpoints(show)
          }
          onExport={(opts) => {
            void handleExportVideo(opts);
          }}
          onHeightChange={setHudHeight}
        />
      ) : null}
    </div>
  );
}

function getColor(a: Activity): string {
  if (a.type === 'Run') {
    const km = a.distance / 1000;
    return km > 20 ? '#ef4444' : '#e8663d';
  }
  if (a.type === 'Ride') return '#4f7ce0';
  if (a.type === 'Hike') return '#22c55e';
  return '#7b61d9';
}

export function TracksPage({
  activities,
  onBack,
  onSelectActivity,
  getTitle,
  lightsOff = false,
  dark = true,
}: TracksPageProps) {
  const { locale } = useLocale();
  const allYears = getAvailableYears(activities);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [sportFilter, setSportFilter] = useState<SportType | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(
    null
  );
  const [mapPlaying, setMapPlaying] = useState(false);
  const [sortBy, setSortBy] = useState<'date' | 'distance'>('date');

  // Export
  const captureRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  // Year pagination
  const MAX_YEARS = 10;
  const [yearPage, setYearPage] = useState(0);
  const totalYearPages = Math.ceil(allYears.length / MAX_YEARS);
  const visibleYears = allYears.slice(
    yearPage * MAX_YEARS,
    yearPage * MAX_YEARS + MAX_YEARS
  );

  // Determine which sport types exist
  const hasSport = (t: SportType) => activities.some((a) => a.type === t);

  // Filtered base (year + sport)
  const base = activities.filter((a) => {
    if (
      selectedYear !== null &&
      new Date(a.start_date_local).getFullYear() !== selectedYear
    )
      return false;
    if (sportFilter !== null && a.type !== sportFilter) return false;
    return true;
  });

  const withPolyline = base.filter(
    (a) => a.summary_polyline && a.summary_polyline.length > 20
  );

  // Stats for left panel
  const totalDist = base.reduce((s, a) => s + a.distance, 0);
  const totalTime = base.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  );
  const runs = base.filter((a) => a.type === 'Run' && a.average_speed > 0);
  const avgPace =
    runs.length > 0
      ? runs.reduce((s, a) => s + a.average_speed, 0) / runs.length
      : 0;

  // Cluster tracks — defer heavy work
  type Cluster = { representative: Activity; count: number; color: string };
  const [clusteredTracks, setClusteredTracks] = useState<Cluster[]>([]);
  const [clustering, setClustering] = useState(true);

  useEffect(() => {
    setClustering(true);
    const id = setTimeout(() => {
      const acts = [...withPolyline].sort(
        (a, b) =>
          new Date(b.start_date_local).getTime() -
          new Date(a.start_date_local).getTime()
      );
      type Decoded = {
        start: [number, number];
        end: [number, number];
        distBucket: number;
      };
      const decoded: (Decoded | null)[] = acts.map((a) => {
        try {
          const coords = polyline.decode(a.summary_polyline!);
          if (coords.length < 2) return null;
          return {
            start: coords[0] as [number, number],
            end: coords[coords.length - 1] as [number, number],
            distBucket: Math.round(a.distance / 2000),
          };
        } catch {
          return null;
        }
      });
      const clusters: Cluster[] = [];
      const used = new Set<number>();
      for (let i = 0; i < acts.length; i++) {
        if (used.has(i)) continue;
        const di = decoded[i];
        if (!di) continue;
        let count = 1;
        for (let j = i + 1; j < acts.length; j++) {
          if (used.has(j)) continue;
          const dj = decoded[j];
          if (!dj || di.distBucket !== dj.distBucket) continue;
          const startClose =
            Math.abs(di.start[0] - dj.start[0]) < 0.005 &&
            Math.abs(di.start[1] - dj.start[1]) < 0.005;
          const endClose =
            Math.abs(di.end[0] - dj.end[0]) < 0.005 &&
            Math.abs(di.end[1] - dj.end[1]) < 0.005;
          if (startClose && endClose) {
            used.add(j);
            count++;
          }
        }
        used.add(i);
        clusters.push({
          representative: acts[i],
          count,
          color: getColor(acts[i]),
        });
      }
      setClusteredTracks(clusters);
      setClustering(false);
    }, 0);
    return () => clearTimeout(id);
  }, [withPolyline.length, selectedYear, sportFilter]);

  const handleSelectTrack = (a: Activity) => {
    setSelectedActivity((prev) => (prev?.run_id === a.run_id ? null : a));
    onSelectActivity?.(a);
  };

  const allSportTabs: { label: string; value: SportType; color: string }[] = [
    { label: locale === 'zh' ? '跑步' : 'Run', value: 'Run', color: '#e8663d' },
  ];
  const availableSportTabs = allSportTabs.filter((t) => hasSport(t.value));
  const showSportFilter = availableSportTabs.length > 1;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-6 md:px-6">
      {/* Top bar: back + title */}
      <div className="mb-5 flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex shrink-0 items-center gap-1.5 text-sm text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)]"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          {locale === 'zh' ? '返回' : 'Back'}
        </button>
        <h1 className="shrink-0 text-lg font-bold">
          {locale === 'zh' ? '轨迹墙' : 'Track Wall'}
        </h1>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[340px_1fr]">
        {/* Mobile: contents so map can sticky while track wall scrolls.
            Desktop: stacked left column. */}
        <div className="contents lg:flex lg:flex-col lg:gap-4">
          {/* Stats card */}
          <div className="card order-1 p-4 lg:order-none">
            <p className="eyebrow mb-3 text-[10px] text-[var(--color-muted)]">
              {selectedYear ?? (locale === 'zh' ? '全部' : 'Total')}
            </p>
            <div className="space-y-3">
              <div>
                <p className="eyebrow text-[10px] text-[var(--color-muted)]">
                  {locale === 'zh' ? '活动' : 'Activities'}
                </p>
                <p className="metric text-2xl font-semibold text-[var(--color-accent)]">
                  {base.length}
                </p>
              </div>
              <div>
                <p className="eyebrow text-[10px] text-[var(--color-muted)]">
                  {locale === 'zh' ? '距离' : 'Distance'}
                </p>
                <p className="metric text-2xl font-semibold">
                  {formatDistance(totalDist)}{' '}
                  <span className="text-sm font-normal text-[var(--color-muted)]">
                    km
                  </span>
                </p>
              </div>
              <div>
                <p className="eyebrow text-[10px] text-[var(--color-muted)]">
                  {locale === 'zh' ? '时间' : 'Time'}
                </p>
                <p className="metric text-lg font-semibold">
                  {Math.floor(totalTime / 3600)}h{' '}
                  {Math.floor((totalTime % 3600) / 60)}m
                </p>
              </div>
              {avgPace > 0 && (
                <div>
                  <p className="eyebrow text-[10px] text-[var(--color-muted)]">
                    {locale === 'zh' ? '均配速' : 'Avg Pace'}
                  </p>
                  <p className="metric text-lg font-semibold">
                    {formatPace(avgPace)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Activity detail — hide bulky static summary while playback HUD is up */}
          {selectedActivity && !mapPlaying && (
            <div className="card order-3 px-4 py-3 lg:order-none">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="eyebrow text-[10px] text-[var(--color-muted)]">
                  {locale === 'zh' ? '已选记录' : 'Selected'}
                </p>
                <button
                  onClick={() => {
                    setMapPlaying(false);
                    setSelectedActivity(null);
                  }}
                  className="text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)]"
                >
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <p className="mb-0.5 truncate text-xs font-semibold">
                {getTitle ? getTitle(selectedActivity) : selectedActivity.name}
              </p>
              <p className="mb-2 text-[10px] text-[var(--color-muted)]">
                {new Date(selectedActivity.start_date_local).toLocaleDateString(
                  locale === 'zh' ? 'zh-CN' : 'en-US',
                  { year: 'numeric', month: 'short', day: 'numeric' }
                )}{' '}
                {new Date(selectedActivity.start_date_local).toLocaleTimeString(
                  locale === 'zh' ? 'zh-CN' : 'en-US',
                  { hour: '2-digit', minute: '2-digit' }
                )}
              </p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="eyebrow text-[9px] text-[var(--color-muted)]">
                    {locale === 'zh' ? '距离' : 'Distance'}
                  </p>
                  <p className="metric text-base leading-tight font-semibold">
                    {(selectedActivity.distance / 1000).toFixed(2)}{' '}
                    <span className="text-[10px] font-normal text-[var(--color-muted)]">
                      km
                    </span>
                  </p>
                </div>
                <div>
                  <p className="eyebrow text-[9px] text-[var(--color-muted)]">
                    {locale === 'zh' ? '时间' : 'Time'}
                  </p>
                  <p className="metric text-base leading-tight font-semibold">
                    {(() => {
                      const s = parseMovingTime(selectedActivity.moving_time);
                      return `${Math.floor(s / 3600) ? Math.floor(s / 3600) + 'h ' : ''}${Math.floor((s % 3600) / 60)}m`;
                    })()}
                  </p>
                </div>
                {selectedActivity.average_speed > 0 && (
                  <div>
                    <p className="eyebrow text-[9px] text-[var(--color-muted)]">
                      {locale === 'zh' ? '配速' : 'Pace'}
                    </p>
                    <p className="metric text-base leading-tight font-semibold">
                      {formatPace(selectedActivity.average_speed)}{' '}
                      <span className="text-[10px] font-normal text-[var(--color-muted)]">
                        /km
                      </span>
                    </p>
                  </div>
                )}
                {selectedActivity.elevation_gain != null &&
                  selectedActivity.elevation_gain > 0 && (
                    <div>
                      <p className="eyebrow text-[9px] text-[var(--color-muted)]">
                        {locale === 'zh' ? '爬升' : 'Elev'}
                      </p>
                      <p className="metric text-base leading-tight font-semibold">
                        {Math.round(selectedActivity.elevation_gain)}{' '}
                        <span className="text-[10px] font-normal text-[var(--color-muted)]">
                          m
                        </span>
                      </p>
                    </div>
                  )}
                {selectedActivity.average_heartrate != null &&
                  selectedActivity.average_heartrate > 0 && (
                    <div>
                      <p className="eyebrow text-[9px] text-[var(--color-muted)]">
                        {locale === 'zh' ? '心率' : 'HR'}
                      </p>
                      <p className="metric text-base leading-tight font-semibold">
                        {Math.round(selectedActivity.average_heartrate)}{' '}
                        <span className="text-[10px] font-normal text-[var(--color-muted)]">
                          bpm
                        </span>
                      </p>
                    </div>
                  )}
              </div>
            </div>
          )}

          {/* Map — sticky on mobile while browsing the track wall.
              Idle stays compact; playback grows so HUD + ctrl stack + logo fit. */}
          <div className="sticky top-16 z-40 order-2 -my-2 py-2 lg:static lg:z-auto lg:order-none lg:my-0 lg:py-0">
            <div
              className={`card overflow-hidden transition-[height] duration-300 ease-out [--card-shadow:var(--shadow-card-hover)] lg:[--card-shadow:var(--shadow-card)] ${
                mapPlaying
                  ? 'h-[min(70vh,520px)] md:h-[min(65vh,560px)]'
                  : 'h-[280px] md:h-[360px]'
              }`}
            >
              <TrackMap
                activity={selectedActivity}
                activities={withPolyline}
                dark={dark}
                lightsOff={lightsOff}
                onPlaybackChange={setMapPlaying}
              />
            </div>
          </div>
        </div>

        {/* Right: track grid with year filter inside */}
        <div className="order-4 min-w-0 lg:order-none">
          <div ref={captureRef} className="card p-4">
            {/* Year pills (scroll) + export; sport filter only when multiple sports */}
            <div className="mb-4 space-y-2.5 border-b border-[var(--color-border)] pb-3">
              <div className="flex min-w-0 items-center gap-2">
                <div className="-mx-1 flex min-w-0 flex-1 flex-nowrap items-center gap-1.5 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                  {totalYearPages > 1 && (
                    <button
                      type="button"
                      onClick={() => setYearPage((p) => Math.max(0, p - 1))}
                      disabled={yearPage === 0}
                      className="shrink-0 cursor-pointer px-1 text-base leading-none text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-30"
                    >
                      ‹
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setSelectedYear(null)}
                    className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-all ${selectedYear === null ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '全部' : 'All'}
                  </button>
                  {visibleYears.map((yr) => (
                    <button
                      type="button"
                      key={yr}
                      onClick={() =>
                        setSelectedYear(selectedYear === yr ? null : yr)
                      }
                      className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-all ${selectedYear === yr ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                    >
                      {yr}
                    </button>
                  ))}
                  {totalYearPages > 1 && (
                    <button
                      type="button"
                      onClick={() =>
                        setYearPage((p) => Math.min(totalYearPages - 1, p + 1))
                      }
                      disabled={yearPage === totalYearPages - 1}
                      className="shrink-0 cursor-pointer px-1 text-base leading-none text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-30"
                    >
                      ›
                    </button>
                  )}
                </div>
                <button
                  onClick={async () => {
                    if (!captureRef.current || exporting) return;
                    setExporting(true);
                    try {
                      const el = captureRef.current;
                      const prevOverflow = el.style.overflow;
                      el.style.overflow = 'visible';
                      await new Promise((resolve) =>
                        requestAnimationFrame(resolve)
                      );
                      const dataUrl = await toPng(el, {
                        pixelRatio: 2,
                        cacheBust: true,
                      });
                      el.style.overflow = prevOverflow;
                      const link = document.createElement('a');
                      const label = selectedYear ?? 'all';
                      link.download = `tracks-${label}.png`;
                      link.href = dataUrl;
                      link.click();
                    } catch (err) {
                      console.error('Export failed:', err);
                    } finally {
                      setExporting(false);
                    }
                  }}
                  disabled={exporting}
                  className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-[var(--color-muted)] transition-all hover:text-[var(--color-text)] disabled:opacity-50"
                  title={locale === 'zh' ? '导出图片' : 'Export as image'}
                >
                  {exporting ? (
                    <svg
                      className="h-3.5 w-3.5 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="h-3.5 w-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  )}
                </button>
              </div>
              {showSportFilter ? (
                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setSportFilter(null)}
                    className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition-all ${sportFilter === null ? 'border-transparent bg-[var(--color-accent)] text-white' : 'border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '全部' : 'All'}
                  </button>
                  {availableSportTabs.map(({ label, value, color }) => (
                    <button
                      type="button"
                      key={value}
                      onClick={() =>
                        setSportFilter(sportFilter === value ? null : value)
                      }
                      className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition-all ${sportFilter === value ? 'border-transparent text-white' : 'border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                      style={
                        sportFilter === value ? { backgroundColor: color } : {}
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            {clustering ? (
              <div className="flex flex-wrap gap-1">
                {Array.from({ length: 40 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-[72px] w-[72px] animate-pulse rounded bg-[var(--color-sunken)] md:h-[80px] md:w-[80px]"
                    style={{ animationDelay: `${i * 20}ms` }}
                  />
                ))}
              </div>
            ) : clusteredTracks.length === 0 ? (
              <p className="py-8 text-center text-sm text-[var(--color-muted)]">
                {locale === 'zh' ? '暂无轨迹数据' : 'No tracks found'}
              </p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {[...clusteredTracks]
                  .sort((a, b) =>
                    sortBy === 'distance'
                      ? b.representative.distance - a.representative.distance
                      : new Date(b.representative.start_date_local).getTime() -
                        new Date(a.representative.start_date_local).getTime()
                  )
                  .map(({ representative: a, count, color }) => (
                    <div key={a.run_id} className="relative">
                      <TrackThumb
                        activity={a}
                        color={color}
                        selected={selectedActivity?.run_id === a.run_id}
                        onClick={() => handleSelectTrack(a)}
                        title={
                          getTitle
                            ? `${getTitle(a)} — ${(a.distance / 1000).toFixed(1)} km`
                            : undefined
                        }
                      />
                      {count > 1 && (
                        <span className="pointer-events-none absolute right-1 bottom-1 rounded bg-[var(--color-bg)]/80 px-1 py-0.5 text-[9px] leading-none font-bold text-[var(--color-muted)]">
                          ×{count}
                        </span>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* Legend + sort */}
            {!clustering && clusteredTracks.length > 0 && (
              <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-muted)]">
                {sportFilter === null || sportFilter === 'Run' ? (
                  <>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-0.5 w-3 rounded bg-[#e8663d]" />
                      {locale === 'zh' ? '跑步' : 'Run'}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-0.5 w-3 rounded bg-[#ef4444]" />
                      {locale === 'zh' ? '跑步 >20km' : 'Run >20km'}
                    </span>
                  </>
                ) : null}
                {null}
                {null}
                <div className="ml-auto flex items-center gap-1">
                  <span>
                    {clusteredTracks.length}{' '}
                    {locale === 'zh' ? '条路线' : 'routes'}
                  </span>
                  <span className="mx-1.5 text-[var(--color-border)]">·</span>
                  <button
                    type="button"
                    onClick={() => setSortBy('date')}
                    className={`cursor-pointer transition-colors ${sortBy === 'date' ? 'font-medium text-[var(--color-text)]' : 'hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '时间' : 'Date'}
                  </button>
                  <span className="text-[var(--color-border)]">/</span>
                  <button
                    type="button"
                    onClick={() => setSortBy('distance')}
                    className={`cursor-pointer transition-colors ${sortBy === 'distance' ? 'font-medium text-[var(--color-text)]' : 'hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '距离' : 'Dist'}
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* end track grid card */}
        </div>
        {/* end right column */}
      </div>
    </div>
  );
}
