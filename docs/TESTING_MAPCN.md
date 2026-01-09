# Testing MapCN/Carto Integration

This guide helps verify that the MapCN integration works correctly.

## Prerequisites

- Node.js >= 20
- pnpm installed
- Running data synced (or sample data)

## Quick Test (5 minutes)

1. Clone the repository and checkout the PR branch.
2. Install dependencies:
   ```bash
   pnpm install
   ```
3. Start development server:
   ```bash
   pnpm develop
   ```
4. Open http://localhost:5173 in your browser.

## Testing Checklist

### ✅ Basic Functionality
- [ ] Map tiles load without errors.
- [ ] Map displays at correct initial position.
- [ ] No console errors in browser DevTools.
- [ ] No 404 or network errors in Network tab.

### ✅ Visual Quality
- [ ] Map tiles are clear and readable.
- [ ] Text labels are visible.
- [ ] Colors match the theme (light/dark).
- [ ] Map looks professional.

### ✅ Running Routes
- [ ] Running route polylines display correctly.
- [ ] Routes follow actual paths (not straight lines).
- [ ] Multiple routes display without overlap issues.
- [ ] Route colors are visible against map background.

### ✅ Theme Switching
- [ ] **Light theme:** Map uses `osm-bright` (Voyager) style.
- [ ] **Dark theme:** Map uses `dark-matter` style.
- [ ] Switching themes updates map immediately.
- [ ] No visual glitches during theme transition.

### ✅ Map Controls
- [ ] Zoom in/out buttons work.
- [ ] Zoom with scroll wheel works.
- [ ] Pan/drag map works.
- [ ] Fullscreen control works.
- [ ] "Lights" control works (privacy mode).

### ✅ Performance
- [ ] Map loads in < 5 seconds on normal connection.
- [ ] Zoom/pan is smooth (no lag).
- [ ] Works well with many routes displayed.

### ✅ Responsive Design
- [ ] Map displays correctly on mobile screens.
- [ ] Touch gestures work (pinch zoom, drag).
- [ ] Controls are accessible on small screens.

### ✅ Chinese Language Support (if IS_CHINESE = true)
- [ ] Map labels show Chinese characters (where available in basemap data).
- [ ] Chinese location names display correctly.

### ✅ Backward Compatibility
Test switching back to other providers:

**Test Mapbox:**
Modify `src/utils/const.ts`:
```typescript
export const MAP_TILE_VENDOR = 'mapbox';
export const MAP_TILE_STYLE_LIGHT = 'light-v10';
export const MAP_TILE_STYLE_DARK = 'dark-v10';
export const MAP_TILE_ACCESS_TOKEN = 'your_mapbox_token';
```
- [ ] Mapbox works correctly.

**Test MapTiler:**
Modify `src/utils/const.ts`:
```typescript
export const MAP_TILE_VENDOR = 'maptiler';
export const MAP_TILE_STYLE_LIGHT = 'basic-light';
export const MAP_TILE_STYLE_DARK = 'basic-dark';
export const MAP_TILE_ACCESS_TOKEN = 'your_maptiler_token';
```
- [ ] MapTiler works correctly.

## China-Specific Testing
If testing from China:
- [ ] Map tiles load (not blocked by firewall).
- [ ] Loading speed is acceptable.
- [ ] No timeout errors.

**Note:** If Carto is blocked, check if `MAP_TILE_FALLBACK_PROVIDERS` are configured and working.

## Troubleshooting Guide

### Problem: Maps not loading at all

**Symptoms:** Blank gray area where map should be

**Solutions:**
1. Open browser console (F12 → Console tab)
2. Look for error messages:

**Error: "Failed to fetch style"**
`❌ Failed to fetch: https://basemaps.cartocdn.com/...`

**Fix:**
- Check internet connection
- If in China, switch to fallback:
  ```typescript
  export const MAP_TILE_VENDOR = 'mapcn_openfreemap';
  ```
- Or try: `pnpm verify:maps` to test URLs

**Error: "Unauthorized" or "Invalid token"**

`❌ 401 Unauthorized`

**Fix:**
You're using wrong vendor with empty token
Solution:
```typescript
// Either keep MapCN (no token):
export const MAP_TILE_VENDOR = 'mapcn';
export const MAP_TILE_ACCESS_TOKEN = '';

// Or add token for other vendors:
export const MAP_TILE_VENDOR = 'mapbox';
export const MAP_TILE_ACCESS_TOKEN = 'pk.your_token_here';
```

### Problem: Maps load but routes don't show
**Symptoms:** Map visible, but no running routes

**Solutions:**
- Check if you have synced data: `src/static/activities.json` should exist
- Check console for JavaScript errors
- Verify route data exists: `pnpm data:analysis`

### Problem: Wrong colors or style
**Symptoms:** Map looks weird, doesn't match theme

**Cause:** Style mismatch between vendor and style name

**Fix:**
```typescript
// ❌ WRONG - mixing vendors
export const MAP_TILE_VENDOR = 'mapcn';
export const MAP_TILE_STYLE_LIGHT = 'light-v10'; // This is Mapbox!

// ✅ CORRECT
export const MAP_TILE_VENDOR = 'mapcn';
export const MAP_TILE_STYLE_LIGHT = 'osm-bright'; // This is Carto
```

### Problem: Slow loading in China
**Symptoms:** Map takes >10 seconds to load

**Solutions:**
Switch to OpenFreeMap (no CDN blocking):
```typescript
export const MAP_TILE_VENDOR = 'mapcn_openfreemap';
```
Or use MapTiler with China servers:
```typescript
export const MAP_TILE_VENDOR = 'maptiler';
export const MAP_TILE_ACCESS_TOKEN = 'get_free_token';
```

### Problem: "403 Forbidden" errors
**Symptoms:** Network tab shows 403 errors

**Cause:** Firewall or regional blocking

**Solutions:**
- Test URL access: `pnpm verify:maps`
- Switch to fallback provider
- Try different network (VPN if necessary)

### Problem: Map works locally but not on deployed site
**Symptoms:** Works on `localhost:5173` but not on `yourdomain.com`

**Possible causes:**
- HTTPS mixed content - Deployed site must use HTTPS
- CORS issues - Should not affect Carto (publicly accessible)
- Cache issues - Clear CDN/browser cache

**Solutions:**
- Ensure your deployed site uses HTTPS
- Clear Vercel/Netlify cache and redeploy
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Problem: Attribution not showing
**Symptoms:** No "© CARTO" text on map

**Fix:** Attribution should be automatic with Mapbox GL JS, but verify in:
```typescript
// In your Map component, ensure attributionControl is true
<Map attributionControl={true} ... />
```

## Quick Diagnostic Checklist
Run through this checklist to diagnose issues:

- [ ] Is your internet connection working?
- [ ] Can you access `https://basemaps.cartocdn.com` in browser?
- [ ] Is `MAP_TILE_VENDOR = 'mapcn'` in const.ts?
- [ ] Is `MAP_TILE_ACCESS_TOKEN = ''` (empty)?
- [ ] Did you run `pnpm install`?
- [ ] Did you restart dev server after config changes?
- [ ] Are there console errors? (F12)
- [ ] Do you have running data in `src/static/activities.json`?

### Still Having Issues?
1. Run verification: `pnpm verify:maps`
2. Check logs: Browser console (F12) and terminal
3. Try fallback: Switch to `mapcn_openfreemap`
4. Ask for help: Open GitHub issue with:
   - Your OS and browser
   - Console error messages
   - Network tab screenshots
   - Your `MAP_TILE_VENDOR` setting
