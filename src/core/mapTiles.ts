// Free, tokenless map tile styles for local development / fallback.
// Same provider used by the classic theme (mapcn_openfreemap):
//   https://tiles.openfreemap.org/ - OpenFreeMap, no API key required.
export const MAP_TILE_STYLE_LIGHT = 'https://tiles.openfreemap.org/styles/bright';
export const MAP_TILE_STYLE_DARK = 'https://tiles.openfreemap.org/styles/dark';

/** Returns a tokenless GL style URL based on the current theme. */
export function getMapStyle(dark: boolean): string {
  return dark ? MAP_TILE_STYLE_DARK : MAP_TILE_STYLE_LIGHT;
}
