import {
  useState,
  useEffect,
  useMemo,
  useRef,
  useSyncExternalStore,
  type KeyboardEvent,
} from 'react';
import type { Activity, SportFilter } from '@/types';
import { formatDuration, formatPace } from '@/hooks/useActivities';
import { useLocale } from '@/hooks/useLocale';

type PageSizeConfig = number | { mobile: number; desktop: number };

interface ActivityLogProps {
  activities: Activity[];
  years: number[];
  year: number | null;
  setYear: (y: number | null) => void;
  selectedActivity?: Activity | null;
  onSelectActivity?: (a: Activity | null) => void;
  filter?: SportFilter;
  getTitle?: (a: Activity) => string;
  /** Default 16 (upstream). Pass `{ mobile, desktop }` for responsive sizing. */
  pageSize?: PageSizeConfig;
  /** Default = upstream table. Pass `'pro'` for compact mobile/pro layout. */
  variant?: 'default' | 'pro';
}

const DEFAULT_PAGE_SIZE = 16;
const LG_MQ = '(min-width: 1024px)';
const FOCUS_RING =
  'outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]';

type DistanceFilter = 'all' | '10' | '20' | '40';

function subscribeLg(onChange: () => void) {
  const mq = window.matchMedia(LG_MQ);
  mq.addEventListener('change', onChange);
  return () => mq.removeEventListener('change', onChange);
}

function getLgSnapshot() {
  return window.matchMedia(LG_MQ).matches;
}

function getLgServerSnapshot() {
  // Vite SPA has no SSR; mobile-first avoids a large first page on phones
  // when dashboard_pro uses responsive { mobile, desktop } pageSize.
  return false;
}

function resolvePageSize(
  config: PageSizeConfig | undefined,
  isDesktop: boolean
): number {
  if (config == null) return DEFAULT_PAGE_SIZE;
  if (typeof config === 'number') return config;
  return isDesktop ? config.desktop : config.mobile;
}

function typeIcon(type: string): string {
  const icons: Record<string, string> = {
    Run: '🏃',
    Ride: '🚴',
    Hike: '🥾',
  };
  return icons[type] ?? '📌';
}

function typeLabel(type: string, t: (k: string) => string): string {
  if (type === 'Run') return t('run');
  if (type === 'Ride') return t('ride');
  if (type === 'Hike') return t('hike');
  return type;
}

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(
    target.closest('input, textarea, select, [contenteditable="true"]')
  );
}

function formatRowDate(iso: string): {
  full: string;
  ymd: string;
  time: string;
} {
  return {
    full: iso.slice(0, 16).replace('T', ' '),
    ymd: iso.slice(0, 10), // 2024-05-03
    time: iso.slice(11, 16), // 16:35
  };
}

