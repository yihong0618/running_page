import { useEffect, useRef, useState } from 'react';
import { toPng } from 'html-to-image';
import * as polyline from '@mapbox/polyline';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Activity } from '../types';
import {
  getAvailableYears,
  formatDistance,
  parseMovingTime,
  formatPace,
} from '../hooks/useActivities';
import { useLocale } from '../hooks/useLocale';
import { MAPBOX_TOKEN } from '../config';

type SportType = 'Run';

interface TracksPageProps {
  activities: Activity[];
  filter: string;
  onBack: () => void;
  onSelectActivity?: (a: Activity | null) => void;
}

function renderTrackSVG(summaryPolyline: string, size = 80): string {
  try {
    const coords = polyline.decode(summaryPolyline);
    if (coords.length < 2) return '';
    const lats = coords.map((c) => c[0]);
    const lngs = coords.map((c) => c[1]);
    const minLat = Math.min(...lats),
      maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs),
      maxLng = Math.max(...lngs);
    const latRange = maxLat - minLat || 0.001;
    const lngRange = maxLng - minLng || 0.001;
    const scale = Math.min((size - 8) / lngRange, (size - 8) / latRange);
    const offsetX = (size - lngRange * scale) / 2;
    const offsetY = (size - latRange * scale) / 2;
    return coords
      .map(([lat, lng]) => {
        const x = (lng - minLng) * scale + offsetX;
        const y = size - ((lat - minLat) * scale + offsetY);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  } catch {
    return '';
  }
}

function TrackThumb({
  activity,
  color,
  selected,
  onClick,
}: {
  activity: Activity;
  color: string;
  selected: boolean;
  onClick: () => void;
}) {
  const size = 80;
  const points = activity.summary_polyline
    ? renderTrackSVG(activity.summary_polyline, size)
    : '';
  if (!points) return null;
  return (
    <div
      className={`group relative cursor-pointer rounded transition-all ${selected ? 'ring-2 ring-[var(--color-accent)] ring-offset-1 ring-offset-[var(--color-bg)]' : ''}`}
      onClick={onClick}
      title={`${activity.name} — ${(activity.distance / 1000).toFixed(1)} km`}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className={`transition-opacity ${selected ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}
      >
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth={selected ? '2' : '1.5'}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function TrackMap({
  activity,
  activities,
  dark,
}: {
  activity: Activity | null;
  activities: Activity[];
  dark?: boolean;
}) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const mapReady = useRef(false);
  const activityRef = useRef(activity);
  const activitiesRef = useRef(activities);
  const style =
    dark !== false
      ? 'mapbox://styles/mapbox/dark-v11'
      : 'mapbox://styles/mapbox/light-v11';

  // Keep the latest props in refs via an effect (not during render) so the
  // stable updateRoutes callback below can read them at event time. This is
  // the React-recommended alternative to writing ref.current during render
  // (react-hooks/refs).
  useEffect(() => {
    activityRef.current = activity;
    activitiesRef.current = activities;
  });

  // Stable callback ref — always reads latest data from refs
  const updateRoutes = useRef(() => {
    const m = map.current;
    if (!m || !mapReady.current) return;
    const act = activityRef.current;
    const acts = activitiesRef.current;
    ['selected', 'all-routes'].forEach((id) => {
      if (m.getLayer(id)) m.removeLayer(id);
      if (m.getSource(id)) m.removeSource(id);
    });
    if (act?.summary_polyline) {
      const coords = polyline
        .decode(act.summary_polyline)
        .map(([lat, lng]) => [lng, lat]);
      m.addSource('selected', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords },
        },
      });
      m.addLayer({
        id: 'selected',
        type: 'line',
        source: 'selected',
        paint: {
          'line-color': getColor(act),
          'line-width': 3,
          'line-opacity': 0.9,
        },
      });
      const bounds = new mapboxgl.LngLatBounds();
      coords.forEach((c) => bounds.extend(c as [number, number]));
      m.fitBounds(bounds, { padding: 50, maxZoom: 14 });
      return;
    }
    const features = acts
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
    if (!features.length) return;
    m.addSource('all-routes', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features },
    });
    m.addLayer({
      id: 'all-routes',
      type: 'line',
      source: 'all-routes',
      paint: {
        'line-color': [
          'match',
          ['get', 'type'],
          'Run',
          '#f97316',
          'Ride',
          '#3b82f6',
          'Hike',
          '#22c55e',
          '#a855f7',
        ],
        'line-width': 1.2,
        'line-opacity': 0.5,
      },
    });
    const allCoords = features.flatMap(
      (f) => f.geometry.coordinates as [number, number][]
    );
    if (!allCoords.length) return;
    const lngs = allCoords.map((c) => c[0]).sort((a, b) => a - b);
    const lats = allCoords.map((c) => c[1]).sort((a, b) => a - b);
    const t = Math.floor(lngs.length * 0.1);
    m.fitBounds(
      new mapboxgl.LngLatBounds(
        [lngs[t], lats[t]],
        [lngs[lngs.length - 1 - t], lats[lats.length - 1 - t]]
      ),
      { padding: 30, maxZoom: 13 }
    );
  });

  // Init map once
  useEffect(() => {
    if (!mapContainer.current) return;
    if (map.current) {
      map.current.setStyle(style);
      return;
    }
    mapboxgl.accessToken = MAPBOX_TOKEN;
    mapReady.current = false;
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style,
      center: [108, 35],
      zoom: 3,
    });
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.on('style.load', () => {
      mapReady.current = true;
      updateRoutes.current();
    });
    return () => {
      map.current?.remove();
      map.current = null;
      mapReady.current = false;
    };
  }, [dark]);

  // Re-render routes when selection or data changes
  useEffect(() => {
    if (mapReady.current) updateRoutes.current();
  }, [activity, activities]);

  return <div ref={mapContainer} className="h-full w-full" />;
}

function getColor(a: Activity): string {
  if (a.type === 'Run') {
    const km = a.distance / 1000;
    return km >= 40 ? '#ef4444' : km >= 20 ? '#f97316' : '#f97316';
  }
  return '#a855f7';
}

export function TracksPage({
  activities,
  onBack,
  onSelectActivity,
}: TracksPageProps) {
  const { locale } = useLocale();
  const allYears = getAvailableYears(activities);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [sportFilter, setSportFilter] = useState<SportType | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(
    null
  );
  const [sortBy, setSortBy] = useState<'date' | 'distance'>('date');

  // Export
  const captureRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  // Year pagination
  const MAX_YEARS = 10;
  const [yearPage, setYearPage] = useState(0);
  const totalYearPages = Math.ceil(allYears.length / MAX_YEARS);
  const visibleYears = allYears.slice(
    yearPage * MAX_YEARS,
    yearPage * MAX_YEARS + MAX_YEARS
  );

  // Determine which sport types exist
  const hasSport = (t: SportType) => activities.some((a) => a.type === t);

  // Filtered base (year + sport)
  const base = activities.filter((a) => {
    if (
      selectedYear !== null &&
      new Date(a.start_date_local).getFullYear() !== selectedYear
    )
      return false;
    if (sportFilter !== null && a.type !== sportFilter) return false;
    return true;
  });

  const withPolyline = base.filter(
    (a) => a.summary_polyline && a.summary_polyline.length > 20
  );

  // Stats for left panel
  const totalDist = base.reduce((s, a) => s + a.distance, 0);
  const totalTime = base.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  );
  const runs = base.filter((a) => a.type === 'Run' && a.average_speed > 0);
  const avgPace =
    runs.length > 0
      ? runs.reduce((s, a) => s + a.average_speed, 0) / runs.length
      : 0;

  // Cluster tracks — defer heavy work
  type Cluster = { representative: Activity; count: number; color: string };
  const [clusteredTracks, setClusteredTracks] = useState<Cluster[]>([]);
  const [clustering, setClustering] = useState(true);

  useEffect(() => {
    setClustering(true);
    const id = setTimeout(() => {
      const acts = [...withPolyline].sort(
        (a, b) =>
          new Date(b.start_date_local).getTime() -
          new Date(a.start_date_local).getTime()
      );
      type Decoded = {
        start: [number, number];
        end: [number, number];
        distBucket: number;
      };
      const decoded: (Decoded | null)[] = acts.map((a) => {
        try {
          const coords = polyline.decode(a.summary_polyline!);
          if (coords.length < 2) return null;
          return {
            start: coords[0] as [number, number],
            end: coords[coords.length - 1] as [number, number],
            distBucket: Math.round(a.distance / 2000),
          };
        } catch {
          return null;
        }
      });
      const clusters: Cluster[] = [];
      const used = new Set<number>();
      for (let i = 0; i < acts.length; i++) {
        if (used.has(i)) continue;
        const di = decoded[i];
        if (!di) continue;
        let count = 1;
        for (let j = i + 1; j < acts.length; j++) {
          if (used.has(j)) continue;
          const dj = decoded[j];
          if (!dj || di.distBucket !== dj.distBucket) continue;
          const startClose =
            Math.abs(di.start[0] - dj.start[0]) < 0.005 &&
            Math.abs(di.start[1] - dj.start[1]) < 0.005;
          const endClose =
            Math.abs(di.end[0] - dj.end[0]) < 0.005 &&
            Math.abs(di.end[1] - dj.end[1]) < 0.005;
          if (startClose && endClose) {
            used.add(j);
            count++;
          }
        }
        used.add(i);
        clusters.push({
          representative: acts[i],
          count,
          color: getColor(acts[i]),
        });
      }
      setClusteredTracks(clusters);
      setClustering(false);
    }, 0);
    return () => clearTimeout(id);
  }, [withPolyline.length, selectedYear, sportFilter]);

  const handleSelectTrack = (a: Activity) => {
    setSelectedActivity((prev) => (prev?.run_id === a.run_id ? null : a));
    onSelectActivity?.(a);
  };

  const allSportTabs: { label: string; value: SportType; color: string }[] = [
    { label: locale === 'zh' ? '跑步' : 'Run', value: 'Run', color: '#f97316' },
  ];

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-6">
      {/* Top bar: back + title */}
      <div className="mb-5 flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex shrink-0 items-center gap-1.5 text-sm text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)]"
        >
          <svg
            className="h-4 w-4"
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
          {locale === 'zh' ? '返回' : 'Back'}
        </button>
        <h1 className="shrink-0 text-lg font-bold">
          {locale === 'zh' ? '轨迹墙' : 'Track Wall'}
        </h1>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[340px_1fr]">
        {/* Left: stats + map */}
        <div className="flex flex-col gap-4">
          {/* Stats card */}
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4">
            <p className="mb-3 text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
              {selectedYear ?? (locale === 'zh' ? '全部' : 'Total')}
            </p>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
                  {locale === 'zh' ? '活动' : 'Activities'}
                </p>
                <p className="font-mono text-2xl font-bold text-[var(--color-accent)]">
                  {base.length}
                </p>
              </div>
              <div>
                <p className="text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
                  {locale === 'zh' ? '距离' : 'Distance'}
                </p>
                <p className="font-mono text-2xl font-bold">
                  {formatDistance(totalDist)}{' '}
                  <span className="text-sm font-normal text-[var(--color-muted)]">
                    km
                  </span>
                </p>
              </div>
              <div>
                <p className="text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
                  {locale === 'zh' ? '时间' : 'Time'}
                </p>
                <p className="font-mono text-lg font-bold">
                  {Math.floor(totalTime / 3600)}h{' '}
                  {Math.floor((totalTime % 3600) / 60)}m
                </p>
              </div>
              {avgPace > 0 && (
                <div>
                  <p className="text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
                    {locale === 'zh' ? '均配速' : 'Avg Pace'}
                  </p>
                  <p className="font-mono text-lg font-bold">
                    {formatPace(avgPace)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Activity detail — only when a single track is selected */}
          {selectedActivity && (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-[10px] tracking-wider text-[var(--color-muted)] uppercase">
                  {locale === 'zh' ? '已选记录' : 'Selected'}
                </p>
                <button
                  onClick={() => setSelectedActivity(null)}
                  className="text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)]"
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <p className="mb-0.5 truncate text-xs font-semibold">
                {selectedActivity.name}
              </p>
              <p className="mb-2 text-[10px] text-[var(--color-muted)]">
                {new Date(selectedActivity.start_date_local).toLocaleDateString(
                  locale === 'zh' ? 'zh-CN' : 'en-US',
                  { year: 'numeric', month: 'short', day: 'numeric' }
                )}{' '}
                {new Date(selectedActivity.start_date_local).toLocaleTimeString(
                  locale === 'zh' ? 'zh-CN' : 'en-US',
                  { hour: '2-digit', minute: '2-digit' }
                )}
              </p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="text-[9px] tracking-wider text-[var(--color-muted)] uppercase">
                    {locale === 'zh' ? '距离' : 'Distance'}
                  </p>
                  <p className="font-mono text-base leading-tight font-bold">
                    {(selectedActivity.distance / 1000).toFixed(2)}{' '}
                    <span className="text-[10px] font-normal text-[var(--color-muted)]">
                      km
                    </span>
                  </p>
                </div>
                <div>
                  <p className="text-[9px] tracking-wider text-[var(--color-muted)] uppercase">
                    {locale === 'zh' ? '时间' : 'Time'}
                  </p>
                  <p className="font-mono text-base leading-tight font-bold">
                    {(() => {
                      const s = parseMovingTime(selectedActivity.moving_time);
                      return `${Math.floor(s / 3600) ? Math.floor(s / 3600) + 'h ' : ''}${Math.floor((s % 3600) / 60)}m`;
                    })()}
                  </p>
                </div>
                {selectedActivity.average_speed > 0 && (
                  <div>
                    <p className="text-[9px] tracking-wider text-[var(--color-muted)] uppercase">
                      {locale === 'zh' ? '配速' : 'Pace'}
                    </p>
                    <p className="font-mono text-base leading-tight font-bold">
                      {formatPace(selectedActivity.average_speed)}{' '}
                      <span className="text-[10px] font-normal text-[var(--color-muted)]">
                        /km
                      </span>
                    </p>
                  </div>
                )}
                {selectedActivity.elevation_gain != null &&
                  selectedActivity.elevation_gain > 0 && (
                    <div>
                      <p className="text-[9px] tracking-wider text-[var(--color-muted)] uppercase">
                        {locale === 'zh' ? '爬升' : 'Elev'}
                      </p>
                      <p className="font-mono text-base leading-tight font-bold">
                        {Math.round(selectedActivity.elevation_gain)}{' '}
                        <span className="text-[10px] font-normal text-[var(--color-muted)]">
                          m
                        </span>
                      </p>
                    </div>
                  )}
                {selectedActivity.average_heartrate != null &&
                  selectedActivity.average_heartrate > 0 && (
                    <div>
                      <p className="text-[9px] tracking-wider text-[var(--color-muted)] uppercase">
                        {locale === 'zh' ? '心率' : 'HR'}
                      </p>
                      <p className="font-mono text-base leading-tight font-bold">
                        {Math.round(selectedActivity.average_heartrate)}{' '}
                        <span className="text-[10px] font-normal text-[var(--color-muted)]">
                          bpm
                        </span>
                      </p>
                    </div>
                  )}
              </div>
            </div>
          )}

          {/* Map */}
          <div
            className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]"
            style={{ height: 260 }}
          >
            <TrackMap
              activity={selectedActivity}
              activities={withPolyline}
              dark
            />
          </div>
        </div>

        {/* Right: track grid with year filter inside */}
        <div className="min-w-0">
          <div
            ref={captureRef}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4"
          >
            {/* Year pills + sport filter */}
            <div className="mb-4 flex items-center gap-1.5 border-b border-[var(--color-border)] pb-3">
              {totalYearPages > 1 && (
                <button
                  onClick={() => setYearPage((p) => Math.max(0, p - 1))}
                  disabled={yearPage === 0}
                  className="px-1 text-base leading-none text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:opacity-30"
                >
                  ‹
                </button>
              )}
              <button
                onClick={() => setSelectedYear(null)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${selectedYear === null ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
              >
                {locale === 'zh' ? '全部' : 'All'}
              </button>
              {visibleYears.map((yr) => (
                <button
                  key={yr}
                  onClick={() =>
                    setSelectedYear(selectedYear === yr ? null : yr)
                  }
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${selectedYear === yr ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                >
                  {yr}
                </button>
              ))}
              {totalYearPages > 1 && (
                <button
                  onClick={() =>
                    setYearPage((p) => Math.min(totalYearPages - 1, p + 1))
                  }
                  disabled={yearPage === totalYearPages - 1}
                  className="px-1 text-base leading-none text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:opacity-30"
                >
                  ›
                </button>
              )}
              {/* Sport filter — right side */}
              <div className="ml-auto flex items-center gap-1.5">
                <button
                  onClick={() => setSportFilter(null)}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${sportFilter === null ? 'border-transparent bg-[var(--color-accent)] text-white' : 'border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                >
                  {locale === 'zh' ? '全部' : 'All'}
                </button>
                {allSportTabs
                  .filter((t) => hasSport(t.value))
                  .map(({ label, value, color }) => (
                    <button
                      key={value}
                      onClick={() =>
                        setSportFilter(sportFilter === value ? null : value)
                      }
                      className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${sportFilter === value ? 'border-transparent text-white' : 'border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
                      style={
                        sportFilter === value ? { backgroundColor: color } : {}
                      }
                    >
                      {label}
                    </button>
                  ))}
                <span className="mx-1 h-3 w-px bg-[var(--color-border)]" />
                <button
                  onClick={async () => {
                    if (!captureRef.current || exporting) return;
                    setExporting(true);
                    try {
                      const el = captureRef.current;
                      const prevOverflow = el.style.overflow;
                      el.style.overflow = 'visible';
                      await new Promise((resolve) =>
                        requestAnimationFrame(resolve)
                      );
                      const dataUrl = await toPng(el, {
                        pixelRatio: 2,
                        cacheBust: true,
                      });
                      el.style.overflow = prevOverflow;
                      const link = document.createElement('a');
                      const label = selectedYear ?? 'all';
                      link.download = `tracks-${label}.png`;
                      link.href = dataUrl;
                      link.click();
                    } catch (err) {
                      console.error('Export failed:', err);
                    } finally {
                      setExporting(false);
                    }
                  }}
                  disabled={exporting}
                  className="flex h-6 w-6 items-center justify-center rounded text-[var(--color-muted)] transition-all hover:text-[var(--color-text)] disabled:opacity-50"
                  title={locale === 'zh' ? '导出图片' : 'Export as image'}
                >
                  {exporting ? (
                    <svg
                      className="h-3.5 w-3.5 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  ) : (
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
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {clustering ? (
              <div className="flex flex-wrap gap-1">
                {Array.from({ length: 40 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-[80px] w-[80px] animate-pulse rounded bg-[var(--color-border)]"
                    style={{ animationDelay: `${i * 20}ms` }}
                  />
                ))}
              </div>
            ) : clusteredTracks.length === 0 ? (
              <p className="py-8 text-center text-sm text-[var(--color-muted)]">
                {locale === 'zh' ? '暂无轨迹数据' : 'No tracks found'}
              </p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {[...clusteredTracks]
                  .sort((a, b) =>
                    sortBy === 'distance'
                      ? b.representative.distance - a.representative.distance
                      : new Date(b.representative.start_date_local).getTime() -
                        new Date(a.representative.start_date_local).getTime()
                  )
                  .map(({ representative: a, count, color }) => (
                    <div key={a.run_id} className="relative">
                      <TrackThumb
                        activity={a}
                        color={color}
                        selected={selectedActivity?.run_id === a.run_id}
                        onClick={() => handleSelectTrack(a)}
                      />
                      {count > 1 && (
                        <span className="pointer-events-none absolute right-1 bottom-1 rounded bg-[var(--color-bg)]/80 px-1 py-0.5 text-[9px] leading-none font-bold text-[var(--color-muted)]">
                          ×{count}
                        </span>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* Legend + sort */}
            {!clustering && clusteredTracks.length > 0 && (
              <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-muted)]">
                {sportFilter === null || sportFilter === 'Run' ? (
                  <>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-0.5 w-3 rounded bg-[#f97316]" />
                      {locale === 'zh' ? '跑步' : 'Run'}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-0.5 w-3 rounded bg-[#ef4444]" />
                      {locale === 'zh' ? '跑步 >20km' : 'Run >20km'}
                    </span>
                  </>
                ) : null}
                {null}
                {null}
                <div className="ml-auto flex items-center gap-1">
                  <span>
                    {clusteredTracks.length}{' '}
                    {locale === 'zh' ? '条路线' : 'routes'}
                  </span>
                  <span className="mx-1.5 text-[var(--color-border)]">·</span>
                  <button
                    onClick={() => setSortBy('date')}
                    className={`transition-colors ${sortBy === 'date' ? 'font-medium text-[var(--color-text)]' : 'hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '时间' : 'Date'}
                  </button>
                  <span className="text-[var(--color-border)]">/</span>
                  <button
                    onClick={() => setSortBy('distance')}
                    className={`transition-colors ${sortBy === 'distance' ? 'font-medium text-[var(--color-text)]' : 'hover:text-[var(--color-text)]'}`}
                  >
                    {locale === 'zh' ? '距离' : 'Dist'}
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* end track grid card */}
        </div>
        {/* end right column */}
      </div>
    </div>
  );
}
