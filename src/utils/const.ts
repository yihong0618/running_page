// Constants
const MAPBOX_TOKEN =
  // For security reasons, please avoid using the default public token provided by Mapbox as much as possible.
  // Instead, manually add a new token and apply URL restrictions.
  // (please refer to https://github.com/yihong0618/running_page/issues/643#issuecomment-2042668580)
  'pk.eyJ1IjoieWlob25nMDYxOCIsImEiOiJjbWYxdXR4YncwMTJtMm5zOTE4eTZpMGdtIn0.OnsXdwkZFztR8a5Ph_T-xg';
const MUNICIPALITY_CITIES_ARR = [
  '北京市',
  '上海市',
  '天津市',
  '重庆市',
  '香港特别行政区',
  '澳门特别行政区',
];
const MAP_LAYER_LIST = [
  'road-label',
  'waterway-label',
  'natural-line-label',
  'natural-point-label',
  'water-line-label',
  'water-point-label',
  'poi-label',
  'airport-label',
  'settlement-subdivision-label',
  'settlement-label',
  'state-label',
  'country-label',
];

const USE_GOOGLE_ANALYTICS = false;
const GOOGLE_ANALYTICS_TRACKING_ID = '';

// styling: set to `true` if you want dash-line route
const USE_DASH_LINE = true;
// styling: route line opacity: [0, 1]
const LINE_OPACITY = 0.4;
// styling: map height - responsive design
// Use smaller height on mobile devices for better user experience
const MAP_HEIGHT = window.innerWidth <= 768 ? 250 : 600;
//set to `false` if you want to hide the road label characters
const ROAD_LABEL_DISPLAY = true;
// updated on 2024/11/17: privacy mode is set to true by default
//set to `true` if you want to display only the routes without showing the map.
const PRIVACY_MODE = false;
// updated on 2024/11/17: lights are turned off by default
//set to `false` if you want to make light off as default, only effect when `PRIVACY_MODE` = false
const LIGHTS_ON = false;
//set to `true` if you want to show the 'Elevation Gain' column
const SHOW_ELEVATION_GAIN = false;
// richer title for the activity types (like garmin style)
const RICH_TITLE = false;

// IF you are outside China please make sure IS_CHINESE = false
const IS_CHINESE = true;
const USE_ANIMATION_FOR_GRID = false;
const CHINESE_INFO_MESSAGE = (yearLength: number, year: string): string => {
  const yearStr = year === 'Total' ? '所有' : ` ${year} `;
  return `记录自己跑步 ${yearLength} 年了，下面列表展示的是${yearStr}的数据`;
};
const ENGLISH_INFO_MESSAGE = (yearLength: number, year: string): string =>
  `Running Journey with ${yearLength} Years, the table shows year ${year} data`;

// English is not supported for location info messages yet
const CHINESE_LOCATION_INFO_MESSAGE_FIRST =
  '跑过了一些地方，希望随着时间推移，点亮的地方越来越多';
const CHINESE_LOCATION_INFO_MESSAGE_SECOND = '不要停下来，不要停下奔跑的脚步';

const INFO_MESSAGE = IS_CHINESE ? CHINESE_INFO_MESSAGE : ENGLISH_INFO_MESSAGE;
const FULL_MARATHON_RUN_TITLE = IS_CHINESE ? '全程马拉松' : 'Full Marathon';
const HALF_MARATHON_RUN_TITLE = IS_CHINESE ? '半程马拉松' : 'Half Marathon';
const MORNING_RUN_TITLE = IS_CHINESE ? '清晨跑步' : 'Morning Run';
const MIDDAY_RUN_TITLE = IS_CHINESE ? '午间跑步' : 'Midday Run';
const AFTERNOON_RUN_TITLE = IS_CHINESE ? '午后跑步' : 'Afternoon Run';
const EVENING_RUN_TITLE = IS_CHINESE ? '傍晚跑步' : 'Evening Run';
const NIGHT_RUN_TITLE = IS_CHINESE ? '夜晚跑步' : 'Night Run';
const RUN_GENERIC_TITLE = IS_CHINESE ? '跑步' : 'Run';
const RUN_TRAIL_TITLE = IS_CHINESE ? '越野跑' : 'Trail Run';
const RUN_TREADMILL_TITLE = IS_CHINESE ? '跑步机' : 'Treadmill Run';
const HIKING_TITLE = IS_CHINESE ? '徒步' : 'Hiking';
const CYCLING_TITLE = IS_CHINESE ? '骑行' : 'Cycling';
const SKIING_TITLE = IS_CHINESE ? '滑雪' : 'Skiing';
const WALKING_TITLE = IS_CHINESE ? '步行' : 'Walking';
const SWIMMING_TITLE = IS_CHINESE ? '游泳' : 'Swimming';
const ALL_TITLE = IS_CHINESE ? '所有' : 'All';
const ACTIVITY_COUNT_TITLE = IS_CHINESE ? '活动次数' : 'Activity Count';
const MAX_DISTANCE_TITLE = IS_CHINESE ? '最远距离' : 'Max Distance';
const MAX_SPEED_TITLE = IS_CHINESE ? '最快速度' : 'Max Speed';
const TOTAL_TIME_TITLE = IS_CHINESE ? '总时间' : 'Total Time';
const AVERAGE_SPEED_TITLE = IS_CHINESE ? '平均速度' : 'Average Speed';
const TOTAL_DISTANCE_TITLE = IS_CHINESE ? '总距离' : 'Total Distance';
const AVERAGE_DISTANCE_TITLE = IS_CHINESE ? '平均距离' : 'Average Distance';
const TOTAL_ELEVATION_GAIN_TITLE = IS_CHINESE
  ? '总海拔爬升'
  : 'Total Elevation Gain';