export function ActivityLog({
  activities,
  years,
  year,
  setYear,
  selectedActivity,
  onSelectActivity,
  filter: _filter = 'all',
  getTitle,
  pageSize: pageSizeConfig,
  variant = 'default',
}: ActivityLogProps) {
  const { t, locale } = useLocale();
  const [page, setPage] = useState(0);
  const needsResponsive =
    pageSizeConfig != null && typeof pageSizeConfig === 'object';
  const isDesktop = useSyncExternalStore(
    needsResponsive ? subscribeLg : () => () => {},
    needsResponsive ? getLgSnapshot : () => true,
    getLgServerSnapshot
  );
  const pageSize = resolvePageSize(pageSizeConfig, isDesktop);
  const [distFilter, setDistFilter] = useState<DistanceFilter>('all');
  const prevSelectedIdRef = useRef<Activity['run_id'] | null>(null);
  const pendingYearSelectRef = useRef(false);
  const logRef = useRef<HTMLDivElement>(null);
  const isPro = variant === 'pro';

  const sorted = useMemo(() => {
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
    return [...distFiltered].sort(
      (a, b) =>
        new Date(b.start_date_local).getTime() -
        new Date(a.start_date_local).getTime()
    );
  }, [activities, distFilter]);

  // Keep selection in view; don't fight the user when they change distance filter.
  useEffect(() => {
    if (pendingYearSelectRef.current) {
      pendingYearSelectRef.current = false;
      onSelectActivity?.(sorted[0] ?? null);
      return;
    }
    if (!selectedActivity) {
      prevSelectedIdRef.current = null;
      return;
    }
    const id = selectedActivity.run_id;
    const isNewSelection = prevSelectedIdRef.current !== id;
    prevSelectedIdRef.current = id;

    const idx = sorted.findIndex((a) => a.run_id === id);
    if (idx >= 0) {
      setPage(Math.floor(idx / pageSize));
      return;
    }
    if (isNewSelection) {
      // Selected from map/calendar — reveal row by clearing distance filter
      if (distFilter !== 'all') setDistFilter('all');
    } else {
      // User's distance filter hid the current row — drop selection
      onSelectActivity?.(null);
    }
  }, [selectedActivity, sorted, distFilter, onSelectActivity, pageSize]);

  const yearOptions: Array<number | null> = [null, ...years];

  const totalPages = Math.ceil(sorted.length / pageSize) || 1;
  const safePage = Math.min(page, Math.max(0, totalPages - 1));
  const pageData = sorted.slice(safePage * pageSize, (safePage + 1) * pageSize);
  // When only one sport type, keep type column width but hide labels/values
  const showTypeContent = useMemo(() => {
    const types = new Set(sorted.map((a) => a.type));
    return types.size > 1;
  }, [sorted]);

  const toggleSelect = (a: Activity) => {
    const next = selectedActivity?.run_id === a.run_id ? null : a;
    onSelectActivity?.(next);
    if (next) logRef.current?.focus({ preventScroll: true });
    else logRef.current?.blur();
  };

  const handleLogKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (!selectedActivity) return;
    if (e.altKey || e.ctrlKey || e.metaKey || e.nativeEvent.isComposing) return;
    if (isTypingTarget(e.target)) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      onSelectActivity?.(null);
      logRef.current?.blur();
      return;
    }

    if (e.key === 'ArrowDown' || e.key === 'j') {
      e.preventDefault();
      const idx = sorted.findIndex((a) => a.run_id === selectedActivity.run_id);
      const next = sorted[idx + 1];
      if (next) onSelectActivity?.(next);
      return;
    }

    if (e.key === 'ArrowUp' || e.key === 'k') {
      e.preventDefault();
      const idx = sorted.findIndex((a) => a.run_id === selectedActivity.run_id);
      if (idx > 0) onSelectActivity?.(sorted[idx - 1]);
      return;
    }

    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const yi = yearOptions.findIndex((y) => y === year);
      const nextYi = e.key === 'ArrowLeft' ? yi - 1 : yi + 1;
      if (nextYi < 0 || nextYi >= yearOptions.length) return;
      pendingYearSelectRef.current = true;
      setYear(yearOptions[nextYi]);
      setPage(0);
    }
  };

  return (
    <div
      ref={logRef}
      tabIndex={-1}
      onKeyDown={handleLogKeyDown}
      className={
        isPro
          ? 'card flex min-h-0 flex-col p-4 outline-none md:p-6 lg:flex-1'
          : 'card p-6 outline-none'
      }
    >
      {/* Header */}
      <div
        className={
          isPro
            ? 'mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between'
            : 'mb-4 flex items-center justify-between'
        }
      >
        <h2 className="text-lg font-bold">{t('activityLog')}</h2>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {selectedActivity ? (
            <span className="hidden text-xs text-[var(--color-muted)] lg:inline">
              {t('keyboardHint')}
            </span>
          ) : null}
          <span className="text-sm text-[var(--color-muted)]">
            {t('showing')} {safePage * pageSize + 1}-
            {Math.min((safePage + 1) * pageSize, sorted.length)} {t('of')}{' '}
            {sorted.length}
          </span>
        </div>
      </div>

      {/* Year tabs */}
      <div
        className={
          isPro
            ? '-mx-1 mb-3 flex min-w-0 flex-nowrap items-center gap-2 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden'
            : 'mb-3 flex flex-wrap items-center gap-2'
        }
      >
        <button
          type="button"
          onClick={() => {
            setYear(null);
            setPage(0);
          }}
          className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-all ${FOCUS_RING} ${year === null ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-sunken)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
        >
          {locale === 'zh' ? '全部' : 'All'}
        </button>
        {years.map((y) => (
          <button
            type="button"
            key={y}
            onClick={() => {
              setYear(y);
              setPage(0);
            }}
            className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-all ${FOCUS_RING} ${year === y ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-sunken)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
          >
            {y}
          </button>
        ))}
      </div>

      {/* Distance filter */}
      <div
        className={
          isPro
            ? 'mb-5 flex flex-wrap items-center gap-2'
            : 'mb-5 flex items-center gap-2'
        }
      >
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
            className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-all ${distFilter === val ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-sunken)] text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {isPro ? (
        <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
          <table className="w-max min-w-full border-collapse text-sm md:w-full">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-muted)]">
                <th className="w-[5.75rem] py-0 pr-3 pb-3 pl-3 font-medium whitespace-nowrap md:w-[10.5rem] md:pr-6 md:pl-5">
                  {t('date')}
                </th>
                <th
                  className={`pr-2 pb-3 font-medium whitespace-nowrap md:w-[1%] md:pr-3 ${
                    showTypeContent ? '' : 'hidden md:table-cell'
                  }`}
                >
                  <span className={showTypeContent ? undefined : 'invisible'}>
                    {t('type')}
                  </span>
                </th>
                <th className="max-w-[5.5rem] min-w-0 pr-3 pb-3 font-medium md:w-auto md:max-w-[12rem]">
                  {t('name')}
                </th>
                <th className="pr-3 pb-3 font-medium whitespace-nowrap md:pr-4">
                  {t('distance')}
                </th>
                <th className="pr-3 pb-3 font-medium whitespace-nowrap md:pr-4">
                  {t('duration')}
                </th>
                <th className="pr-3 pb-3 font-medium whitespace-nowrap md:pr-4">
                  {t('pace')}
                </th>
                <th className="pr-3 pb-3 font-medium whitespace-nowrap md:pr-4">
                  {t('hr')}
                </th>
              </tr>
            </thead>
            <tbody>
              {pageData.map((a) => {
                const date = formatRowDate(a.start_date_local);
                return (
                  <tr
                    key={a.run_id}
                    onClick={() => toggleSelect(a)}
                    className={`cursor-pointer border-b border-[var(--color-border)]/30 transition-colors ${
                      selectedActivity?.run_id === a.run_id
                        ? 'border-l-2 border-l-[var(--color-accent)] bg-[var(--color-accent)]/10'
                        : 'hover:bg-[var(--color-bg)]'
                    }`}
                    aria-selected={selectedActivity?.run_id === a.run_id}
                  >
                    <td className="w-[5.75rem] py-3 pr-3 pl-3 text-sm text-[var(--color-muted)] md:w-[10.5rem] md:pr-6 md:pl-5 md:whitespace-nowrap">
                      <span className="flex flex-col leading-tight md:hidden">
                        <span className="text-[10px] tracking-wide opacity-70">
                          {date.ymd}
                        </span>
                        <span className="metric">{date.time}</span>
                      </span>
                      <span className="hidden whitespace-nowrap md:inline">
                        {date.full}
                      </span>
                    </td>
                    <td
                      className={`py-3 pr-2 whitespace-nowrap text-[var(--color-muted)] md:w-[1%] md:pr-3 ${
                        showTypeContent ? '' : 'hidden md:table-cell'
                      }`}
                    >
                      <span
                        className={showTypeContent ? undefined : 'invisible'}
                        aria-hidden={!showTypeContent}
                      >
                        {typeIcon(a.type)} {typeLabel(a.type, t)}
                      </span>
                    </td>
                    <td className="max-w-[5.5rem] min-w-0 truncate py-3 pr-3 md:max-w-[14rem] md:pr-4">
                      {getTitle ? getTitle(a) : a.name || t('run')}
                    </td>
                    <td className="metric py-3 pr-3 font-medium whitespace-nowrap md:pr-4">
                      {(a.distance / 1000).toFixed(1)}
                      <span className="ml-1 text-xs font-normal text-[var(--color-muted)]">
                        km
                      </span>
                    </td>
                    <td className="py-3 pr-3 whitespace-nowrap text-[var(--color-muted)] md:pr-4">
                      {formatDuration(a.moving_time)}
                    </td>
                    <td className="py-3 pr-3 whitespace-nowrap text-[var(--color-muted)] md:pr-4">
                      {formatPace(a.average_speed)}
                    </td>
                    <td className="py-3 pr-3 whitespace-nowrap text-[var(--color-muted)] md:pr-4">
                      {a.average_heartrate
                        ? Math.round(a.average_heartrate)
                        : '--'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
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
                  onClick={() => toggleSelect(a)}
                  className={`cursor-pointer border-b border-[var(--color-border)]/30 transition-colors ${
                    selectedActivity?.run_id === a.run_id
                      ? 'border-l-2 border-l-[var(--color-accent)] bg-[var(--color-accent)]/10'
                      : 'hover:bg-[var(--color-bg)]'
                  }`}
                  aria-selected={selectedActivity?.run_id === a.run_id}
                >
                  <td className="py-3 text-[var(--color-muted)]">
                    {a.start_date_local.slice(0, 16).replace('T', ' ')}
                  </td>
                  <td className="py-3">
                    <span className="text-[var(--color-muted)]">
                      {typeIcon(a.type)} {a.type}
                    </span>
                  </td>
                  <td className="py-3">
                    {getTitle ? getTitle(a) : a.name || t('run')}
                  </td>
                  <td className="metric py-3 font-medium">
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
                    {a.average_heartrate
                      ? Math.round(a.average_heartrate)
                      : '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between border-t border-[var(--color-border)] pt-4 lg:mt-auto">
        <button
          type="button"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={safePage === 0}
          aria-label={t('prevPage')}
          className={`cursor-pointer text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-30 ${FOCUS_RING}`}
        >
          ←
        </button>
        <span className="text-sm text-[var(--color-muted)]">
          {t('page')} {safePage + 1} {t('pageOf')} {totalPages} {t('pages')}
        </span>
        <button
          type="button"
          onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
          disabled={safePage >= totalPages - 1}
          aria-label={t('nextPage')}
          className={`cursor-pointer text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-30 ${FOCUS_RING}`}
        >
          →
        </button>
      </div>
    </div>
  );
}
