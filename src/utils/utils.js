import * as mapboxPolyline from '@mapbox/polyline';
import gcoord from 'gcoord';
import { WebMercatorViewport } from 'react-map-gl'
import { chinaGeojson } from '../static/run_countries';
import { chinaCities } from '../static/city';
import {
  MUNICIPALITY_CITIES_ARR,
  NEED_FIX_MAP,
  RUN_TITLES,
  MAIN_COLOR,
  RIDE_COLOR,
  VIRTUAL_RIDE_COLOR,
  HIKE_COLOR,
  SWIM_COLOR,
  ROWING_COLOR,
  ROAD_TRIP_COLOR,
  FLIGHT_COLOR,
  RUN_COLOR,
  KAYAKING_COLOR,
  SNOWBOARD_COLOR,
} from './const';

const titleForShow = (run) => {
  const date = run.start_date_local.slice(0, 11);
  const distance = (run.distance / 1000.0).toFixed(1);
  let name = 'Run';
  if (run.name) {
    name = run.name;
  }
  return `${name} ${date} ${distance} KM ${
    !run.summary_polyline ? '(No map data for this workout)' : ''
  }`;
};

const formatPace = (d) => {
  if (Number.isNaN(d) || d == 0) return '0';
  const pace = (1000.0 / 60.0) * (1.0 / d);
  const minutes = Math.floor(pace);
  const seconds = Math.floor((pace - minutes) * 60.0);
  return `${minutes}'${seconds.toFixed(0).toString().padStart(2, '0')}"`;
};

const convertMovingTime2Sec = (moving_time) => {
  if (!moving_time) {
    return 0;
  }
  // moving_time : '2 days, 12:34:56' or '12:34:56';
  const splits = moving_time.split(', ');
  const days = splits.length == 2 ? parseInt(splits[0]) : 0;
  const time = splits.splice(-1)[0]
  const [hours, minutes, seconds] = time.split(':').map(Number);
  const totalSeconds = (((days * 24) + hours) * 60 + minutes) * 60 + seconds;
  return totalSeconds;
}

const formatRunTime = (moving_time) => {
  const totalSeconds = convertMovingTime2Sec(moving_time)
  const seconds = totalSeconds % 60
  const minutes = (totalSeconds-seconds) / 60
  if (minutes === 0) {
    return seconds + 's';
  }
  return minutes + 'min';
};

// for scroll to the map
const scrollToMap = () => {
  const el = document.querySelector('.fl.w-100.w-70-l');
  const rect = el.getBoundingClientRect();
  window.scroll(rect.left + window.scrollX, rect.top + window.scrollY);
};