const AVERAGE_HEART_RATE_TITLE = IS_CHINESE ? '平均心率' : 'Average Heart Rate';
const YEARLY_TITLE = IS_CHINESE ? 'Year' : 'Yearly';
const MONTHLY_TITLE = IS_CHINESE ? 'Month' : 'Monthly';
const WEEKLY_TITLE = IS_CHINESE ? 'Week' : 'Weekly';
const DAILY_TITLE = IS_CHINESE ? 'Day' : 'Daily';
const LOCATION_TITLE = IS_CHINESE ? 'Location' : 'Location';
const HOME_PAGE_TITLE = IS_CHINESE ? '首页' : 'Home';

const LOADING_TEXT = IS_CHINESE ? '加载中...' : 'Loading...';
const NO_ROUTE_DATA = IS_CHINESE ? '暂无路线数据' : 'No route data';
const INVALID_ROUTE_DATA = IS_CHINESE ? '路线数据无效' : 'Invalid route data';

const ACTIVITY_TYPES = {
  RUN_GENERIC_TITLE,
  RUN_TRAIL_TITLE,
  RUN_TREADMILL_TITLE,
  HIKING_TITLE,
  CYCLING_TITLE,
  SKIING_TITLE,
  WALKING_TITLE,
  SWIMMING_TITLE,
  ALL_TITLE,
};

const RUN_TITLES = {
  FULL_MARATHON_RUN_TITLE,
  HALF_MARATHON_RUN_TITLE,
  MORNING_RUN_TITLE,
  MIDDAY_RUN_TITLE,
  AFTERNOON_RUN_TITLE,
  EVENING_RUN_TITLE,
  NIGHT_RUN_TITLE,
};
const ACTIVITY_TOTAL = {
  ACTIVITY_COUNT_TITLE,
  MAX_DISTANCE_TITLE,
  MAX_SPEED_TITLE,
  TOTAL_TIME_TITLE,
  AVERAGE_SPEED_TITLE,
  TOTAL_DISTANCE_TITLE,
  AVERAGE_DISTANCE_TITLE,
  TOTAL_ELEVATION_GAIN_TITLE,
  AVERAGE_HEART_RATE_TITLE,
  YEARLY_TITLE,
  MONTHLY_TITLE,
  WEEKLY_TITLE,
  DAILY_TITLE,
  LOCATION_TITLE,
};

export {
  USE_GOOGLE_ANALYTICS,
  GOOGLE_ANALYTICS_TRACKING_ID,
  CHINESE_LOCATION_INFO_MESSAGE_FIRST,
  CHINESE_LOCATION_INFO_MESSAGE_SECOND,
  MAPBOX_TOKEN,
  MUNICIPALITY_CITIES_ARR,
  MAP_LAYER_LIST,
  IS_CHINESE,
  ROAD_LABEL_DISPLAY,
  INFO_MESSAGE,
  RUN_TITLES,
  USE_ANIMATION_FOR_GRID,
  USE_DASH_LINE,
  LINE_OPACITY,
  MAP_HEIGHT,
  PRIVACY_MODE,
  LIGHTS_ON,
  SHOW_ELEVATION_GAIN,
  RICH_TITLE,
  ACTIVITY_TYPES,
  ACTIVITY_TOTAL,
  HOME_PAGE_TITLE,
  LOADING_TEXT,
  NO_ROUTE_DATA,
  INVALID_ROUTE_DATA,
};

