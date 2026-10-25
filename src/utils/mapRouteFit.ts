import * as polyline from '@mapbox/polyline';
import mapboxgl from 'mapbox-gl';
import type { Activity } from '../types';
import type { Coordinate } from './routeAnimation';

function boundsFromCoords(coords: Coordinate[]): mapboxgl.LngLatBounds | null {
  if (coords.length === 0) return null;
  const bounds = new mapboxgl.LngLatBounds();
  for (const c of coords) bounds.extend(c);
  return bounds;
}

/** Pull back so an export end card can show the whole route beside left-side stats. */
export function fitMapToEndCard(
  map: mapboxgl.Map,
  coords: Coordinate[],
  opts?: { sizeMode?: 'native' | 'phone' }
): void {
  const bounds = boundsFromCoords(coords);
  if (!bounds) return;
  const width = map.getContainer().clientWidth || 1;
  const height = map.getContainer().clientHeight || 1;
  map.stop();
  const phone = opts?.sizeMode === 'phone';
  // Phone video cover-crops the center 9:16 of this canvas. Fit the route into
  // that crop (not the full window) so fullscreen and a small card match.
  const padding = phone
    ? phoneEndCardPadding(width, height)
    : {
        top: 48,
        bottom: 40,
        left: Math.round(Math.max(140, width * 0.42)),
        right: 36,
      };
  const camera = map.cameraForBounds(bounds, {
    padding,
    maxZoom: phone ? 17.5 : 16,
  });
  if (!camera || camera.zoom == null) return;
  // End still used to fit the whole route into padded space and read small.
  // 1.5× linear scale ≈ +0.58 zoom (both native and phone).
  const zoom = Math.min(camera.zoom + Math.log2(1.5), phone ? 18 : 17);
  map.easeTo({
    center: camera.center,
    zoom,
    bearing: 0,
    pitch: 0,
    duration: 800,
  });
}

/** Padding that places the route inside the 1080×1920 cover crop, left room for stats. */
function phoneEndCardPadding(
  width: number,
  height: number
): { top: number; bottom: number; left: number; right: number } {
  const targetAspect = 1080 / 1920;
  const insetLeft = 0.4;
  const insetRight = 0.08;
  const insetTop = 0.12;
  const insetBottom = 0.14;
  if (width / height > targetAspect) {
    const cropW = height * targetAspect;
    const side = (width - cropW) / 2;
    return {
      top: Math.round(height * insetTop),
      bottom: Math.round(height * insetBottom),
      left: Math.round(side + cropW * insetLeft),
      right: Math.round(side + cropW * insetRight),
    };
  }
  const cropH = width / targetAspect;
  const vert = (height - cropH) / 2;
  return {
    top: Math.round(vert + cropH * insetTop),
    bottom: Math.round(vert + cropH * insetBottom),
    left: Math.round(width * insetLeft),
    right: Math.round(width * insetRight),
  };
}

export function waitForMapIdle(
  map: mapboxgl.Map,
  timeoutMs = 1600
): Promise<void> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      resolve();
    };
    map.once('idle', finish);
    window.setTimeout(finish, timeoutMs);
  });
}

/** Fit camera to a single selected route (dashboard RouteMap). */
export function fitMapToSelectedRoute(
  map: mapboxgl.Map,
  coords: Coordinate[],
  privacy: boolean
): void {
  const bounds = boundsFromCoords(coords);
  if (!bounds) return;
  map.easeTo({
    pitch: 0,
    bearing: 0,
    duration: privacy ? 200 : 400,
  });
  map.fitBounds(bounds, {
    padding: 50,
    maxZoom: 14,
    duration: privacy ? 200 : 500,
  });
}

/** Light sample for overview 3D orbit (each route start + end). */
export function overviewOrbitCoords(activities: Activity[]): Coordinate[] {
  const out: Coordinate[] = [];
  for (const a of activities) {
    if (!a.summary_polyline) continue;
    const coords = polyline.decode(a.summary_polyline);
    if (coords.length === 0) continue;
    out.push([coords[0][1], coords[0][0]]);
    const last = coords[coords.length - 1];
    out.push([last[1], last[0]]);
  }
  return out;
}

/** Fit camera to all routes on home map (trimmed bbox). */
export function fitMapToRouteOverview(
  map: mapboxgl.Map,
  activities: Activity[],
  privacy: boolean
): void {
  const allCoords: [number, number][] = [];
  for (const a of activities) {
    if (!a.summary_polyline) continue;
    const coords = polyline.decode(a.summary_polyline);
    if (coords.length > 0) {
      allCoords.push([coords[0][1], coords[0][0]]);
    }
  }
  if (allCoords.length === 0) return;

  const trimPct = 0.1;
  const trimCount = Math.floor(allCoords.length * trimPct);
  const lngs = allCoords.map((c) => c[0]).sort((a, b) => a - b);
  const lats = allCoords.map((c) => c[1]).sort((a, b) => a - b);

  const bounds = new mapboxgl.LngLatBounds(
    [lngs[trimCount], lats[trimCount]],
    [lngs[lngs.length - 1 - trimCount], lats[lats.length - 1 - trimCount]]
  );

  map.easeTo({
    pitch: 0,
    bearing: 0,
    duration: privacy ? 200 : 400,
  });
  map.fitBounds(bounds, {
    padding: 30,
    maxZoom: 13,
    duration: privacy ? 200 : 500,
  });
}

/** Fit camera to all routes on Tracks page map. */
export function fitTrackMapOverview(
  map: mapboxgl.Map,
  activities: Activity[],
  privacy: boolean
): void {
  const allCoords = activities
    .filter((a) => a.summary_polyline)
    .flatMap((a) =>
      polyline
        .decode(a.summary_polyline!)
        .map(([lat, lng]) => [lng, lat] as [number, number])
    );
  if (allCoords.length === 0) return;

  const lngs = allCoords.map((c) => c[0]).sort((a, b) => a - b);
  const lats = allCoords.map((c) => c[1]).sort((a, b) => a - b);
  const t = Math.floor(lngs.length * 0.1);

  map.easeTo({ pitch: 0, bearing: 0, duration: privacy ? 200 : 600 });
  map.fitBounds(
    new mapboxgl.LngLatBounds(
      [lngs[t], lats[t]],
      [lngs[lngs.length - 1 - t], lats[lats.length - 1 - t]]
    ),
    {
      padding: 30,
      maxZoom: 13,
      duration: privacy ? 200 : 800,
    }
  );
}
