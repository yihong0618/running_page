import MapboxLanguage from '@mapbox/mapbox-gl-language';
import React, { useRef, useCallback } from 'react';
import ReactMapGL, { Layer, Source, FullscreenControl } from 'react-map-gl';
import useActivities from 'src/hooks/useActivities';
import {
  IS_CHINESE,
  MAIN_COLOR,
  MAPBOX_TOKEN,
  PROVINCE_FILL_COLOR,
  USE_DASH_LINE,
  LINE_OPACITY,
  MAP_HEIGHT,
} from 'src/utils/const';
import { geoJsonForMap } from 'src/utils/utils';
import RunMarker from './RunMaker';
import RunMapButtons from './RunMapButtons';
import styles from './style.module.scss';

const RunMap = ({
  title,
  viewport,
  setViewport,
  changeYear,
  geoData,
  thisYear,
  mapButtonYear,
}) => {
  const { provinces } = useActivities();
  const mapRef = useRef();
  const mapRefCallback = useCallback(
    (ref) => {
      if (ref !== null) {
        mapRef.current = ref;
        const map = ref.getMap();
        if (map && IS_CHINESE) {
          map.addControl(new MapboxLanguage({ defaultLanguage: 'zh-Hans' }));
        }
      }
    },
    [mapRef]
  );
  const filterProvinces = provinces.slice();
  // for geojson format
  filterProvinces.unshift('in', 'name');

  const isBigMap = viewport.zoom <= 3;
  if (isBigMap && IS_CHINESE) {
    geoData = geoJsonForMap();
  }

  const isSingleRun =
    geoData.features.length === 1 &&
    geoData.features[0].geometry.coordinates.length;
  let startLon;
  let startLat;
  let endLon;
  let endLat;
  if (isSingleRun) {
    const points = geoData.features[0].geometry.coordinates;
    [startLon, startLat] = points[0];
    [endLon, endLat] = points[points.length - 1];
  }
  let dash = USE_DASH_LINE && !isSingleRun ? [2, 2] : [2, 0];

  return (
    <ReactMapGL
      {...viewport}
      width='100%'
      height={MAP_HEIGHT}
      mapStyle="mapbox://styles/mapbox/dark-v10"
      onViewportChange={setViewport}
      ref={mapRefCallback}
      mapboxApiAccessToken={MAPBOX_TOKEN}
    >
      <RunMapButtons
        changeYear={changeYear}
        thisYear={thisYear}
        mapButtonYear={mapButtonYear}
      />
      <FullscreenControl className={styles.fullscreenButton} />
      <Source id="data" type="geojson" data={geoData}>
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
      {isSingleRun && (
        <RunMarker
          startLat={startLat}
          startLon={startLon}
          endLat={endLat}
          endLon={endLon}
        />
      )}
      <span className={styles.runTitle}>{title}</span>
    </ReactMapGL>
  );
};

export default RunMap;
