import MapboxLanguage from '@mapbox/mapbox-gl-language';
import React, {
  useRef,
  useCallback,
  useState,
  useEffect,
  useMemo,
} from 'react';
import Map, {
  Layer,
  Source,
  FullscreenControl,
  NavigationControl,
  MapRef,
} from 'react-map-gl';
import { MapInstance } from 'react-map-gl/src/types/lib';
import useActivities from '@/hooks/useActivities';
import {
  IS_CHINESE,
  ROAD_LABEL_DISPLAY,
  MAPBOX_TOKEN,
  PROVINCE_FILL_COLOR,
  COUNTRY_FILL_COLOR,
  USE_DASH_LINE,
  LINE_OPACITY,
  MAP_HEIGHT,
  PRIVACY_MODE,
  LIGHTS_ON,
  MAP_TILE_VENDOR,
  MAP_TILE_ACCESS_TOKEN,
  getRuntimeSingleRunColor,
} from '@/utils/const';
import {
  Coordinate,
  IViewState,
  geoJsonForMap,
  getMapStyle,
  isTouchDevice,
} from '@/utils/utils';
import { RouteAnimator } from '@/utils/routeAnimation';
import RunMarker from './RunMarker';
import RunMapButtons from './RunMapButtons';
import styles from './style.module.css';
import { FeatureCollection } from 'geojson';
import { RPGeometry } from '@/static/run_countries';
import './mapbox.css';
import LightsControl from '@/components/RunMap/LightsControl';
import { useMapTheme, useThemeChangeCounter } from '@/hooks/useTheme';

interface IRunMapProps {
  title: string;
  viewState: IViewState;
  setViewState: (_viewState: IViewState) => void;
  changeYear: (_year: string) => void;
  geoData: FeatureCollection<RPGeometry>;
  thisYear: string;
  animationTrigger?: number; // Optional trigger to force animation replay
}

