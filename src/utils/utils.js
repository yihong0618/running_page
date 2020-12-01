import * as mapboxPolyline from '@mapbox/polyline';
import { WebMercatorViewport } from 'react-map-gl';
import { chinaGeojson } from '../static/run_countries';
import { MUNICIPALITY_CITIES_ARR, RUN_TITLES } from './const';

const titleForShow = (run) => {
  const date = run.start_date_local.slice(0, 11);
  const distance = (run.distance / 1000.0).toFixed(1);
  let name = 'Run';
  if (run.name.slice(0, 7) === 'Running') {
    name = 'run';
  }
  if (run.name) {
    name = run.name;
  }
  return `${name} ${date} ${distance} KM ${!run.summary_polyline ? '(No map data for this run)' : ''}`;
};

const formatPace = (d) => {
  if (Number.isNaN(d)) return '0';
  const pace = (1000.0 / 60.0) * (1.0 / d);
  const minutes = Math.floor(pace);
  const seconds = Math.floor((pace - minutes) * 60.0);
  return `${minutes}:${seconds.toFixed(0).toString().padStart(2, '0')}`;
};

// for scroll to the map
const scrollToMap = () => {
  const el = document.querySelector('.fl.w-100.w-70-l');
  const rect = el.getBoundingClientRect();
  window.scroll(rect.left + window.scrollX, rect.top + window.scrollY);
};

// what about oversea?
const locationForRun = (run) => {
  const location = run.location_country;
  let [city, province, country] = ['', '', ''];
  if (location) {
    // Only for Chinese now
    const cityMatch = location.match(/[\u4e00-\u9fa5]*(市|自治州)/);
    const provinceMatch = location.match(/[\u4e00-\u9fa5]*(省|自治区)/);
    if (cityMatch) {
      [city] = cityMatch;
    }
    if (provinceMatch) {
      [province] = provinceMatch;
    }
    const l = location.split(',');
    // or to handle keep location format
    let countryMatch = l[l.length - 1].match(/[\u4e00-\u9fa5].*[\u4e00-\u9fa5]/);
    if (!countryMatch && l.length >= 3) {
      countryMatch = l[2].match(/[\u4e00-\u9fa5].*[\u4e00-\u9fa5]/);
    }
    if (countryMatch) {
      [country] = countryMatch;
    }
  }
  if (MUNICIPALITY_CITIES_ARR.includes(city)) {
    province = city;
  }

  return { country, province, city };
};

const intComma = (x = '') => x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');

const pathForRun = (run) => {
  try {
    const c = mapboxPolyline.decode(run.summary_polyline);
    // reverse lat long for mapbox
    c.forEach((arr) => {
      [arr[0], arr[1]] = [arr[1], arr[0]];
    });
    return c;
  } catch (err) {
    return [];
  }
};

const geoJsonForRuns = (runs) => ({
  type: 'FeatureCollection',
  features: runs.map((run) => {
    const points = pathForRun(run);
    if (!points) {
      return null;
    }

    return {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: points,
      },
    };
  }),
});

const geoJsonForMap = () => chinaGeojson;

const titleForRun = (run) => {
  const runDistance = run.distance / 1000;
  const runHour = +run.start_date_local.slice(11, 13);
  if (runDistance > 20 && runDistance < 40) {
    return RUN_TITLES.HALF_MARATHON_RUN_TITLE;
  }
  if (runDistance >= 40) {
    return RUN_TITLES.FULL_MARATHON_RUN_TITLE;
  }
  if (runHour >= 0 && runHour <= 8) {
    return RUN_TITLES.MORNING_RUN_TITLE;
  }
  if (runHour > 8 && runHour <= 12) {
    return RUN_TITLES.LUNCH_RUN_TITLE;
  }
  if (runHour > 12 && runHour <= 18) {
    return RUN_TITLES.AFTERNOON_RUN_TITLE;
  }
  if (runHour > 18 && runHour <= 21) {
    return RUN_TITLES.EVENING_RUN_TITLE;
  }
  return RUN_TITLES.NIGHT_RUN_TITLE;
};

const applyToArray = (func, array) => func.apply(Math, array);
const getBoundsForGeoData = (geoData) => {
  const { features } = geoData;
  let points;
  // find first have data
  for (const f of features) {
    if (f.geometry.coordinates.length) {
      points = f.geometry.coordinates;
      break;
    }
  }
  if (!points) {
    return {};
  }
  // Calculate corner values of bounds
  const pointsLong = points.map((point) => point[0]);
  const pointsLat = points.map((point) => point[1]);
  const cornersLongLat = [
    [applyToArray(Math.min, pointsLong), applyToArray(Math.min, pointsLat)],
    [applyToArray(Math.max, pointsLong), applyToArray(Math.max, pointsLat)],
  ];
  const viewport = new WebMercatorViewport({ width: 800, height: 600 })
    .fitBounds(cornersLongLat, { padding: 200 });
  let { longitude, latitude, zoom } = viewport;
  if (features.length > 1) {
    zoom = 11.5;
  }
  return { longitude, latitude, zoom };
};

const filterYearRuns = ((run, year) => run.start_date_local.slice(0, 4) === year);
const filterAndSortRuns = (activities, year, sortFunc) => {
  let s = activities;
  if (year !== 'Total') {
    s = activities.filter((run) => filterYearRuns(run, year));
  }
  return s.sort(sortFunc);
};

const sortDateFunc = (a, b) => new Date(b.start_date_local.replace(' ', 'T')) - new Date(a.start_date_local.replace(' ', 'T'));
const sortDateFuncReverse = (a, b) => sortDateFunc(b, a);

export {
  titleForShow, formatPace, scrollToMap, locationForRun, intComma, pathForRun, geoJsonForRuns, geoJsonForMap, titleForRun, filterYearRuns, filterAndSortRuns, sortDateFunc, sortDateFuncReverse, getBoundsForGeoData,
};
