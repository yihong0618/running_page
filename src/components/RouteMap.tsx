import { useEffect, useRef, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import * as polyline from '@mapbox/polyline';
import type { Activity } from '../types';
import { getMapStyle, getMapAccessToken } from '../core/mapTiles';
import {
  SHOW_START_END_MARKERS,
  START_MARKER_COLOR,
  END_MARKER_COLOR,
  DEFAULT_LOCALE,
} from '../core/config';

interface RouteMapProps {
  activities: Activity[];
  selectedActivity?: Activity | null;
  dark?: boolean;
  onClearSelection?: () => void;
}

// Route animation class (simplified from classic theme)
class RouteAnimator {
  private points: [number, number][];
  private duration: number;
  private startTime: number;
  private animId: number | null = null;

  constructor(
    points: [number, number][],
    private onUpdate: (pts: [number, number][]) => void,
    private onComplete: () => void
  ) {
    this.points = points;
    // Duration based on distance, 2-6 seconds
    this.duration = Math.max(2000, Math.min(6000, points.length * 10));
    this.startTime = 0;
  }

  start() {
    if (this.points.length < 2) {
      this.onUpdate(this.points);
      this.onComplete();
      return;
    }
    this.startTime = performance.now();
    this.onUpdate([this.points[0]]);
    this.animId = requestAnimationFrame(this.step.bind(this));
  }

  stop() {
    if (this.animId) {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
  }

  private step(t: number) {
    const elapsed = t - this.startTime;
    const p = Math.min(1, elapsed / this.duration);

    if (p >= 1) {
      this.onUpdate(this.points);
      this.animId = null;
      this.onComplete();
      return;
    }

    const idx = Math.floor(p * (this.points.length - 1));
    this.onUpdate(this.points.slice(0, idx + 1));
    this.animId = requestAnimationFrame(this.step.bind(this));
  }
}

// Get activity color
function getActivityColor(type: string, distance?: number): string {
  if (type === 'Run' || type === 'VirtualRun' || type === 'TrailRun') {
    const km = (distance || 0) / 1000;
    return km >= 40 ? '#ef4444' : '#f97316';
  }
  if (type === 'Ride' || type === 'VirtualRide') return '#3b82f6';
  if (type === 'Hike' || type === 'hiking' || type === 'Hiking')
    return '#22c55e';
  if (type === 'Walk' || type === 'walking' || type === 'Walking')
    return '#eab308';
  if (type === 'Swim' || type === 'swimming' || type === 'Swimming')
    return '#06b6d4';
  return '#a855f7';
}

export function RouteMap({
  activities,
  selectedActivity,
  dark,
  onClearSelection,
}: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const animatorRef = useRef<RouteAnimator | null>(null);
  const style = getMapStyle(dark !== false);

  const clearMarkers = useCallback(() => {
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];
  }, []);

  const addStartEndMarkers = useCallback(
    (coords: [number, number][]) => {
      if (!map.current || !SHOW_START_END_MARKERS || coords.length < 2) return;
      clearMarkers();

      const startEl = document.createElement('div');
      startEl.innerHTML =
        '<svg width="20" height="28" viewBox="0 0 20 28"><path d="M10 0v20" stroke="#999" stroke-width="1.5"/><path d="M10 2l10 5-10 5V2z" fill="' +
        START_MARKER_COLOR +
        '" stroke="#aaa" stroke-width="0.5"/><circle cx="10" cy="24" r="3.5" fill="#999"/></svg>';
      markersRef.current.push(
        new mapboxgl.Marker({ element: startEl })
          .setLngLat(coords[0])
          .addTo(map.current)
      );

      const endEl = document.createElement('div');
      endEl.innerHTML =
        '<svg width="20" height="28" viewBox="0 0 20 28"><path d="M10 0v20" stroke="#999" stroke-width="1.5"/><path d="M10 2l10 5-10 5V2z" fill="' +
        END_MARKER_COLOR +
        '" stroke="#dc2626" stroke-width="0.5"/><circle cx="10" cy="24" r="3.5" fill="#999"/></svg>';
      markersRef.current.push(
        new mapboxgl.Marker({ element: endEl })
          .setLngLat(coords[coords.length - 1])
          .addTo(map.current)
      );
    },
    [clearMarkers]
  );

  const updateRoutes = useCallback(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // Stop any ongoing animation
    if (animatorRef.current) {
      animatorRef.current.stop();
      animatorRef.current = null;
    }
    clearMarkers();

    // Remove all selected-related layers/sources
    ['selected', 'selected-bg', 'selected-casing', 'routes'].forEach((id) => {
      try {
        if (map.current!.getLayer(id)) map.current!.removeLayer(id);
      } catch {
        /* ignore */
      }
      try {
        if (map.current!.getSource(id)) map.current!.removeSource(id);
      } catch {
        /* ignore */
      }
    });

    if (selectedActivity?.summary_polyline) {
      const coords = polyline
        .decode(selectedActivity.summary_polyline)
        .map(([lat, lng]) => [lng, lat]) as [number, number][];

      const color = getActivityColor(
        selectedActivity.type,
        selectedActivity.distance
      );

      // Fit bounds
      const bounds = new mapboxgl.LngLatBounds();
      coords.forEach((c) => bounds.extend(c));
      map.current.fitBounds(bounds, { padding: 40, maxZoom: 15 });

      // Background route (full, semi-transparent)
      map.current.addSource('selected-bg', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords },
        },
      });
      map.current.addLayer({
        id: 'selected-bg',
        type: 'line',
        source: 'selected-bg',
        paint: { 'line-color': color, 'line-width': 2, 'line-opacity': 0.15 },
      });

      // Animated route
      map.current.addSource('selected', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: [coords[0]] },
        },
      });
      map.current.addLayer({
        id: 'selected',
        type: 'line',
        source: 'selected',
        paint: { 'line-color': color, 'line-width': 2.5, 'line-opacity': 0.9 },
      });

      // Start/end markers
      addStartEndMarkers(coords);

      // Animate
      animatorRef.current = new RouteAnimator(
        coords,
        (pts) => {
          try {
            const src = map.current?.getSource('selected');
            if (src && pts.length > 0) {
              (src as mapboxgl.GeoJSONSource).setData({
                type: 'Feature',
                properties: {},
                geometry: { type: 'LineString', coordinates: pts },
              });
            }
          } catch {
            /* ignore */
          }
        },
        () => {}
      );
      setTimeout(() => animatorRef.current?.start(), 200);
      return;
    }

    // Show all routes
    const features = activities
      .filter((a) => a.summary_polyline)
      .map((a) => ({
        type: 'Feature' as const,
        properties: { type: a.type },
        geometry: {
          type: 'LineString' as const,
          coordinates: polyline
            .decode(a.summary_polyline!)
            .map(([lat, lng]) => [lng, lat]),
        },
      }));

    if (features.length === 0) return;

    map.current.addSource('routes', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features },
    });
    map.current.addLayer({
      id: 'routes',
      type: 'line',
      source: 'routes',
      paint: {
        'line-color': [
          'match',
          ['get', 'type'],
          'Run',
          '#f97316',
          'Ride',
          '#3b82f6',
          '#a855f7',
        ],
        'line-width': 1.5,
        'line-opacity': 0.6,
      },
    });

    // Fit bounds
    const allCoords = features
      .map((f) => f.geometry.coordinates[0] as [number, number])
      .filter(Boolean);
    if (allCoords.length > 0) {
      const trimCount = Math.floor(allCoords.length * 0.1);
      const lngs = allCoords.map((c) => c[0]).sort((a, b) => a - b);
      const lats = allCoords.map((c) => c[1]).sort((a, b) => a - b);
      map.current.fitBounds(
        new mapboxgl.LngLatBounds(
          [lngs[trimCount], lats[trimCount]],
          [lngs[lngs.length - 1 - trimCount], lats[lats.length - 1 - trimCount]]
        ),
        { padding: 30, maxZoom: 13 }
      );
    }
  }, [activities, selectedActivity, clearMarkers, addStartEndMarkers]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Set access token based on provider
    const accessToken = getMapAccessToken();
    mapboxgl.accessToken = accessToken || 'pk.placeholder';

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style,
      center: [121.4, 31.2],
      zoom: 10,
      language: DEFAULT_LOCALE === 'zh' ? 'zh' : 'en',
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.current.on('style.load', () => {
      updateRoutes();
    });
    map.current.on('load', () => {
      map.current?.resize();
      // Delay setLanguage to ensure style is fully loaded
      setTimeout(() => {
        try {
          map.current?.setLanguage('zh');
        } catch {
          /* ignore */
        }
      }, 500);
      updateRoutes();
    });

    resizeObserverRef.current = new ResizeObserver(() => map.current?.resize());
    resizeObserverRef.current.observe(mapContainer.current);

    return () => {
      if (animatorRef.current) animatorRef.current.stop();
      clearMarkers();
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
      map.current?.remove();
      map.current = null;
    };
  }, [dark]);

  useEffect(() => {
    if (!map.current) return;
    if (map.current.isStyleLoaded()) updateRoutes();
    else map.current.once('style.load', () => updateRoutes());
  }, [activities, selectedActivity, updateRoutes]);

  useEffect(() => {
    if (map.current && style) map.current.setStyle(style);
  }, [style]);

  return (
    <div className="relative h-[280px] overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]">
      {selectedActivity && (
        <button
          onClick={onClearSelection}
          className="absolute top-3 left-3 z-10 flex items-center gap-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-medium shadow-md transition-colors hover:bg-[var(--color-bg)]"
        >
          <svg
            className="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Overview
        </button>
      )}
      <div ref={mapContainer} className="h-full w-full" />
    </div>
  );
}
