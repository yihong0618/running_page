# Migration Guide: Upgrading to MapCN

## For Existing Users

If you've been using running_page with Mapbox, this guide helps you migrate to the new free MapCN default.

## What Changed?

**Before (using Mapbox):**
```typescript
// Old default in src/utils/const.ts
export const MAP_TILE_VENDOR = 'mapbox';
export const MAP_TILE_STYLE_LIGHT = 'light-v10';
export const MAP_TILE_STYLE_DARK = 'dark-v10';
export const MAP_TILE_ACCESS_TOKEN = 'pk.eyJ1Ijo...'; // Your token
```

**After (using MapCN):**
```typescript
// New default in src/utils/const.ts
export const MAP_TILE_VENDOR = 'mapcn';
export const MAP_TILE_STYLE_LIGHT = 'osm-bright';
export const MAP_TILE_STYLE_DARK = 'dark-matter';
export const MAP_TILE_ACCESS_TOKEN = ''; // No token needed!
```

## Migration Steps

### Option 1: Automatic (Recommended)

1.  Pull the latest code:
    ```bash
    git pull origin master
    ```
2.  **The defaults are already configured for MapCN!** Just rebuild:
    ```bash
    pnpm install
    pnpm build
    ```
3.  Redeploy (if using Vercel/GitHub Pages, it will auto-deploy)
4.  Verify - Visit your site and check maps load correctly

That's it! No Mapbox token needed anymore. 🎉

### Option 2: Keep Using Mapbox (If You Prefer)

If you want to continue using Mapbox:

1.  Preserve your configuration in `src/utils/const.ts`:
    ```typescript
    export const MAP_TILE_VENDOR = 'mapbox';
    export const MAP_TILE_STYLE_LIGHT = 'light-v10';
    export const MAP_TILE_STYLE_DARK = 'dark-v10';
    export const MAP_TILE_ACCESS_TOKEN = 'your_mapbox_token_here';
    ```
2.  Rebuild and redeploy:
    ```bash
    pnpm build
    ```

**Note:** You'll continue to use your Mapbox token (costs may apply).

## What to Expect

### Visual Differences

| Aspect | Mapbox | MapCN (Carto) |
| :--- | :--- | :--- |
| **Quality** | Excellent | Very Good |
| **Styling** | Sleek, modern | Clean, OSM-based |
| **Color Palette** | Mapbox brand colors | Neutral/natural colors |
| **Labels** | Professional typography | Standard OSM labels |
| **Performance** | Very fast | Fast (CDN-backed) |

### Map Style Comparison

**Light Theme:**
*   Mapbox: `light-v10` (cool gray, blue water)
*   MapCN: `osm-bright` (warm tan, blue water)

**Dark Theme:**
*   Mapbox: `dark-v10` (charcoal gray)
*   MapCN: `dark-matter` (deep blue-gray)

Routes on both styles are highly visible - this is the most important aspect for running visualization!

## Troubleshooting

### Maps Not Loading After Migration?

1.  Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)
2.  Check browser console (F12) for errors
3.  Verify configuration in `src/utils/const.ts`
4.  Try fallback provider:
    ```typescript
    export const MAP_TILE_VENDOR = 'mapcn_openfreemap';
    ```

### "403 Forbidden" Errors?

If you're in China or behind strict firewall:
```typescript
export const MAP_TILE_VENDOR = 'mapcn_openfreemap';
```

### Want to Switch Back to Mapbox Temporarily?

```typescript
export const MAP_TILE_VENDOR = 'mapbox';
export const MAP_TILE_STYLE_LIGHT = 'light-v11';
export const MAP_TILE_STYLE_DARK = 'dark-v11';
export const MAP_TILE_ACCESS_TOKEN = 'your_token_here';
```
Rebuild and redeploy.

## Benefits of MapCN

*   ✅ **Free** - No token, no registration, no costs
*   ✅ **Simple** - Works out of the box
*   ✅ **Open** - Based on OpenStreetMap data
*   ✅ **Reliable** - Backed by CARTO's CDN
*   ✅ **Legal** - Free for non-commercial/personal use

## Commercial Users

⚠️ If you use `running_page` for commercial purposes, you must either:

1.  Obtain a CARTO Enterprise license, OR
2.  Switch to paid Mapbox/MapTiler

See `docs/CARTO_TERMS.md` for details.

## Questions?

*   Technical issues: See `docs/TESTING_MAPCN.md`
*   General questions: Open a GitHub Issue
*   Carto terms: See `docs/CARTO_TERMS.md`

### Feedback

Please report your migration experience in Issue #1055!
