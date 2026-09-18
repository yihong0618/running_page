/**
 * 地图瓦片配置
 * 支持 MapTiler、Mapbox 和 OpenFreeMap
 */
import {
  MAP_PROVIDER,
  MAP_STYLE_LIGHT,
  MAP_STYLE_DARK,
  MAPBOX_TOKEN,
  MAPTILER_TOKEN,
} from './config';

// MapTiler 样式映射
const MAPTILER_STYLES: Record<string, string> = {
  'dataviz-light': 'https://api.maptiler.com/maps/dataviz/style.json?key=',
  'dataviz-dark': 'https://api.maptiler.com/maps/dataviz-dark/style.json?key=',
  'basic-light': 'https://api.maptiler.com/maps/basic-v2/style.json?key=',
  'basic-dark': 'https://api.maptiler.com/maps/basic-v2-dark/style.json?key=',
  'streets-light': 'https://api.maptiler.com/maps/streets-v2/style.json?key=',
  'streets-dark':
    'https://api.maptiler.com/maps/streets-v2-dark/style.json?key=',
  'outdoor-light': 'https://api.maptiler.com/maps/outdoor-v2/style.json?key=',
  'outdoor-dark':
    'https://api.maptiler.com/maps/outdoor-v2-dark/style.json?key=',
  'bright-light': 'https://api.maptiler.com/maps/bright-v2/style.json?key=',
  'bright-dark': 'https://api.maptiler.com/maps/bright-v2-dark/style.json?key=',
  'topo-light': 'https://api.maptiler.com/maps/topo-v2/style.json?key=',
  'topo-dark': 'https://api.maptiler.com/maps/topo-v2-dark/style.json?key=',
  'winter-light': 'https://api.maptiler.com/maps/winter-v2/style.json?key=',
  'winter-dark': 'https://api.maptiler.com/maps/winter-v2-dark/style.json?key=',
  hybrid: 'https://api.maptiler.com/maps/hybrid/style.json?key=',
};

// Mapbox 样式映射
const MAPBOX_STYLES: Record<string, string> = {
  'dark-v10': 'mapbox://styles/mapbox/dark-v10',
  'dark-v11': 'mapbox://styles/mapbox/dark-v11',
  'light-v10': 'mapbox://styles/mapbox/light-v10',
  'light-v11': 'mapbox://styles/mapbox/light-v11',
  'navigation-night': 'mapbox://styles/mapbox/navigation-night-v1',
  'satellite-streets-v12': 'mapbox://styles/mapbox/satellite-streets-v12',
};

// OpenFreeMap 样式映射
const OPENFREEMAP_STYLES: Record<string, string> = {
  bright: 'https://tiles.openfreemap.org/styles/bright',
  dark: 'https://tiles.openfreemap.org/styles/dark',
  liberty: 'https://tiles.openfreemap.org/styles/liberty',
};

/**
 * 获取地图访问令牌
 */
export function getMapAccessToken(): string {
  switch (MAP_PROVIDER) {
    case 'maptiler':
      return MAPTILER_TOKEN;
    case 'mapbox':
      return MAPBOX_TOKEN;
    case 'openfreemap':
    default:
      return '';
  }
}

/**
 * 获取地图样式 URL (带中文语言参数)
 */
export function getMapStyle(dark: boolean): string {
  const styleName = dark ? MAP_STYLE_DARK : MAP_STYLE_LIGHT;

  switch (MAP_PROVIDER) {
    case 'maptiler': {
      const styleUrl =
        MAPTILER_STYLES[styleName] || MAPTILER_STYLES['streets-light'];
      // 添加语言参数设置为中文
      return styleUrl + MAPTILER_TOKEN;
    }
    case 'mapbox': {
      return MAPBOX_STYLES[styleName] || 'mapbox://styles/mapbox/dark-v10';
    }
    case 'openfreemap':
    default: {
      return OPENFREEMAP_STYLES[styleName] || OPENFREEMAP_STYLES['bright'];
    }
  }
}

/**
 * 检查当前地图提供商是否需要访问令牌
 */
export function mapRequiresToken(): boolean {
  return MAP_PROVIDER === 'maptiler' || MAP_PROVIDER === 'mapbox';
}

// 向后兼容的导出
export const MAP_TILE_STYLE_LIGHT = getMapStyle(false);
export const MAP_TILE_STYLE_DARK = getMapStyle(true);
