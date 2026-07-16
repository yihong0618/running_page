import { useState, useEffect } from 'react';
import type { Activity, SportFilter } from '../types';
import { formatDuration, formatPace } from '../hooks/useActivities';
import { useLocale } from '../hooks/useLocale';

interface ActivityLogProps {
  activities: Activity[];
  years: number[];
  year: number | null;
  setYear: (y: number | null) => void;
  selectedActivity?: Activity | null;
  onSelectActivity?: (a: Activity | null) => void;
  filter?: SportFilter;
}

const PAGE_SIZE = 16;

type DistanceFilter = 'all' | '10' | '20' | '40';

function typeIcon(type: string): string {
  const icons: Record<string, string> = {
    Run: '🏃',
  };
  return icons[type] ?? '📌';
}

export function ActivityLog({
  activities,
  years,
  year,
  setYear,
  selectedActivity,
  onSelectActivity,
  filter = 'all',
}: ActivityLogProps) {
  const { t } = useLocale();
  const [page, setPage] = useState(0);
  const [distFilter, setDistFilter] = useState<DistanceFilter>('all');

  const distFiltered = activities.filter((a) => {
    const km = a.distance / 1000;
    switch (distFilter) {
      case '10':
        return km >= 10 && km < 20;
      case '20':
        return km >= 20 && km < 40;
      case '40':
        return km >= 40;
      default:
        return true;
    }
  });

  const sorted = [...distFiltered].sort(
    (a, b) =>
      new Date(b.start_date_local).getTime() -
      new Date(a.start_date_local).getTime()
  );

  useEffect(() => {
    if (selectedActivity) {
      const idx = sorted.findIndex((a) => a.run_id === selectedActivity.run_id);
      if (idx >= 0) {
        setPage(Math.floor(idx / PAGE_SIZE));
      } else {
        setDistFilter('all');
      }
    }
    // `sorted` is in deps so the page refreshes when the list changes (year/filter switch)
    // even if the selected run_id stays the same — avoids stale closure. M6 fix.
  }, [selectedActivity?.run_id, sorted]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">{t('activityLog')}</h2>
        <span className="text-sm text-[var(--color-muted)]">
          {t('showing')} {page * PAGE_SIZE + 1}-
          {Math.min((page + 1) * PAGE_SIZE, sorted.length)} {t('of')}{' '}
          {sorted.length}
        </span>
      </div>

      {/* Year tabs */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <button
          onClick={() => {
            setYear(null);
            setPage(0);
          }}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${year === null ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
        >
          All
        </button>
        {years.map((y) => (
          <button
            key={y}
            onClick={() => {
              setYear(y);
              setPage(0);
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${year === y ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
          >
            {y}
          </button>
        ))}
      </div>

      {/* Distance filter */}
      <div className="mb-5 flex items-center gap-2">
        {(
          [
            ['all', t('all')],
            ['10', '10km+'],
            ['20', '20km+'],
            ['40', '40km+'],
          ] as [DistanceFilter, string][]
        ).map(([val, label]) => (
          <button
            key={val}
            onClick={() => {
              setDistFilter(val);
              setPage(0);
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${distFilter === val ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-muted)]">
              <th className="pb-3 font-medium">{t('date')}</th>
              <th className="pb-3 font-medium">{t('type')}</th>
              <th className="pb-3 font-medium">{t('name')}</th>
              <th className="pb-3 font-medium">{t('distance')}</th>
              <th className="pb-3 font-medium">{t('duration')}</th>
              <th className="pb-3 font-medium">{t('pace')}</th>
              <th className="pb-3 font-medium">{t('hr')}</th>
            </tr>
          </thead>
          <tbody>
            {pageData.map((a) => (
              <tr
                key={a.run_id}
                onClick={() =>
                  onSelectActivity?.(
                    selectedActivity?.run_id === a.run_id ? null : a
                  )
                }
                className={`cursor-pointer border-b border-[var(--color-border)]/30 transition-colors ${
                  selectedActivity?.run_id === a.run_id
                    ? 'border-l-2 border-l-[var(--color-accent)] bg-[var(--color-accent)]/10'
                    : 'hover:bg-[var(--color-bg)]'
                }`}
              >
                <td className="py-3 text-[var(--color-muted)]">
                  {a.start_date_local.slice(0, 16).replace('T', ' ')}
                </td>
                <td className="py-3">
                  <span className="text-[var(--color-muted)]">
                    {typeIcon(a.type)} {a.type}
                  </span>
                </td>
                <td className="py-3">{a.name || t('run')}</td>
                <td className="py-3 font-mono font-medium">
                  {(a.distance / 1000).toFixed(1)}
                  <span className="ml-1 text-xs font-normal text-[var(--color-muted)]">
                    km
                  </span>
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {formatDuration(a.moving_time)}
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {formatPace(a.average_speed)}
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {a.average_heartrate ? Math.round(a.average_heartrate) : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between border-t border-[var(--color-border)] pt-4">
        <button
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          className="text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:opacity-30"
        >
          ←
        </button>
        <span className="text-sm text-[var(--color-muted)]">
          {t('page')} {page + 1} {t('pageOf')} {totalPages} {t('pages')}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
          disabled={page >= totalPages - 1}
          className="text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:opacity-30"
        >
          →
        </button>
      </div>
    </div>
  );
}
