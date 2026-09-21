import { useTheme, type ThemeMode } from '../../../core/theme';
import { MAP_TILE_STYLE_DARK, MAP_TILE_STYLE_LIGHT } from '../utils/const';

export type Theme = ThemeMode;
export { useTheme };

export const getMapThemeFromCurrentTheme = (theme: Theme): string =>
  theme === 'dark' ? MAP_TILE_STYLE_DARK : MAP_TILE_STYLE_LIGHT;