const RunMap = ({
  title,
  viewState,
  setViewState,
  changeYear,
  geoData,
  thisYear,
  animationTrigger,
}: IRunMapProps) => {
  const { countries, provinces } = useActivities();
  const mapRef = useRef<MapRef>(null);
  const [lights, setLights] = useState(PRIVACY_MODE ? false : LIGHTS_ON);
  // layers that should remain visible when lights are off
  const keepWhenLightsOff = ['runs2', 'animated-run'];
  const [mapGeoData, setMapGeoData] =
    useState<FeatureCollection<RPGeometry> | null>(null);
  const [isLoadingMapData, setIsLoadingMapData] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Use the map theme hook to get the current map theme
  const currentMapTheme = useMapTheme();
  // Listen for theme changes to update single run color
  const themeChangeCounter = useThemeChangeCounter();

  // Get theme-aware single run color that updates when theme changes
  const singleRunColor = useMemo(
    () => getRuntimeSingleRunColor(),
    [themeChangeCounter]
  );

  // Generate map style based on current theme
  const mapStyle = useMemo(
    () => getMapStyle(MAP_TILE_VENDOR, currentMapTheme, MAP_TILE_ACCESS_TOKEN),
    [currentMapTheme]
  );

  // Mapbox GL JS requires a token even when using other vendors
  // Use actual MAPBOX_TOKEN when vendor is 'mapbox', otherwise use a dummy token
  const mapboxAccessToken = useMemo(() => {
    if (MAP_TILE_VENDOR === 'mapbox') {
      return MAPBOX_TOKEN;
    }
    // Use a dummy token for other vendors (Mapbox GL JS still requires a token)
    // This is a valid format but won't be used for actual mapbox requests
    return 'pk.eyJ1IjoidW5rbm93biIsImEiOiJjbGZqY2N0d3EwMGNsM3BwN2N4d2N4d2N4In0.unknown';
  }, []);

  // Update map when theme changes
  useEffect(() => {
    if (mapRef.current) {
      const map = mapRef.current.getMap();

      // Save current map state before changing style
      const currentCenter = map.getCenter();
      const currentZoom = map.getZoom();
      const currentBearing = map.getBearing();
      const currentPitch = map.getPitch();

      // Apply new style
      map.setStyle(mapStyle);

      // Create a stable handler for style.load to ensure proper cleanup
      const handleStyleLoad = () => {
        // Add a small delay to ensure style is fully loaded
        setTimeout(() => {
          try {
            // Restore map view state
            map.setCenter(currentCenter);
            map.setZoom(currentZoom);
            map.setBearing(currentBearing);
            map.setPitch(currentPitch);

            // Reapply layer visibility settings with current lights state
            switchLayerVisibility(map, lights);
          } catch (error) {
            console.warn('Error applying map style changes:', error);
          }
        }, 100);
      };

      // Use once to automatically remove the listener after it fires
      map.once('style.load', handleStyleLoad);
    }
  }, [mapStyle]); // Keep only mapStyle in dependency to prevent excessive re-renders

  useEffect(() => {
    if (mapRef.current) {
      const map = mapRef.current.getMap();

      // Track tile loading errors
      let tileErrorCount = 0;
      const MAX_TILE_ERRORS = 10;

      const handleStyleError = (e: any) => {
        console.error('❌ Map style failed to load:', e);
        setMapError(
          'Map tiles failed to load. Please check your internet connection.'
        );

        if (MAP_TILE_VENDOR === 'mapcn') {
          console.warn('⚠️ Carto Basemaps (MapCN) failed to load.');
          console.info('💡 Possible solutions:');
          console.info('   1. Check your internet connection');
          console.info(
            '   2. If in China, Carto may be blocked.  Try fallback:'
          );
          console.info('      - Change MAP_TILE_VENDOR to "mapcn_openfreemap"');
          console.info(
            '      - Or use MAP_TILE_VENDOR = "maptiler" with free token'
          );
        }
      };

      const handleTileError = () => {
        tileErrorCount++;

        if (tileErrorCount === MAX_TILE_ERRORS) {
          console.error(`❌ ${MAX_TILE_ERRORS}+ tile loading errors detected`);
          console.warn('⚠️ Map tiles are not loading properly.');
          console.info(
            '💡 Try switching to a different provider in src/utils/const.ts'
          );
        }
      };

      map.on('error', handleStyleError);
      map.on('tileerror', handleTileError);

      // Cleanup
      return () => {
        map.off('error', handleStyleError);
        map.off('tileerror', handleTileError);
      };
    }
  }, [mapRef]);

  // animation state (single run only)
  const [animatedPoints, setAnimatedPoints] = useState<Coordinate[]>([]);
  const routeAnimatorRef = useRef<RouteAnimator | null>(null);
  const lastRouteKeyRef = useRef<string | null>(null);

  // Memoize filter arrays to prevent recreating them on every render
  const filterProvinces = useMemo(() => {
    const filtered = provinces.slice();
    filtered.unshift('in', 'name');
    return filtered;
  }, [provinces]);

  const filterCountries = useMemo(() => {
    const filtered = countries.slice();
    filtered.unshift('in', 'name');
    return filtered;
  }, [countries]);

  /**
   * Toggle visibility of map layers based on lights setting
   * @param map - The Mapbox map instance
   * @param lights - Whether lights are on or off
   */
  function switchLayerVisibility(map: MapInstance, lights: boolean) {
    const styleJson = map.getStyle();
    styleJson.layers.forEach((it: { id: string }) => {
      if (!keepWhenLightsOff.includes(it.id)) {
        if (lights) map.setLayoutProperty(it.id, 'visibility', 'visible');
        else map.setLayoutProperty(it.id, 'visibility', 'none');
      }
    });
  }

  // Apply layer visibility when lights setting changes
  useEffect(() => {
    if (mapRef.current) {
      const map = mapRef.current.getMap();
      // Add a small delay to ensure map is ready
      setTimeout(() => {
        try {
          switchLayerVisibility(map, lights);
        } catch (error) {
          console.warn('Error switching layer visibility:', error);
        }
      }, 50);
    }
  }, [lights]);

  const mapRefCallback = useCallback(
    (ref: MapRef) => {
      if (ref !== null) {
        const map = ref.getMap();
        if (map && IS_CHINESE) {
          map.addControl(new MapboxLanguage({ defaultLanguage: 'zh-Hans' }));
        }
        // all style resources have been downloaded
        // and the first visually complete rendering of the base style has occurred.
        // it's odd. when use style other than mapbox, the style.load event is not triggered.Add commentMore actions
        // so I use data event instead of style.load event and make sure we handle it only once.
        map.on('data', (event) => {
          if (event.dataType !== 'style' || mapRef.current) {
            return;
          }
          if (!ROAD_LABEL_DISPLAY) {
            const layers = map.getStyle().layers;
            const labelLayerNames = layers
              .filter(
                (layer: any) =>
                  (layer.type === 'symbol' || layer.type === 'composite') &&
                  layer.layout.text_field !== null
              )
              .map((layer: any) => layer.id);
            labelLayerNames.forEach((layerId) => {
              map.removeLayer(layerId);
            });
          }
          mapRef.current = ref;
          switchLayerVisibility(map, lights);
        });
      }
      if (mapRef.current) {
        const map = mapRef.current.getMap();
        switchLayerVisibility(map, lights);
      }
    },
    [mapRef, lights]
  );

  const initGeoDataLength = geoData.features.length;
  const isBigMap = (viewState.zoom ?? 0) <= 3;

  useEffect(() => {
    if (isBigMap && IS_CHINESE && !mapGeoData && !isLoadingMapData) {
      setIsLoadingMapData(true);
      geoJsonForMap()
        .then((data) => {
          setMapGeoData(data);
          setIsLoadingMapData(false);
        })
        .catch(() => {
          setIsLoadingMapData(false);
        });
    }
  }, [isBigMap, IS_CHINESE, mapGeoData, isLoadingMapData]);

  let combinedGeoData = geoData;
  if (isBigMap && IS_CHINESE && mapGeoData) {
    // Show boundary and line together, combine geoData(only when not combine yet)
    if (geoData.features.length === initGeoDataLength) {
      combinedGeoData = {
        type: 'FeatureCollection',
        features: geoData.features.concat(mapGeoData.features),
      };
    }
  }

  // Memoize expensive calculations
  const { isSingleRun, startLon, startLat, endLon, endLat } = useMemo(() => {
    const isSingle =
      geoData.features.length === 1 &&
      geoData.features[0].geometry.coordinates.length;

    let startLon = 0;
    let startLat = 0;
    let endLon = 0;
    let endLat = 0;

    if (isSingle) {
      const points = geoData.features[0].geometry.coordinates as Coordinate[];
      [startLon, startLat] = points[0];
      [endLon, endLat] = points[points.length - 1];
    }

    return { isSingleRun: isSingle, startLon, startLat, endLon, endLat };
  }, [geoData]);

  const dash = useMemo(() => {
    return USE_DASH_LINE && !isSingleRun && !isBigMap ? [2, 2] : [2, 0];
  }, [isSingleRun, isBigMap]);

  const onMove = useCallback(
    ({ viewState }: { viewState: IViewState }) => {
      setViewState(viewState);
    },
    [setViewState]
  );

  const style: React.CSSProperties = useMemo(
    () => ({
      width: '100%',
      height: MAP_HEIGHT,
      maxWidth: '100%', // Prevent overflow on mobile
    }),
    []
  );

  const fullscreenButton: React.CSSProperties = useMemo(
    () => ({
      position: 'absolute',
      marginTop: '29.2px',
      right: '0px',
      opacity: 0.3,
    }),
    []
  );

  useEffect(() => {
    const handleFullscreenChange = () => {
      if (mapRef.current) {
        mapRef.current.getMap().resize();
      }
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // start route animation using RouteAnimator
  const startRouteAnimation = useCallback(() => {
    if (!isSingleRun) return;
    const points = geoData.features[0].geometry.coordinates as Coordinate[];
    if (!points || points.length < 2) return;

    // Stop any existing animation
    if (routeAnimatorRef.current) {
      routeAnimatorRef.current.stop();
    }

    // Create new animator
    routeAnimatorRef.current = new RouteAnimator(
      points,
      setAnimatedPoints,
      () => {
        routeAnimatorRef.current = null;
      }
    );

    // Start animation
    routeAnimatorRef.current.start();
  }, [geoData, isSingleRun]);

  // autoplay once when single run changes
  useEffect(() => {
    if (!isSingleRun) return;
    const pts = geoData.features[0].geometry.coordinates as Coordinate[];
    const key = `${pts.length}-${pts[0]?.join(',')}-${pts[pts.length - 1]?.join(',')}`;
    if (key && key !== lastRouteKeyRef.current) {
      lastRouteKeyRef.current = key;
      startRouteAnimation();
    }
    // cleanup on unmount
    return () => {
      if (routeAnimatorRef.current) {
        routeAnimatorRef.current.stop();
      }
    };
  }, [geoData, isSingleRun, startRouteAnimation]);

  // Force animation when animationTrigger changes (for table clicks)
  useEffect(() => {
    if (animationTrigger && animationTrigger > 0 && isSingleRun) {
      startRouteAnimation();
    }
  }, [animationTrigger, isSingleRun, startRouteAnimation]);

  const handleMapClick = useCallback(() => {
    if (!isSingleRun) return;
    startRouteAnimation();
  }, [isSingleRun, startRouteAnimation]);

  return (
    <Map
      {...viewState}
      onMove={onMove}
      onClick={handleMapClick}
      style={style}
      mapStyle={mapStyle}
      ref={mapRefCallback}
      cooperativeGestures={isTouchDevice()}
      mapboxAccessToken={mapboxAccessToken}
    >
      {mapError && (
        <div className={styles.mapErrorNotification}>
          <span>⚠️ {mapError}</span>
          <button onClick={() => window.location.reload()}>Reload Page</button>
          <a
            href="https://github.com/yihong0618/running_page#map-tiles-customization"
            target="_blank"
            rel="noopener noreferrer"
          >
            Troubleshooting Guide
          </a>
        </div>
      )}
      <RunMapButtons changeYear={changeYear} thisYear={thisYear} />
      <Source id="data" type="geojson" data={combinedGeoData}>
        <Layer
          id="province"
          type="fill"
          paint={{
            'fill-color': PROVINCE_FILL_COLOR,
          }}
          filter={filterProvinces}
        />
        <Layer
          id="countries"
          type="fill"
          paint={{
            'fill-color': COUNTRY_FILL_COLOR,
            // in China, fill a bit lighter while already filled provinces
            'fill-opacity': ['case', ['==', ['get', 'name'], '中国'], 0.1, 0.5],
          }}
          filter={filterCountries}
        />
        <Layer
          id="runs2"
          type="line"
          paint={{
            'line-color': ['get', 'color'],
            'line-width': isBigMap && lights ? 1 : 2,
            'line-dasharray': dash,
            'line-opacity':
              isSingleRun || isBigMap || !lights ? 1 : LINE_OPACITY,
            'line-blur': 1,
          }}
          layout={{
            'line-join': 'round',
            'line-cap': 'round',
          }}
        />
      </Source>
      {isSingleRun && animatedPoints.length > 0 && (
        <Source
          id="animated-run"
          type="geojson"
          data={{
            type: 'FeatureCollection',
            features: [
              {
                type: 'Feature',
                properties: { color: singleRunColor },
                geometry: {
                  type: 'LineString',
                  coordinates: animatedPoints,
                },
              },
            ],
          }}
        >
          <Layer
            id="animated-run"
            type="line"
            paint={{
              'line-color': ['get', 'color'],
              'line-width': 3,
              'line-opacity': 1,
            }}
            layout={{
              'line-join': 'round',
              'line-cap': 'round',
            }}
          />
        </Source>
      )}
      {isSingleRun && (
        <RunMarker
          startLat={startLat}
          startLon={startLon}
          endLat={endLat}
          endLon={endLon}
        />
      )}
      <span className={styles.runTitle}>{title}</span>
      <FullscreenControl style={fullscreenButton} />
      {!PRIVACY_MODE && <LightsControl setLights={setLights} lights={lights} />}
      <NavigationControl
        showCompass={false}
        position={'bottom-right'}
        style={{ opacity: 0.3 }}
      />
    </Map>
  );
};

export default RunMap;
