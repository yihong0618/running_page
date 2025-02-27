import MapboxLanguage from '@mapbox/mapbox-gl-language';
import React, {useRef, useCallback, useState, useEffect} from 'react';
import Map, {Layer, Source, FullscreenControl, NavigationControl, MapRef} from 'react-map-gl';
import {MapInstance} from "react-map-gl/src/types/lib";
import useActivities from '@/hooks/useActivities';
import {
  MAP_LAYER_LIST,
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
} from '@/utils/const';
import { Coordinate, IViewState, geoJsonForMap,RunIds,Activity } from '@/utils/utils';
import RunMarker from './RunMarker';
import RunMapButtons from './RunMapButtons';
import styles from './style.module.css';
import { FeatureCollection } from 'geojson';
import { RPGeometry } from '@/static/run_countries';
import './mapbox.css';
import LightsControl from "@/components/RunMap/LightsControl";

interface IRunMapProps {
  title: string;
  viewState: IViewState;
  setViewState: (_viewState: IViewState) => void;
  changeYear: (_year: string) => void;
  geoData: FeatureCollection<RPGeometry>;
  thisYear: string;
  selectedRunIds: RunIds;
  
}

const RunMap = ({
  title,
  viewState,
  setViewState,
  changeYear,
  geoData,
  thisYear,
  selectedRunIds,
 
}: IRunMapProps) => {
  const { countries, provinces } = useActivities();
  const mapRef = useRef<MapRef>();
  const [lights, setLights] = useState(PRIVACY_MODE ? false : LIGHTS_ON);
  const keepWhenLightsOff = ['runs2']
  function switchLayerVisibility(map: MapInstance, lights: boolean) {
    const styleJson = map.getStyle();
    styleJson.layers.forEach((it: { id: string; }) => {
      if (!keepWhenLightsOff.includes(it.id)) {
        if (lights)
          map.setLayoutProperty(it.id, 'visibility', 'visible');
        else
          map.setLayoutProperty(it.id, 'visibility', 'none');
      }
    })
  }
  const mapRefCallback = useCallback(
    (ref: MapRef) => {
      if (ref !== null) {
        const map = ref.getMap();
        if (map && IS_CHINESE) {
            map.addControl(new MapboxLanguage({defaultLanguage: 'zh-Hans'}));
        }
        // all style resources have been downloaded
        // and the first visually complete rendering of the base style has occurred.
        map.on('style.load', () => {
          if (!ROAD_LABEL_DISPLAY) {
            MAP_LAYER_LIST.forEach((layerId) => {
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
  const filterProvinces = provinces.slice();
  const filterCountries = countries.slice();
  // for geojson format
  filterProvinces.unshift('in', 'name');
  filterCountries.unshift('in', 'name');

  const initGeoDataLength = geoData.features.length;
  const isBigMap = (viewState.zoom ?? 0) <= 5;
  if (isBigMap && IS_CHINESE) {
    // Show boundary and line together, combine geoData(only when not combine yet)
    if(geoData.features.length === initGeoDataLength){
      geoData = {
          "type": "FeatureCollection",
          "features": geoData.features.concat(geoJsonForMap().features)
      };
    }
  }

  // const isSingleRun =
  //   geoData.features.length === 1 &&
  //   geoData.features[0].geometry.coordinates.length;
  // 替换原有 isSingleRun 逻辑
const isSingleRun = selectedRunIds.length === 1;
  let startLon = 0;
  let startLat = 0;
  let endLon = 0;
  let endLat = 0;

  if (isSingleRun) {
    // 从所有轨迹中查找选中轨迹
    // 👇 直接从 geoData 查找选中轨迹
    // const selectedFeature = geoData.features.find(f => 
    //   f.properties?.run_id === selectedRunIds[0]
    // );
    const selectedFeature = geoData.features.find(f => 
      f.properties?.isSelected // 👈 直接使用已生成的选中标记
    );

    if (selectedFeature?.geometry?.coordinates) {
      const points = selectedFeature.geometry.coordinates as Coordinate[];
      [startLon, startLat] = points[0];
      [endLon, endLat] = points[points.length - 1];
    }

  // if (isSingleRun) {
  //   const points = geoData.features[0].geometry.coordinates as Coordinate[];
    // [startLon, startLat] = points[0];
    // [endLon, endLat] = points[points.length - 1];
  }
  let dash = USE_DASH_LINE && !isSingleRun && !isBigMap ? [2, 2] : [2, 0];
  const onMove = React.useCallback(({ viewState }: { viewState: IViewState }) => {
    setViewState(viewState);
  }, []);
  const style: React.CSSProperties = {
    width: '100%',
    height: MAP_HEIGHT,
  };
  const fullscreenButton: React.CSSProperties = {
    position: 'absolute',
    marginTop: '29.2px',
    right: '0px',
    opacity: 0.3,
  };

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

  return (
    <Map
      {...viewState}
      onMove={onMove}
      style={style}
      mapStyle="mapbox://styles/mapbox/light-v10"
      ref={mapRefCallback}
      mapboxAccessToken={MAPBOX_TOKEN}
    >
      <RunMapButtons changeYear={changeYear} thisYear={thisYear} />
      <Source id="data" type="geojson" data={geoData}>
        <Layer
          id="province"
          type="fill"
          paint={{
            'fill-color': PROVINCE_FILL_COLOR,
            'fill-opacity': 0.8,
          }}
          filter={filterProvinces}
        />
        <Layer
          id="countries"
          type="fill"
          paint={{
            'fill-color': COUNTRY_FILL_COLOR,
            // in China, fill a bit lighter while already filled provinces
            'fill-opacity': ["case", ["==", ["get", "name"], '中国'], 0.2, 0.8],
          }}
          filter={filterCountries}
        />
        <Layer
          id="runs2"
          type="line"
          paint={{
            'line-color': [
              'case',
              ['get', 'isSelected'], // 👈 根据选中状态
              '#ff0000', // 选中颜色
              ['get', 'color'] // 默认颜色
            ],
            'line-width': [
              'case',
              ['get', 'isSelected'], 
              4, // 选中加粗
              (isBigMap && lights) ? 1 : 2 // 默认
            ],
            'line-dasharray': dash,
            'line-opacity': [
              'case',
              ['get', 'isSelected'],
              1, // 选中不透明
              0.3 // 非选中半透明
            ],
            'line-blur': 1,
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
      <FullscreenControl style={fullscreenButton}/>
      {!PRIVACY_MODE && <LightsControl setLights={setLights} lights={lights}/>}
      <NavigationControl showCompass={true} position={'bottom-right'} style={{opacity: 0.9}}/>
      {/* {console.log('实时 isSingleRun:', isSingleRun)}; */}
      {/* {console.log('当前选中ID数量:', selectedRunIds.length)};
      {console.log('geoData 轨迹数量:', geoData.features.length)}; */}
    </Map>
    
  );
};

export default RunMap;