const nike = 'rgb(224,237,94)'; // if you want to change the main color, modify this value in src/styles/variables.scss
const dark_vanilla = 'rgb(228,212,220)';

// If your map has an offset please change this line
// issues #92 and #198
export const NEED_FIX_MAP = false;
export const MAIN_COLOR = nike;
export const PROVINCE_FILL_COLOR = '#47b8e0';
export const COUNTRY_FILL_COLOR = dark_vanilla;

// Static color constants
export const RUN_COLOR_LIGHT = '#47b8e0';
export const RUN_COLOR_DARK = MAIN_COLOR;

// Single run animation colors
export const SINGLE_RUN_COLOR_LIGHT = '#52c41a'; // Green for light theme
export const SINGLE_RUN_COLOR_DARK = '#ff4d4f'; // Red for dark theme

// Helper function to get theme-aware RUN_COLOR
export const getRuntimeRunColor = (): string => {
  if (typeof window === 'undefined') return RUN_COLOR_DARK;

  const dataTheme = document.documentElement.getAttribute('data-theme');
  const savedTheme = localStorage.getItem('theme');

  // Determine current theme (default to dark)
  const isDark =
    dataTheme === 'dark' ||
    (!dataTheme && savedTheme === 'dark') ||
    (!dataTheme && !savedTheme);

  return isDark ? RUN_COLOR_DARK : RUN_COLOR_LIGHT;
};

// Helper function to get theme-aware SINGLE_RUN_COLOR
export const getRuntimeSingleRunColor = (): string => {
  if (typeof window === 'undefined') return SINGLE_RUN_COLOR_DARK;

  const dataTheme = document.documentElement.getAttribute('data-theme');
  const savedTheme = localStorage.getItem('theme');

  // Determine current theme (default to dark)
  const isDark =
    dataTheme === 'dark' ||
    (!dataTheme && savedTheme === 'dark') ||
    (!dataTheme && !savedTheme);

  return isDark ? SINGLE_RUN_COLOR_DARK : SINGLE_RUN_COLOR_LIGHT;
};

// Legacy export for backwards compatibility
export const RUN_COLOR = '#47b8e0';
export const RUN_TRAIL_COLOR = 'rgb(255,153,51)';
export const CYCLING_COLOR = 'rgb(51,255,87)';
export const HIKING_COLOR = 'rgb(151,51,255)';
export const WALKING_COLOR = HIKING_COLOR;
export const SWIMMING_COLOR = 'rgb(255,51,51)';

// map tiles vendor, maptiler or mapbox or stadiamaps
// if you want to use maptiler, set the access token in MAP_TILE_ACCESS_TOKEN
export const MAP_TILE_VENDOR = 'mapcn';

// map tiles style name, see MAP_TILE_STYLES for more details
export const MAP_TILE_STYLE_LIGHT = 'osm-bright';
export const MAP_TILE_STYLE_DARK = 'dark-matter';

// access token. you can apply a new one, it's free.
// maptiler: Gt5R0jT8tuIYxW6sNrAg | sign up at https://cloud.maptiler.com/auth/widget
// stadiamaps: 8a769c5a-9125-4936-bdcf-a6b90cb5d0a4 | sign up at https://client.stadiamaps.com/signup/
// mapcn: empty
export const MAP_TILE_ACCESS_TOKEN = '';

