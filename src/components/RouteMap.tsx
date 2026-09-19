import { useCallback, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import * as polyline from '@mapbox/polyline';
import type { Activity } from '../types';
import { MAPBOX_TOKEN } from '../config';

interface RouteMapProps {
  activities: Activity[];
  selectedActivity?: Activity | null;
  dark?: boolean;
  onClearSelection?: () => void;
}

export function RouteMap({
  activities,
  selectedActivity,
  dark,
  onClearSelection,
}: RouteMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  const style =
    dark !== false
      ? 'mapbox://styles/mapbox/dark-v11'
      : 'mapbox://styles/mapbox/light-v11';

  // Declared before the effects that reference it (react-hooks/immutability).
  const updateRoutes = useCallback(() => {
    if (!mapRef.current) return;

    // Remove existing source/layer
    if (mapRef.current.getLayer('routes')) mapRef.current.removeLayer('routes');
    if (mapRef.current.getSource('routes'))
      mapRef.current.removeSource('routes');
    if (mapRef.current.getLayer('selected'))
      mapRef.current.removeLayer('selected');
    if (mapRef.current.getSource('selected'))
      mapRef.current.removeSource('selected');

    // If a single activity is selected, show only that route highlighted
    if (selectedActivity?.summary_polyline) {
      const coords = polyline
        .decode(selectedActivity.summary_polyline)
        .map(([lat, lng]) => [lng, lat]);

      mapRef.current.addSource('selected', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords },
        },
      });

      mapRef.current.addLayer({
        id: 'selected',
        type: 'line',
        source: 'selected',
        paint: {
          'line-color': selectedActivity.type === 'Run' ? '#f97316' : '#3b82f6',
          'line-width': 3,
          'line-opacity': 0.9,
        },
      });

      const bounds = new mapboxgl.LngLatBounds();
      for (const c of coords) bounds.extend(c as [number, number]);
      mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 14 });
      return;
    }

    // Otherwise show all routes
    const features = activities
      .filter((a) => a.summary_polyline)
      .map((a) => {
        const coords = polyline
          .decode(a.summary_polyline!)
          .map(([lat, lng]) => [lng, lat]);
        return {
          type: 'Feature' as const,
          properties: { type: a.type },
          geometry: {
            type: 'LineString' as const,
            coordinates: coords,
          },
        };
      });

    if (features.length === 0) return;

    mapRef.current.addSource('routes', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features,
      },
    });

    mapRef.current.addLayer({
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

    // Fit bounds to majority of routes (ignore outliers)
    // Use median-based approach: find the region where most routes are
    const allCoords: [number, number][] = [];
    for (const f of features) {
      // Use first coord of each route as representative point
      if (f.geometry.coordinates.length > 0) {
        allCoords.push(f.geometry.coordinates[0] as [number, number]);
      }
    }

    if (allCoords.length === 0) return;

    // Sort by lng and lat, take the middle 80% to exclude outliers
    const trimPct = 0.1;
    const trimCount = Math.floor(allCoords.length * trimPct);

    const lngs = allCoords.map((c) => c[0]).sort((a, b) => a - b);
    const lats = allCoords.map((c) => c[1]).sort((a, b) => a - b);

    const bounds = new mapboxgl.LngLatBounds(
      [lngs[trimCount], lats[trimCount]],
      [lngs[lngs.length - 1 - trimCount], lats[lats.length - 1 - trimCount]]
    );

    mapRef.current.fitBounds(bounds, { padding: 30, maxZoom: 13 });
  }, [activities, selectedActivity]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapRef.current) {
      mapRef.current.setStyle(style);
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style,
      center: [121.4, 31.2],
      zoom: 10,
    });

    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    mapRef.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [style]);

  useEffect(() => {
    const instance = mapRef.current;
    if (!instance) return;
    instance.on('style.load', updateRoutes);
    if (instance.isStyleLoaded()) updateRoutes();
    return () => {
      instance.off('style.load', updateRoutes);
    };
  }, [style, updateRoutes]);

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
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
