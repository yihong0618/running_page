import { FeatureCollection, LineString, Polygon, MultiPolygon } from 'geojson';
import { useEffect, useState } from 'react';

type RPGeometry = LineString | Polygon | MultiPolygon;

export default function useChinaGeoJson() {
  const [geoData, setGeoData] = useState<FeatureCollection<RPGeometry>>();

  useEffect(() => {
    import('@/static/run_countries').then((res) => {
      setGeoData(res.chinaGeojson);
    })
  }, []);

  return geoData;
}
