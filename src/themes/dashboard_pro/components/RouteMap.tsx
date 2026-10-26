import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from 'react';
import { useMapChromeIdle } from '@/hooks/useMapChromeIdle';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './RouteMap.css';
import * as polyline from '@mapbox/polyline';
import type { Activity } from '@/types';
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
import { useLocale } from '@/hooks/useLocale';
import type { Coordinate } from '@/utils/routeAnimation';
import {
  CHASE_LAYER_IDS,
  clearMapTerrain,
  attachMapModeButtons,
  createMapChaseController,
  createMapOrbitController,
  isMapFullscreen,
  removeChaseHighlight,
  updateChaseControlButton,
  updateFullscreenButton,
  type MapModeControlHandles,
  type PlaybackProgress,
} from '@/utils/mapChase3d';
import {
  fitMapToEndCard,
  fitMapToRouteOverview,
  fitMapToSelectedRoute,
  overviewOrbitCoords,
  waitForMapIdle,
} from '@/utils/mapRouteFit';
import { routeForActivity } from '@/core/routeFallback';
import {
  buildMapVideoEndCard,
  buildMapVideoOverlayStats,
  nextPlaybackSpeed,
  PlaybackHudView,
  usePlaybackSeries,
} from './PlaybackHud';
import { parseMovingTime } from '@/hooks/useActivities';
import { loadSplits } from '@/core/splits';
import { getPlaybackPrefs, setPlaybackPrefs } from '@/utils/playbackPrefs';
import {
  defaultMapVideoFilename,
  downloadBlob,
  MapVideoAbortedError,
  MapVideoUnsupportedError,
  phoneChaseZoomOutExtra,
  startMapVideoCapture,
  type MapVideoCapture,
} from '@/utils/exportMapVideo';

const ROUTE_LAYER_IDS = new Set(['routes', 'selected', ...CHASE_LAYER_IDS]);

interface RouteMapProps {
  activities: Activity[];
  /** Full history used to find a display-only route when the selection has no GPS. */
  allActivities?: Activity[];
  selectedActivity?: Activity | null;
  dark?: boolean;
  onClearSelection?: () => void;
  /** Hide basemap tiles; keep route lines (classic privacy lights-off) */
  lightsOff?: boolean;
  className?: string;
}

function applyLightsOff(map: mapboxgl.Map, lightsOff: boolean) {
  const styleJson = map.getStyle();
  if (!styleJson?.layers) return;
  for (const layer of styleJson.layers) {
    if (ROUTE_LAYER_IDS.has(layer.id)) {
      map.setLayoutProperty(layer.id, 'visibility', 'visible');
      continue;
    }
    if (layer.id === 'background') {
      map.setLayoutProperty(layer.id, 'visibility', 'visible');
      continue;
    }
    map.setLayoutProperty(
      layer.id,
      'visibility',
      lightsOff ? 'none' : 'visible'
    );
  }
}

function routeColor(a: Activity): string {
  return a.type === 'Run' ? '#e8663d' : '#4f7ce0';
}

