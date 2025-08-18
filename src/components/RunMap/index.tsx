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
  MAP_TILE_STYLE,
  MAP_TILE_VENDOR,
  MAP_TILE_ACCESS_TOKEN,
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
  const mapRef = useRef<MapRef>();
  const [lights, setLights] = useState(PRIVACY_MODE ? false : LIGHTS_ON);
  // layers that should remain visible when lights are off
  const keepWhenLightsOff = ['runs2', 'animated-run'];
  const [mapGeoData, setMapGeoData] =
    useState<FeatureCollection<RPGeometry> | null>(null);
  const [isLoadingMapData, setIsLoadingMapData] = useState(false);

  // Memoize map style to prevent recreating it on every render
  const mapStyle = useMemo(
    () => getMapStyle(MAP_TILE_VENDOR, MAP_TILE_STYLE, MAP_TILE_ACCESS_TOKEN),
    []
  );

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

  function switchLayerVisibility(map: MapInstance, lights: boolean) {
    const styleJson = map.getStyle();
    styleJson.layers.forEach((it: { id: string }) => {
      if (!keepWhenLightsOff.includes(it.id)) {
        if (lights) map.setLayoutProperty(it.id, 'visibility', 'visible');
        else map.setLayoutProperty(it.id, 'visibility', 'none');
      }
    });
  }
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
      mapboxAccessToken={MAPBOX_TOKEN}
    >
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
                properties: { color: '#ff4d4f' },
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