const cities = chinaCities.map((c) => c.name);
// what about oversea?
const locationForRun = (run) => {
  let location = run.location_country;
  let [city, province, country] = ['', '', ''];
  if (location) {
    // Only for Chinese now
    // should fiter 臺灣
    if(location.indexOf('臺灣') > -1){
      const taiwan = '台湾';
      location = location.replace('臺灣', taiwan);
      const _locArr = location.split(',').map(item=>item.trim());
      const _locArrLen = _locArr.length;
      // directly repalce last item with 中国
      _locArr[_locArrLen-1] = '中国';
      // if location not contain '台湾省', insert it before zip code(posistion is _locArrLen-2)
      if(_locArr.indexOf(`${taiwan}省`) === -1){
        _locArr.splice(_locArrLen-2, 0, `${taiwan}省`)
      }
      location = _locArr.join(',');
    }
    const cityMatch = location.match(/[\u4e00-\u9fa5]{2,}(市|自治州)/);
    const provinceMatch = location.match(/[\u4e00-\u9fa5]{2,}(省|自治区)/);
    if (cityMatch) {
      [city] = cityMatch;
      if (!cities.includes(city)) {
        city = ''
      }
    }
    if (provinceMatch) {
      [province] = provinceMatch;
    }
    const l = location.split(',');
    // or to handle keep location format
    let countryMatch = l[l.length - 1].match(
      /[\u4e00-\u9fa5].*[\u4e00-\u9fa5]/
    );
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

const intComma = (x = '') => {
  if (x.toString().length <= 5) {
    return x;
  }
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

const pathForRun = (run) => {
  try {
    const c = mapboxPolyline.decode(run.summary_polyline);
    // reverse lat long for mapbox
    c.forEach((arr) => {
      [arr[0], arr[1]] = !NEED_FIX_MAP ? [arr[1], arr[0]] : gcoord.transform([arr[1], arr[0]], gcoord.GCJ02, gcoord.WGS84);
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
        workoutType: run.type,
      },
      properties: {
        'color': colorFromType(run.type),
      },
      name: run.name,
    };
  }),
});

const geoJsonForMap = () => chinaGeojson;

const titleForType = (type) => {
  switch (type) {
    case 'Run':
      return RUN_TITLES.RUN_TITLE;
    case 'Ride':
      return RUN_TITLES.RIDE_TITLE;
    case 'Indoor Ride':
      return RUN_TITLES.INDOOR_RIDE_TITLE;
    case 'VirtualRide':
      return RUN_TITLES.VIRTUAL_RIDE_TITLE;
    case 'Hike':
      return RUN_TITLES.HIKE_TITLE;
    case 'Rowing':
      return RUN_TITLES.ROWING_TITLE;
    case 'Swim':
      return RUN_TITLES.SWIM_TITLE;
    case 'RoadTrip':
      return RUN_TITLES.ROAD_TRIP_TITLE;
    case 'Flight':
      return RUN_TITLES.FLIGHT_TITLE;
    case 'Kayaking':
      return RUN_TITLES.KAYAKING_TITLE;
    case 'Snowboard':
      return RUN_TITLES.SNOWBOARD_TITLE;
    default:
      return RUN_TITLES.RUN_TITLE;
  }
}

const titleForRun = (run) => {
  const type = run.type;
  if (type == 'Run'){
      const runDistance = run.distance / 1000;
      if (runDistance >= 40) {
        return RUN_TITLES.FULL_MARATHON_RUN_TITLE;
      }
      else if (runDistance > 20) {
        return RUN_TITLES.HALF_MARATHON_RUN_TITLE;
      }
  }
  return titleForType(type);
};

const colorFromType = (workoutType) => {
  switch (workoutType) {
    case 'Run':
      return RUN_COLOR;
    case 'Ride':
    case 'Indoor Ride':
      return RIDE_COLOR;
    case 'VirtualRide':
      return VIRTUAL_RIDE_COLOR;
    case 'Hike':
      return HIKE_COLOR;
    case 'Rowing':
      return ROWING_COLOR;
    case 'Swim':
      return SWIM_COLOR;
    case 'RoadTrip':
      return ROAD_TRIP_COLOR;
    case 'Flight':
      return FLIGHT_COLOR;
    case 'Kayaking':
      return KAYAKING_COLOR;
    case 'Snowboard':
      return SNOWBOARD_COLOR;
    default:
      return MAIN_COLOR;
  }
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
  const viewport = new WebMercatorViewport({
    width: 800,
    height: 600,
  }).fitBounds(cornersLongLat, { padding: 200 });
  let { longitude, latitude, zoom } = viewport;
  if (features.length > 1) {
    zoom = 11.5;
  }
  return { longitude, latitude, zoom };
};

const filterYearRuns = (run, year) => {
  if (run && run.start_date_local) {
    return run.start_date_local.slice(0, 4) === year;
  }
  return false;
};

const filterCityRuns = (run, city) => {
  if (run && run.location_country) {
    return run.location_country.includes(city);
  }
  return false;
};
const filterTitleRuns = (run, title) => titleForRun(run) === title;

const filterTypeRuns = (run, type) => run.type === type;

const filterAndSortRuns = (activities, item, filterFunc, sortFunc) => {
  let s = activities;
  if (item !== 'Total') {
    s = activities.filter((run) => filterFunc(run, item));
  }
  return s.sort(sortFunc);
};

const sortDateFunc = (a, b) =>
  new Date(b.start_date_local.replace(' ', 'T')) -
  new Date(a.start_date_local.replace(' ', 'T'));
const sortDateFuncReverse = (a, b) => sortDateFunc(b, a);

export {
  titleForShow,
  formatPace,
  scrollToMap,
  locationForRun,
  intComma,
  pathForRun,
  geoJsonForRuns,
  geoJsonForMap,
  titleForRun,
  titleForType,
  filterYearRuns,
  filterCityRuns,
  filterTitleRuns,
  filterAndSortRuns,
  sortDateFunc,
  sortDateFuncReverse,
  getBoundsForGeoData,
  filterTypeRuns,
  colorFromType,
  formatRunTime,
  convertMovingTime2Sec,
};