export const MAP_TILE_STYLES = {
  mapcn: {
    'osm-bright':
      'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
    'osm-liberty':
      'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    'dark-matter':
      'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  },
  // Alternative free tile providers for regions where Carto may be blocked
  mapcn_openfreemap: {
    'osm-bright': 'https://tiles.openfreemap.org/styles/bright',
    'dark-matter': 'https://tiles.openfreemap.org/styles/dark',
  },
  mapcn_maptiler_free: {
    // Use free, tokenless styles to avoid requiring an API key
    'osm-bright': 'https://tiles.openfreemap.org/styles/bright',
    'dark-matter': 'https://tiles.openfreemap.org/styles/dark',
  },
  maptiler: {
    'dataviz-light': 'https://api.maptiler.com/maps/dataviz/style.json?key=',
    'dataviz-dark':
      'https://api.maptiler.com/maps/dataviz-dark/style.json?key=',
    'basic-light': 'https://api.maptiler.com/maps/basic-v2/style.json?key=',
    'basic-dark': 'https://api.maptiler.com/maps/basic-v2-dark/style.json?key=',
    'streets-light': 'https://api.maptiler.com/maps/streets-v2/style.json?key=',
    'streets-dark':
      'https://api.maptiler.com/maps/streets-v2-dark/style.json?key=',
    'outdoor-light': 'https://api.maptiler.com/maps/outdoor-v2/style.json?key=',
    'outdoor-dark':
      'https://api.maptiler.com/maps/outdoor-v2-dark/style.json?key=',
    'bright-light': 'https://api.maptiler.com/maps/bright-v2/style.json?key=',
    'bright-dark':
      'https://api.maptiler.com/maps/bright-v2-dark/style.json?key=',
    'topo-light': 'https://api.maptiler.com/maps/topo-v2/style.json?key=',
    'topo-dark': 'https://api.maptiler.com/maps/topo-v2-dark/style.json?key=',
    'winter-light': 'https://api.maptiler.com/maps/winter-v2/style.json?key=',
    'winter-dark':
      'https://api.maptiler.com/maps/winter-v2-dark/style.json?key=',
    hybrid: 'https://api.maptiler.com/maps/hybrid/style.json?key=',
  },

  // https://docs.stadiamaps.com/themes/
  stadiamaps: {
    // light
    alidade_smooth:
      'https://tiles.stadiamaps.com/styles/alidade_smooth.json?api_key=',
    alidade_smooth_dark:
      'https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json?api_key=',
    alidade_satellite:
      'https://tiles.stadiamaps.com/styles/alidade_satellite.json?api_key=',
  },

  // https://docs.mapbox.com/api/maps/styles/
  mapbox: {
    'dark-v10': 'mapbox://styles/mapbox/dark-v10',
    'dark-v11': 'mapbox://styles/mapbox/dark-v11',
    'light-v10': 'mapbox://styles/mapbox/light-v10',
    'light-v11': 'mapbox://styles/mapbox/light-v11',
    'navigation-night': 'mapbox://styles/mapbox/navigation-night-v1',
    'satellite-streets-v12': 'mapbox://styles/mapbox/satellite-streets-v12',
  },
  default: 'mapbox://styles/mapbox/dark-v10',
};

// Configuration validation
if (typeof window !== 'undefined') {
  // Validate token requirements
  if (MAP_TILE_VENDOR === 'mapcn' && MAP_TILE_ACCESS_TOKEN !== '') {
    console.warn(
      '⚠️ MapCN (Carto) does not require an access token.\n' +
        '💡 You can set MAP_TILE_ACCESS_TOKEN = "" in src/utils/const.ts'
    );
  }

  if (
    ['mapbox', 'maptiler', 'stadiamaps'].includes(MAP_TILE_VENDOR) &&
    MAP_TILE_ACCESS_TOKEN === ''
  ) {
    console.error(
      `❌ ${MAP_TILE_VENDOR.toUpperCase()} requires an access token!\n` +
        `💡 Please set MAP_TILE_ACCESS_TOKEN in src/utils/const.ts\n` +
        `📚 See README.md for instructions on getting a token.\n` +
        `\n` +
        `💡 TIP: Use MAP_TILE_VENDOR = 'mapcn' for free (no token required)`
    );
  }

  // Validate style matches vendor
  const vendorStyles = (MAP_TILE_STYLES as any)[MAP_TILE_VENDOR];
  if (vendorStyles && !vendorStyles[MAP_TILE_STYLE_LIGHT]) {
    console.error(
      `❌ Style "${MAP_TILE_STYLE_LIGHT}" is not valid for vendor "${MAP_TILE_VENDOR}"\n` +
        `💡 Available styles: ${Object.keys(vendorStyles).join(', ')}\n` +
        `📚 Check src/utils/const.ts MAP_TILE_STYLES for valid combinations`
    );
  }

  // Success message for correct MapCN configuration
  if (
    MAP_TILE_VENDOR === 'mapcn' &&
    MAP_TILE_ACCESS_TOKEN === '' &&
    vendorStyles?.[MAP_TILE_STYLE_LIGHT]
  ) {
    console.info(
      '✅ Using MapCN (Carto Basemaps) - Free, no token required!\n' +
        '📖 Attribution: Map tiles © CARTO, Map data © OpenStreetMap contributors\n' +
        '📚 See docs/CARTO_TERMS.md for usage terms'
    );
  }
}
