/**
 * 配置从根目录 config.yml 加载，由 Vite 在构建时转换。
 * 直接编辑 config.yml 即可，无需改动此文件。
 */
import rawConfig from '@config';
import type { Locale } from './i18n';

export interface GoalConfig {
  yearly: number;
  monthly: number;
  weekly: number;
  /** 'distance' (km) | 'time' (minutes) */
  unit: 'distance' | 'time';
}

export interface NavLink {
  name: string;
  url: string;
}

export interface SiteMetadata {
  siteTitle: string;
  siteUrl: string;
  logo: string;
  description: string;
  repoUrl: string | undefined;
  navLinks: NavLink[];
}

interface AppConfig {
  // 站点信息
  site_title: string;
  site_url: string;
  site_logo: string;
  site_description: string;
  repo_url: string;
  nav_links: NavLink[];

  // 地图配置
  map_provider: 'maptiler' | 'mapbox' | 'openfreemap';
  map_style_light: string;
  map_style_dark: string;
  mapbox_token: string;
  maptiler_token: string;

  // 轨迹显示
  show_start_end_markers: boolean;
  start_marker_color: string;
  end_marker_color: string;

  // 外观
  locale: Locale;
  theme: 'light' | 'dark' | 'system';
  theme_preset: string;
  avatar?: string;
  goals: Record<string, GoalConfig>;
}

const config = rawConfig as unknown as AppConfig;

// 站点元数据
export const SITE_METADATA: SiteMetadata = {
  siteTitle: config.site_title ?? 'Running Page',
  siteUrl: config.site_url ?? '',
  logo: config.site_logo ?? '',
  description: config.site_description ?? 'Personal site and blog',
  repoUrl: config.repo_url,
  navLinks: config.nav_links ?? [],
};

// 地图配置
export const MAP_PROVIDER: string = config.map_provider ?? 'openfreemap';
export const MAP_STYLE_LIGHT: string = config.map_style_light ?? 'bright';
export const MAP_STYLE_DARK: string = config.map_style_dark ?? 'dark';
export const MAPBOX_TOKEN: string =
  import.meta.env.VITE_MAPBOX_TOKEN || config.mapbox_token || '';
export const MAPTILER_TOKEN: string =
  import.meta.env.VITE_MAPTILER_TOKEN || config.maptiler_token || '';

// 轨迹显示配置
export const SHOW_START_END_MARKERS: boolean =
  config.show_start_end_markers ?? true;
export const START_MARKER_COLOR: string =
  config.start_marker_color ?? '#ffffff';
export const END_MARKER_COLOR: string = config.end_marker_color ?? '#ef4444';

// 外观配置
export const DEFAULT_LOCALE: Locale = config.locale ?? 'zh';
export const DEFAULT_THEME: 'light' | 'dark' | 'system' =
  config.theme ?? 'system';
export const THEME_PRESET: string = config.theme_preset ?? 'default';
export const GOALS: Record<string, GoalConfig> = config.goals ?? {};
export const DEFAULT_GOAL: GoalConfig = GOALS.all ?? {
  yearly: 2000,
  monthly: 150,
  weekly: 35,
  unit: 'distance',
};
export const AVATAR: string = config.avatar ?? '';
