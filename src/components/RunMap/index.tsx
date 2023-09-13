import MapboxLanguage from '@mapbox/mapbox-gl-language';
import React, { useRef, useCallback, useMemo } from 'react';
import ReactMapGL, {
  Layer,
  Source,
  FullscreenControl,
  MapRef,
} from 'react-map-gl';
import useActivities from '@/hooks/useActivities';
import {
  MAP_LAYER_LIST,
  IS_CHINESE,
  ROAD_LABEL_DISPLAY,
  MAIN_COLOR,
  MAPBOX_TOKEN,
  PROVINCE_FILL_COLOR,
  USE_DASH_LINE,
  LINE_OPACITY,
  MAP_HEIGHT,
} from '@/utils/const';
import { Coordinate, IViewport } from '@/utils/utils';
import RunMarker from './RunMaker';
import RunMapButtons from './RunMapButtons';
import styles from './style.module.scss';
import { FeatureCollection } from 'geojson';
import { RPGeometry } from '@/static/run_countries';
import useChinaGeoJson from '@/hooks/useChinaGeo';
import Loading from '../Loading';

interface IRunMapProps {
  title: string;
  viewport: IViewport;
  setViewport: (_viewport: IViewport) => void;
  changeYear: (_year: string) => void;
  geoData: FeatureCollection<RPGeometry>;
  thisYear: string;
}

const RunMap = ({
  title,
  viewport,
  setViewport,
  changeYear,
  geoData,
  thisYear,
}: IRunMapProps) => {
  const [{ provinces }, loading] = useActivities();
  const mapRef = useRef<MapRef>();
  const mapRefCallback = useCallback(
    (ref: MapRef) => {
      if (ref !== null) {
        mapRef.current = ref;
        const map = ref.getMap();
        if (map && IS_CHINESE) {
          map.addControl(new MapboxLanguage({ defaultLanguage: 'zh-Hans' }));
          if (!ROAD_LABEL_DISPLAY) {
            // todo delete layers
            map.on('load', () => {
              MAP_LAYER_LIST.forEach((layerId) => {
                map.removeLayer(layerId);
              });
            });
          }
        }
      }
    },
    [mapRef]
  );
  const filterProvinces = provinces.slice();
  // for geojson format
  filterProvinces.unshift('in', 'name');

  const isBigMap = (viewport.zoom ?? 0) <= 3;
  const chinaGeo = useChinaGeoJson();

  const geoDataForMap = useMemo(() => {
    return isBigMap && IS_CHINESE ? chinaGeo : geoData;
  }, [isBigMap, chinaGeo, geoData]);

  const isSingleRun = useMemo(() => {
    return (
      geoDataForMap?.features.length === 1 &&
      geoDataForMap?.features[0].geometry.coordinates.length
    );
  }, [geoDataForMap]);

  const markerGeo = useMemo(() => {
    let startLon = 0;
    let startLat = 0;
    let endLon = 0;
    let endLat = 0;
    if (isSingleRun) {
      const points = geoDataForMap?.features[0].geometry.coordinates as (Coordinate[] | undefined);
      if (typeof points !== 'undefined') {
        [startLon, startLat] = points[0];
        [endLon, endLat] = points[points.length - 1];
      }
    }
    return { startLon, startLat, endLon, endLat };
  }, [geoDataForMap, isSingleRun]);

  let dash = USE_DASH_LINE && !isSingleRun ? [2, 2] : [2, 0];

  return (
    loading ? <Loading /> : <ReactMapGL
      {...viewport}
      width="100%"
      height={MAP_HEIGHT}
      mapStyle="mapbox://styles/mapbox/dark-v10"
      onViewportChange={setViewport}
      ref={mapRefCallback}
      mapboxApiAccessToken={MAPBOX_TOKEN}
    >
      <RunMapButtons changeYear={changeYear} thisYear={thisYear} />
      <FullscreenControl className={styles.fullscreenButton} />
      <Source id="data" type="geojson" data={geoDataForMap}>
        <Layer
          id="province"
          type="fill"
          paint={{
            'fill-color': PROVINCE_FILL_COLOR,
          }}
          filter={filterProvinces}
        />
        <Layer
          id="runs2"
          type="line"
          paint={{
            'line-color': MAIN_COLOR,
            'line-width': isBigMap ? 1 : 2,
            'line-dasharray': dash,
            'line-opacity': isSingleRun ? 1 : LINE_OPACITY,
          }}
          layout={{
            'line-join': 'round',
            'line-cap': 'round',
          }}
        />
      </Source>
      {isSingleRun && <RunMarker {...markerGeo} />}
      <span className={styles.runTitle}>{title}</span>
    </ReactMapGL>
  );
};

export default RunMap;