export function RouteMap({
  activities,
  allActivities,
  selectedActivity,
  dark,
  onClearSelection,
  lightsOff = false,
  className = '',
}: RouteMapProps) {
  const { locale, t } = useLocale();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const lightsOffRef = useRef(lightsOff);
  const routePool = allActivities ?? activities;
  const displayActivity = useMemo(
    () =>
      selectedActivity ? routeForActivity(selectedActivity, routePool) : null,
    [selectedActivity, routePool]
  );
  const fallbackActivity =
    selectedActivity &&
    displayActivity &&
    displayActivity.run_id !== selectedActivity.run_id
      ? displayActivity
      : null;
  const activitiesRef = useRef(activities);
  const selectedRef = useRef(selectedActivity);
  const displayRef = useRef(displayActivity);
  const chaseRef = useRef(createMapChaseController());
  const orbitRef = useRef(createMapOrbitController());
  const selectedCoordsRef = useRef<Coordinate[] | null>(null);
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
  const selectedId = selectedActivity ? String(selectedActivity.run_id) : null;
  const chasing = chaseRunId != null && chaseRunId === selectedId;
  const playbackSeries = usePlaybackSeries(
    chasing,
    selectedActivity?.run_id ?? null
  );
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
      movingTimeSec: selectedActivity
        ? parseMovingTime(selectedActivity.moving_time)
        : 0,
      averageSpeedMs: selectedActivity?.average_speed ?? 0,
      startDateLocal: selectedActivity?.start_date_local ?? '',
      sport: selectedActivity?.type ?? 'Run',
      distanceMeters: selectedActivity?.distance ?? 0,
      hrBpm:
        selectedActivity?.average_heartrate != null &&
        selectedActivity.average_heartrate > 0
          ? Math.round(selectedActivity.average_heartrate)
          : null,
    };
  }, [playbackSeries, selectedActivity]);
  const modeHandlesRef = useRef<MapModeControlHandles>({
    fullscreenButton: null,
    chaseButton: null,
  });
  const toggleChaseRef = useRef<() => void>(() => {});
  const styleIdleRef = useRef(false);
  const refitViewRef = useRef<() => void>(() => {});
  const [needsRecenter, setNeedsRecenter] = useState(false);
  const [provider, setProvider] = useState<BasemapProvider>(
    initialBasemapProvider
  );
  const useBlank = lightsOff;
  // Orbit / DEM / buildings are best-effort in injectMapTerrain (no-op on CARTO).
  const can3d = !lightsOff;
  const hasOwnGps = Boolean(
    selectedActivity &&
    displayActivity &&
    displayActivity.run_id === selectedActivity.run_id
  );
  /** 3D stays available in overview; only privacy blanks it. */
  const canOffer3d = can3d;
  /** Chase playback works on the blank privacy basemap; 3D does not. */
  const canOfferPlayback = hasOwnGps;
  const bg = dark !== false ? '#0b0d10' : '#f4f5f7';
  const style = useBlank
    ? blankMapStyle(bg)
    : basemapStyleUrl(provider, dark !== false);

  const abortVideoExport = () => {
    videoCaptureRef.current?.abort();
    videoCaptureRef.current = null;
    setExporting(false);
    setExportEnding(false);
    chaseRef.current.setZoomOutExtra(0);
    chaseRef.current.setStrokeScale(1);
  };

  const stopChase = () => {
    abortVideoExport();
    chaseRef.current.stop({ silent: true });
    setPlaybackSnap(null);
  };

  const flattenView = (map: mapboxgl.Map) => {
    orbitRef.current.stop();
    if (!chaseRef.current.isAnimating()) {
      clearMapTerrain(map);
      map.easeTo({ pitch: 0, bearing: 0, duration: 600 });
    }
  };

  const startOrbitIfNeeded = (map: mapboxgl.Map, coords: Coordinate[]) => {
    if (!view3dRef.current || !can3d || coords.length < 2) {
      flattenView(map);
      return;
    }
    if (chaseRef.current.isAnimating()) return;
    orbitRef.current.start({
      map,
      coords,
      isDark: dark !== false,
    });
  };

  useEffect(() => {
    lightsOffRef.current = lightsOff;
    activitiesRef.current = activities;
    selectedRef.current = selectedActivity;
    displayRef.current = displayActivity;
  });

  const updateRoutesRef = useRef<() => void>(() => {});
  useLayoutEffect(() => {
    updateRoutesRef.current = () => {
      const map = mapRef.current;
      if (!map || !map.isStyleLoaded()) return;

      stopChase();
      orbitRef.current.stop();
      setChaseRunId(null);
      if (map.getLayer('routes')) map.removeLayer('routes');
      if (map.getSource('routes')) map.removeSource('routes');
      if (map.getLayer('selected')) map.removeLayer('selected');
      if (map.getSource('selected')) map.removeSource('selected');
      removeChaseHighlight(map);

      const selected = selectedRef.current;
      const display = displayRef.current;
      const acts = activitiesRef.current;
      const showingFallback = Boolean(
        selected && display && display.run_id !== selected.run_id
      );

      if (selected && display?.summary_polyline) {
        const coords = polyline
          .decode(display.summary_polyline)
          .map(([lat, lng]) => [lng, lat] as Coordinate);
        selectedCoordsRef.current = coords;
        const color = routeColor(display);

        map.addSource('selected', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: { type: 'LineString', coordinates: coords },
          },
        });

        map.addLayer({
          id: 'selected',
          type: 'line',
          source: 'selected',
          paint: {
            'line-color': color,
            'line-width': 3,
            'line-opacity': showingFallback ? 0.75 : 0.9,
            ...(showingFallback ? { 'line-dasharray': [2, 2] } : {}),
          },
        });

        if (view3dRef.current && !showingFallback && can3d) {
          startOrbitIfNeeded(map, coords);
        } else {
          flattenView(map);
          fitMapToSelectedRoute(map, coords, lightsOffRef.current);
        }
        applyLightsOff(map, lightsOffRef.current);
        return;
      }

      if (selected) {
        selectedCoordsRef.current = null;
        flattenView(map);
        applyLightsOff(map, lightsOffRef.current);
        return;
      }

      selectedCoordsRef.current = null;

      const features = acts
        .filter((a) => a.summary_polyline)
        .map((a) => {
          const coords = polyline
            .decode(a.summary_polyline!)
            .map(([lat, lng]) => [lng, lat]);
          return {
            type: 'Feature' as const,
            properties: { type: a.type },
            geometry: {
              type: 'LineString' as const,
              coordinates: coords,
            },
          };
        });

      if (features.length === 0) {
        flattenView(map);
        applyLightsOff(map, lightsOffRef.current);
        return;
      }

      map.addSource('routes', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features,
        },
      });

      map.addLayer({
        id: 'routes',
        type: 'line',
        source: 'routes',
        paint: {
          'line-color': [
            'match',
            ['get', 'type'],
            'Run',
            '#e8663d',
            'Ride',
            '#4f7ce0',
            '#7b61d9',
          ],
          'line-width': lightsOffRef.current ? 2 : 1.5,
          'line-opacity': lightsOffRef.current ? 0.85 : 0.6,
        },
      });

      const orbitCoords = overviewOrbitCoords(acts);
      if (view3dRef.current && can3d && orbitCoords.length > 0) {
        startOrbitIfNeeded(map, orbitCoords);
      } else {
        flattenView(map);
        fitMapToRouteOverview(map, acts, lightsOffRef.current);
      }
      applyLightsOff(map, lightsOffRef.current);
    };
  });

  useEffect(() => {
    refitViewRef.current = () => {
      const map = mapRef.current;
      if (!map?.isStyleLoaded()) return;
      const selected = selectedRef.current;
      const coords = selectedCoordsRef.current;
      if (selected && coords && coords.length > 0) {
        if (view3dRef.current && can3d) {
          startOrbitIfNeeded(map, coords);
        } else {
          fitMapToSelectedRoute(map, coords, lightsOffRef.current);
        }
      } else if (view3dRef.current && can3d) {
        const orbitCoords = overviewOrbitCoords(activitiesRef.current);
        if (orbitCoords.length > 0) startOrbitIfNeeded(map, orbitCoords);
        else {
          flattenView(map);
          fitMapToRouteOverview(
            map,
            activitiesRef.current,
            lightsOffRef.current
          );
        }
      } else {
        flattenView(map);
        fitMapToRouteOverview(map, activitiesRef.current, lightsOffRef.current);
      }
      setNeedsRecenter(false);
    };
  });

  const restoreSelectedLine = (map: mapboxgl.Map) => {
    if (map.getLayer('selected')) {
      map.setPaintProperty('selected', 'line-opacity', 0.9);
    }
    removeChaseHighlight(map);
  };

  const resolveOrbitCoords = (): Coordinate[] | null => {
    const selected = selectedCoordsRef.current;
    if (selected && selected.length >= 2) return selected;
    const overview = overviewOrbitCoords(activitiesRef.current);
    return overview.length > 0 ? overview : null;
  };

  const handleToggle3d = () => {
    const map = mapRef.current;
    const coords = resolveOrbitCoords();
    if (!map || !coords || !canOffer3d) return;
    const next = !view3dRef.current;
    view3dRef.current = next;
    setView3d(next);
    if (chaseRef.current.isAnimating()) {
      chaseRef.current.setCameraMode(next ? '3d' : '2d');
      return;
    }
    if (next) {
      startOrbitIfNeeded(map, coords);
      return;
    }
    flattenView(map);
    if (selectedCoordsRef.current && selectedCoordsRef.current.length >= 2) {
      fitMapToSelectedRoute(
        map,
        selectedCoordsRef.current,
        lightsOffRef.current
      );
    } else {
      fitMapToRouteOverview(map, activitiesRef.current, lightsOffRef.current);
    }
  };

  const handleToggleChase = () => {
    const map = mapRef.current;
    const selected = selectedRef.current;
    const coords = selectedCoordsRef.current;
    if (!map || !selected || !coords || !canOfferPlayback) return;

    if (chaseRef.current.isAnimating()) {
      stopChase();
      setChaseRunId(null);
      restoreSelectedLine(map);
      if (view3dRef.current) {
        startOrbitIfNeeded(map, coords);
      } else {
        flattenView(map);
        fitMapToSelectedRoute(map, coords, lightsOffRef.current);
      }
      return;
    }

    orbitRef.current.stop();
    if (map.getLayer('selected')) {
      map.setPaintProperty('selected', 'line-opacity', 0);
    }

    const runId = String(selected.run_id);
    chaseRef.current.start(
      {
        map,
        coords,
        color: routeColor(selected),
        distanceKm: selected.distance / 1000,
        runId,
        isDark: dark !== false,
        cameraMode: can3d && view3dRef.current ? '3d' : '2d',
        showEndpoints: getPlaybackPrefs().showEndpoints,
        lockOrientation: getPlaybackPrefs().lockOrientation,
        endpointTitles:
          locale === 'en'
            ? { start: 'Start', end: 'Finish' }
            : { start: '起点', end: '终点' },
        compassTitles: {
          lock: t('bearingLock'),
          follow: t('bearingFollow'),
        },
        overviewLayerId: map.getLayer('routes') ? 'routes' : undefined,
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
          restoreSelectedLine(map);
          if (!view3dRef.current) clearMapTerrain(map);
          // Orbit / fitBounds wait until card height + resize settle (chasing effect).
        },
        onBearingLockChange: (locked) => {
          setPlaybackPrefs({ lockOrientation: locked });
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
    const map = mapRef.current;
    if (!map || !chasing) return;
    try {
      // Phone 9:16 cover reads closer — pull 2D chase out for the clip only.
      const canvas = map.getCanvas();
      chaseRef.current.setZoomOutExtra(
        opts.sizeMode === 'phone'
          ? phoneChaseZoomOutExtra(canvas.clientWidth, canvas.clientHeight)
          : 0
      );
      // Always restart from the beginning for a clean export clip.
      chaseRef.current.seek(0);
      if (chaseRef.current.isPaused()) chaseRef.current.resume();
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      });
      const runId = selectedActivity?.run_id;
      if (runId != null && caloriesRef.current.runId !== runId) {
        caloriesRef.current = { runId, kcal: null };
        void loadSplits(runId).then((data) => {
          if (caloriesRef.current.runId !== runId) return;
          const kcal = data?.summary?.calories;
          caloriesRef.current.kcal = kcal != null && kcal > 0 ? kcal : null;
        });
      }
      const capture = startMapVideoCapture({
        mapCanvas: map.getCanvas(),
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
          const live = mapRef.current;
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
          const live = mapRef.current;
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
        /* user/stopChase cancelled */
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
        chaseRef.current.stop({ silent: true });
        setChaseRunId(null);
        setPlaybackSnap(null);
        const live = mapRef.current;
        if (live) {
          restoreSelectedLine(live);
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

  // Card height animates with playback — resize, then re-fit when ending.
  const wasChasingRef = useRef(false);
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const ending = wasChasingRef.current && !chasing;
    wasChasingRef.current = chasing;
    const tick = () => map.resize();
    tick();
    const t1 = window.setTimeout(tick, 80);
    const t2 = window.setTimeout(() => {
      tick();
      if (!ending) return;
      const coords = selectedCoordsRef.current;
      if (!coords || coords.length < 2) return;
      if (view3dRef.current) {
        startOrbitIfNeeded(map, coords);
      } else {
        fitMapToSelectedRoute(map, coords, lightsOffRef.current);
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
    const container = mapContainerRef.current;
    if (!container) return;

    if (MAPBOX_TOKEN) mapboxgl.accessToken = MAPBOX_TOKEN;

    styleIdleRef.current = false;

    const hasRouteLayers = (map: mapboxgl.Map) => {
      try {
        return Boolean(map.getLayer('routes') || map.getLayer('selected'));
      } catch {
        return false;
      }
    };

    const ensureRoutes = () => {
      const map = mapRef.current;
      if (!map?.isStyleLoaded()) return;
      styleIdleRef.current = true;
      if (chaseRef.current.isAnimating()) return;
      if (hasRouteLayers(map)) return;
      updateRoutesRef.current();
    };

    mapRef.current = new mapboxgl.Map({
      container,
      style,
      center: [121.4, 31.2],
      zoom: 10,
      pitch: 0,
      maxPitch: 85,
      attributionControl: false,
      /** Needed so WebGL frames remain readable for MediaRecorder export. */
      preserveDrawingBuffer: true,
      keyboard: false,
      language: mapLabelLanguage(locale),
      locale: mapboxControlLocale(t),
    });

    if (!useBlank) {
      mapRef.current.addControl(
        new mapboxgl.AttributionControl({ compact: true }),
        'bottom-right'
      );
    }

    let settled = false;
    let timedOut = false;

    const fallBackFromMapbox = (reason: string) => {
      if (settled || provider !== 'mapbox' || lightsOff) return;
      settled = true;
      console.warn(reason);
      setProvider('carto');
    };

    const timer = window.setTimeout(() => {
      if (!mapRef.current || mapRef.current.isStyleLoaded() || timedOut) return;
      timedOut = true;
      if (provider === 'mapbox' && !lightsOff) {
        fallBackFromMapbox(
          'Map style load timed out; falling back to CARTO basemap'
        );
      } else if (!lightsOff) {
        console.warn(
          'CARTO style load timed out; falling back to blank basemap'
        );
        mapRef.current.setStyle(blankMapStyle(bg));
      }
    }, MAP_STYLE_LOAD_TIMEOUT_MS);

    const onError = (event: mapboxgl.ErrorEvent) => {
      if (isMapboxAuthError(event.error)) {
        fallBackFromMapbox('Mapbox auth failed; falling back to CARTO basemap');
      }
    };

    mapRef.current.on('error', onError);
    const onUserCameraChange = (event: { originalEvent?: Event }) => {
      // Programmatic fitBounds/easeTo have no originalEvent; ignore those.
      if (!event.originalEvent) return;
      if (chaseRef.current.isAnimating() || orbitRef.current.isAnimating())
        return;
      const map = mapRef.current;
      if (!map) return;
      try {
        if (map.getLayer('routes') || map.getLayer('selected')) {
          setNeedsRecenter(true);
        }
      } catch {
        /* style not ready */
      }
    };

    mapRef.current.on('style.load', () => {
      styleIdleRef.current = false;
      if (!timedOut) {
        settled = true;
        window.clearTimeout(timer);
      }
      ensureRoutes();
    });
    mapRef.current.on('idle', ensureRoutes);
    mapRef.current.on('dragend', onUserCameraChange);
    mapRef.current.on('zoomend', onUserCameraChange);
    mapRef.current.on('rotateend', onUserCameraChange);
    mapRef.current.on('pitchend', onUserCameraChange);
    if (mapRef.current.isStyleLoaded()) ensureRoutes();

    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    const detachModeButtons = attachMapModeButtons(
      mapRef.current,
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
      const next = isMapFullscreen(mapRef.current);
      setIsFullscreen(next);
      requestAnimationFrame(() => mapRef.current?.resize());
    };
    document.addEventListener('fullscreenchange', syncFullscreen);
    document.addEventListener(
      'webkitfullscreenchange' as 'fullscreenchange',
      syncFullscreen
    );

    const resizeMap = () => {
      mapRef.current?.resize();
    };
    const ro = new ResizeObserver(() => {
      resizeMap();
      requestAnimationFrame(resizeMap);
    });
    ro.observe(container);

    const chase = chaseRef.current;
    const orbit = orbitRef.current;
    return () => {
      ro.disconnect();
      window.clearTimeout(timer);
      document.removeEventListener('fullscreenchange', syncFullscreen);
      document.removeEventListener(
        'webkitfullscreenchange' as 'fullscreenchange',
        syncFullscreen
      );
      detachModeButtons?.();
      chase.stop({ silent: true });
      orbit.dispose();
      styleIdleRef.current = false;
      mapRef.current?.off('error', onError);
      mapRef.current?.off('dragend', onUserCameraChange);
      mapRef.current?.off('zoomend', onUserCameraChange);
      mapRef.current?.off('rotateend', onUserCameraChange);
      mapRef.current?.off('pitchend', onUserCameraChange);
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // Recreate when basemap mode or UI language changes
  }, [dark, lightsOff, provider, locale, t]);

  useEffect(() => {
    setNeedsRecenter(false);
    if (styleIdleRef.current) {
      updateRoutesRef.current();
    }
  }, [activities, selectedActivity, displayActivity]);

  useEffect(() => {
    if (!mapRef.current?.isStyleLoaded()) return;
    applyLightsOff(mapRef.current, lightsOff);
    if (mapRef.current.getLayer('routes')) {
      mapRef.current.setPaintProperty(
        'routes',
        'line-width',
        lightsOff ? 2 : 1.5
      );
      mapRef.current.setPaintProperty(
        'routes',
        'line-opacity',
        lightsOff ? 0.85 : 0.6
      );
    }
  }, [lightsOff]);

  return (
    <div
      className={`card route-map-hover-ctrls relative overflow-hidden transition-[height] duration-300 ease-out ${
        chasing ? 'route-map--playing' : ''
      } ${className || 'h-[280px] md:h-[380px]'}`}
      style={lightsOff ? { backgroundColor: bg } : undefined}
    >
      {fallbackActivity ? (
        <p
          role="status"
          className="pointer-events-none absolute top-12 left-3 z-10 max-w-sm rounded-lg bg-[var(--color-card)] px-3 py-1.5 text-xs text-pretty text-[var(--color-muted)] shadow-md"
        >
          {t('routeFallback').replace(
            '{date}',
            fallbackActivity.start_date_local.slice(0, 10)
          )}
        </p>
      ) : selectedActivity && !displayActivity ? (
        <p
          role="status"
          className="pointer-events-none absolute top-12 left-3 z-10 max-w-sm rounded-lg bg-[var(--color-card)] px-3 py-1.5 text-xs text-pretty text-[var(--color-muted)] shadow-md"
        >
          {t('routeFallbackNone')}
        </p>
      ) : null}
      <div
        ref={bindFsRoot}
        className={`route-map-fs-root relative h-full w-full${
          chasing ? 'is-playing' : ''
        }`}
        style={
          chasing
            ? ({
                '--playback-hud-height': `${hudHeight}px`,
              } as CSSProperties)
            : undefined
        }
      >
        <div className="route-map-top-left absolute top-3 left-3 z-10 flex items-center gap-2">
          {selectedActivity && onClearSelection ? (
            <button
              type="button"
              onClick={() => {
                stopChase();
                orbitRef.current.stop();
                setChaseRunId(null);
                onClearSelection();
              }}
              className="flex items-center gap-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-medium shadow-md transition-colors hover:bg-[var(--color-bg)]"
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
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              {t('overview')}
            </button>
          ) : null}
          {canOffer3d ? (
            <button
              type="button"
              className={
                view3d
                  ? 'route-map-toolbar-3d is-active'
                  : 'route-map-toolbar-3d'
              }
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
        <div ref={mapContainerRef} className="h-full w-full" />
        {chasing && playbackSnap ? (
          <PlaybackHudView
            snap={playbackSnap}
            hrSeries={playbackSeries?.hr ?? null}
            timeSeries={playbackSeries?.time ?? null}
            movingTimeSec={
              selectedActivity
                ? parseMovingTime(selectedActivity.moving_time)
                : 0
            }
            averageSpeedMs={selectedActivity?.average_speed ?? 0}
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
            onLockOrientationChange={(locked) =>
              chaseRef.current.setBearingLocked(locked)
            }
            onExport={(opts) => {
              void handleExportVideo(opts);
            }}
            onHeightChange={setHudHeight}
          />
        ) : null}
      </div>
    </div>
  );
}
