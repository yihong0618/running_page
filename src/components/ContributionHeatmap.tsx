import { memo, useMemo, useRef, useState } from 'react';
import { exportCard } from '../utils/exportCard';
import type { Activity, SportFilter } from '../types';
import {
  getAvailableYears,
  formatDistance,
  parseMovingTime,
  formatPace,
} from '../hooks/useActivities';
import { useLocale } from '../hooks/useLocale';

const MAX_VISIBLE_YEARS = 10;
const weekdayIds = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

interface HeatmapProps {
  activities: Activity[];
  year: number;
  filter: SportFilter;
  onSelectActivity?: (a: Activity | null) => void;
}

// Map any activity type to the 4 display categories
function toDisplayType(type: string): 'Run' | 'Ride' | 'Hike' | 'Training' {
  if (type === 'Run') return 'Run';
  if (type === 'Ride') return 'Ride';
  if (type === 'Hike') return 'Hike';
  return 'Training';
}

const TYPE_PALETTES: Record<string, string[]> = {
  Run: ['#fed7aa', '#fb923c', '#f97316', '#ea580c'],
  Ride: ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb'],
  Hike: ['#bbf7d0', '#4ade80', '#22c55e', '#16a34a'],
  Training: ['#fce7f3', '#f9a8d4', '#ec4899', '#db2777'],
};

// Color for single-filter modes (intensity by global max)
function getColor(distance: number, max: number, filter: SportFilter): string {
  if (distance === 0) return 'var(--color-border)';
  const level = Math.ceil(Math.min(distance / max, 1) * 4);
  const colors: Record<string, string[]> = {
    all: ['#eef2bd', '#dce68a', '#b7c64b', '#879629'],
    Run: TYPE_PALETTES.Run,
    Ride: TYPE_PALETTES.Ride,
    Hike: TYPE_PALETTES.Hike,
    Gym: ['#cffafe', '#67e8f9', '#0891b2', '#155e75'],
  };
  const palette = colors[filter] ?? colors.all;
  return palette[level - 1] ?? palette[0];
}

// Color for "all" mode: ratio is per-type (dayDist / typeMax)
function getColorAll(typeRatio: number, displayType: string): string {
  if (typeRatio === 0) return 'var(--color-border)';
  const level = Math.ceil(Math.min(typeRatio, 1) * 4);
  const palette = TYPE_PALETTES[displayType] ?? TYPE_PALETTES.Training;
  return palette[level - 1] ?? palette[0];
}

function typeLabel(type: string, locale: string): string {
  const map: Record<string, { zh: string; en: string }> = {
    Run: { zh: '跑步', en: 'Run' },
    Ride: { zh: '骑行', en: 'Ride' },
    Hike: { zh: '徒步', en: 'Hike' },
    Training: { zh: '训练', en: 'Training' },
    WeightTraining: { zh: '力量训练', en: 'Weight Training' },
    Workout: { zh: '综合训练', en: 'Workout' },
    StairStepper: { zh: '楼梯机', en: 'Stair Stepper' },
    WaterSport: { zh: '水上运动', en: 'Water Sport' },
  };
  return map[type]?.[locale as 'zh' | 'en'] ?? type;
}

// Dominant display type for a day (by distance; Training is fallback)
function dominantDisplayType(
  acts: Activity[]
): 'Run' | 'Ride' | 'Hike' | 'Training' {
  if (acts.length === 0) return 'Training';
  const sorted = [...acts].sort((a, b) => b.distance - a.distance);
  return toDisplayType(sorted[0].type);
}

function buildYearGrid(
  yr: number,
  acts: Activity[],
  isGym: boolean,
  isAll: boolean
) {
  const yearActivities = acts.filter(
    (a) => new Date(a.start_date_local).getFullYear() === yr
  );

  const totalDist = yearActivities.reduce((s, a) => s + a.distance, 0);
  const totalTime = yearActivities.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  );
  const runs = yearActivities.filter((a) => a.type === 'Run');
  // Average pace as distance-weighted mean speed (totalDistance / totalTime),
  // not an arithmetic mean of per-run speeds. M5 fix.
  const runDistance = runs.reduce((s, a) => s + a.distance, 0);
  const runTime = runs.reduce((s, a) => s + parseMovingTime(a.moving_time), 0);
  const avgPace = runTime > 0 && runDistance > 0 ? runDistance / runTime : 0;

  // Per-day totals
  const dayMap = new Map<string, number>();
  const dayTimeMap = new Map<string, number>(); // date → total seconds (for Training)
  const dayActivitiesMap = new Map<string, Activity[]>();
  for (const a of yearActivities) {
    const day = a.start_date_local.slice(0, 10);
    dayMap.set(
      day,
      (dayMap.get(day) || 0) + (isGym ? 1 : a.distance > 0 ? a.distance : 1)
    );
    dayTimeMap.set(
      day,
      (dayTimeMap.get(day) || 0) + parseMovingTime(a.moving_time)
    );
    const arr = dayActivitiesMap.get(day) || [];
    arr.push(a);
    dayActivitiesMap.set(day, arr);
  }

  // Per-type max (for "all" mode per-type intensity)
  // Training uses time (seconds), others use distance
  const typeMaxMap: Record<string, number> = {
    Run: 1,
    Ride: 1,
    Hike: 1,
    Training: 1,
  };
  if (isAll) {
    dayActivitiesMap.forEach((dayActs, day) => {
      const domType = dominantDisplayType(dayActs);
      const value =
        domType === 'Training'
          ? dayTimeMap.get(day) || 0
          : dayActs.reduce((s, a) => s + (a.distance > 0 ? a.distance : 0), 0);
      if (value > typeMaxMap[domType]) typeMaxMap[domType] = value;
    });
  }

  const maxVal = Math.max(...dayMap.values(), 1);

  const startDate = new Date(yr, 0, 1);
  const startDay = startDate.getDay();
  const grid: {
    date: string;
    distance: number;
    timeSecs: number;
    activities: Activity[];
    domType: string;
    typeRatio: number;
  }[][] = [];
  const monthPositions: { label: string; weekIdx: number }[] = [];
  let currentMonth = -1;
  const totalDays =
    Math.round(
      (new Date(yr, 11, 31).getTime() - startDate.getTime()) / 86400000
    ) + 1;

  for (let d = 0; d < totalDays; d++) {
    const date = new Date(yr, 0, 1 + d);
    const weekIdx = Math.floor((d + startDay) / 7);
    while (grid.length <= weekIdx) grid.push([]);
    const key = `${yr}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    const dayActs = dayActivitiesMap.get(key) || [];
    const dist = dayMap.get(key) || 0;
    const domType = dominantDisplayType(dayActs);
    const typeValue =
      domType === 'Training'
        ? dayTimeMap.get(key) || 0
        : dayActs.reduce((s, a) => s + (a.distance > 0 ? a.distance : 0), 0);
    const typeRatio = typeValue / (typeMaxMap[domType] ?? 1);
    grid[weekIdx].push({
      date: key,
      distance: dist,
      timeSecs: dayTimeMap.get(key) || 0,
      activities: dayActs,
      domType,
      typeRatio,
    });
    if (date.getMonth() !== currentMonth) {
      currentMonth = date.getMonth();
      monthPositions.push({ label: `${currentMonth + 1}`, weekIdx });
    }
  }

  return {
    grid,
    max: maxVal,
    monthPositions,
    stats: {
      count: yearActivities.length,
      distance: totalDist,
      time: totalTime,
      pace: avgPace,
    },
  };
}

export const ContributionHeatmap = memo(function ContributionHeatmap({
  activities,
  year: defaultYear,
  filter,
  onSelectActivity,
}: HeatmapProps) {
  const { t, locale } = useLocale();
  const allYears = useMemo(() => getAvailableYears(activities), [activities]);
  const [selectedYear, setSelectedYear] = useState<number | 'all'>(defaultYear);
  const [previousDefaultYear, setPreviousDefaultYear] = useState(defaultYear);
  // yearWindowEnd: index into allYears of the last visible year (0-based, most-recent-first)
  const [yearWindowEnd, setYearWindowEnd] = useState(
    Math.min(MAX_VISIBLE_YEARS - 1, allYears.length - 1)
  );
  const captureRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState('');
  const [exportUrl, setExportUrl] = useState('');
  const [dayActivities, setDayActivities] = useState<Activity[]>([]);

  if (previousDefaultYear !== defaultYear) {
    setPreviousDefaultYear(defaultYear);
    setSelectedYear(defaultYear);
    setDayActivities([]);
    setExportUrl('');
    setExportMessage('');
    const index = allYears.indexOf(defaultYear);
    if (index >= 0)
      setYearWindowEnd(
        Math.min(allYears.length - 1, Math.max(MAX_VISIBLE_YEARS - 1, index))
      );
  }

  const isGym = false;
  const isAll = filter === 'all';

  const yearData = useMemo(() => {
    if (selectedYear === 'all') {
      return allYears.map((yr) => ({
        year: yr,
        ...buildYearGrid(yr, activities, isGym, isAll),
      }));
    }
    return [
      {
        year: selectedYear,
        ...buildYearGrid(selectedYear, activities, isGym, isAll),
      },
    ];
  }, [activities, selectedYear, allYears, isGym, isAll]);

  const dayLabels =
    locale === 'zh'
      ? ['', '一', '', '三', '', '五', '']
      : ['', 'M', '', 'W', '', 'F', ''];

  // Which display types are present this year
  const presentDisplayTypes = useMemo(() => {
    if (!isAll) return [];
    const yearToCheck = selectedYear === 'all' ? null : selectedYear;
    const types = new Set(
      activities
        .filter(
          (a) =>
            yearToCheck === null ||
            new Date(a.start_date_local).getFullYear() === yearToCheck
        )
        .map((a) => toDisplayType(a.type))
    );
    return (['Run', 'Training'] as const).filter((t) => types.has(t));
  }, [activities, selectedYear, isAll]);

  // Gym: monthly session breakdown
  const gymMonthlyData = useMemo(() => {
    if (!isGym || selectedYear === 'all') return [];
    return Array.from({ length: 12 }, (_, m) => {
      const monthActs = activities.filter((a) => {
        const d = new Date(a.start_date_local);
        return d.getFullYear() === selectedYear && d.getMonth() === m;
      });
      const byType = Object.fromEntries([] as [string, number][]);
      return { month: m, total: monthActs.length, byType };
    });
  }, [activities, selectedYear, isGym]);

  const gymTypeColors: Record<string, string> = {
    WeightTraining: '#f97316',
    Workout: '#0e7490',
    StairStepper: '#3b82f6',
    WaterSport: '#06b6d4',
  };

  const heatmapTitle =
    filter === 'Run'
      ? locale === 'zh'
        ? '跑步热力图'
        : 'Run Heatmap'
      : t('heatmapTitle');

  const handleSelectYear = (yr: number | 'all') => {
    setExportUrl('');
    setExportMessage('');
    setSelectedYear(yr);
    setDayActivities([]);
  };

  // Visible year window
  const yearWindowStart = Math.max(0, yearWindowEnd - MAX_VISIBLE_YEARS + 1);
  const visibleYears = allYears.slice(yearWindowStart, yearWindowEnd + 1);
  const canScrollLeft = yearWindowStart > 0;
  const canScrollRight = yearWindowEnd < allYears.length - 1;

  const shiftWindow = (dir: -1 | 1) => {
    setYearWindowEnd((prev) =>
      Math.min(Math.max(prev + dir, MAX_VISIBLE_YEARS - 1), allYears.length - 1)
    );
  };

  const handleExport = async () => {
    if (!captureRef.current || exporting) return;
    setExporting(true);
    setExportMessage('');
    try {
      setExportUrl(
        await exportCard(captureRef.current, `heatmap-${selectedYear}.png`)
      );
      setExportMessage(locale === 'zh' ? '图片已生成' : 'Image ready');
    } catch (err) {
      console.error('Export failed:', err);
      setExportMessage(
        locale === 'zh' ? '导出失败，请重试' : 'Export failed. Please retry.'
      );
    } finally {
      setExporting(false);
    }
  };

  // Aggregate stats for "all" mode
  const allStats = useMemo(() => {
    if (selectedYear !== 'all') return null;
    const count = yearData.reduce((s, d) => s + d.stats.count, 0);
    const distance = yearData.reduce((s, d) => s + d.stats.distance, 0);
    const time = yearData.reduce((s, d) => s + d.stats.time, 0);
    return { count, distance, time };
  }, [yearData, selectedYear]);

  return (
    <div
      ref={captureRef}
      role="region"
      aria-label={heatmapTitle}
      className="heatmap-card overflow-x-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5"
    >
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes expandDown {
          from { opacity: 0; transform: scaleY(0.92) translateY(-8px); }
          to { opacity: 1; transform: scaleY(1) translateY(0); }
        }
        .heatmap-all-years {
          transform-origin: top center;
          animation: expandDown 0.38s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .heatmap-year-row {
          animation: fadeSlideIn 0.32s ease-out both;
        }
        .exporting,
        .exporting *,
        .exporting *::before,
        .exporting *::after {
          animation: none !important;
          transition: none !important;
        }
      `}</style>

      {/* Header */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">{heatmapTitle}</h2>
        <div className="flex flex-wrap items-center gap-1.5">
          {/* ALL button */}
          <button
            aria-pressed={selectedYear === 'all'}
            onClick={() => handleSelectYear('all')}
            className={`rounded px-2.5 py-1 text-xs font-medium transition-all ${
              selectedYear === 'all'
                ? 'bg-[var(--color-accent)] text-[var(--color-on-accent)]'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {locale === 'zh' ? '全部' : 'ALL'}
          </button>

          <span className="h-3 w-px bg-[var(--color-border)]" />

          {/* Left arrow */}
          <button
            aria-label={
              locale === 'zh' ? '较新的热力图年份' : 'Newer heatmap years'
            }
            onClick={() => shiftWindow(-1)}
            disabled={!canScrollLeft}
            className="flex h-5 w-5 items-center justify-center rounded text-[var(--color-muted)] transition-all hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-20"
          >
            <svg
              className="h-3 w-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>

          {/* Visible year buttons */}
          {visibleYears.map((y) => (
            <button
              key={y}
              aria-pressed={selectedYear === y}
              onClick={() => handleSelectYear(y)}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-all ${
                selectedYear === y
                  ? 'bg-[var(--color-accent)] text-[var(--color-on-accent)]'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {y}
            </button>
          ))}

          {/* Right arrow */}
          <button
            aria-label={
              locale === 'zh' ? '较早的热力图年份' : 'Older heatmap years'
            }
            onClick={() => shiftWindow(1)}
            disabled={!canScrollRight}
            className="flex h-5 w-5 items-center justify-center rounded text-[var(--color-muted)] transition-all hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-20"
          >
            <svg
              className="h-3 w-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>

          <span className="h-3 w-px bg-[var(--color-border)]" />

          {/* Export button */}
          <button
            onClick={handleExport}
            disabled={exporting}
            data-export-hidden
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

      <p
        data-export-hidden
        className="heatmap-scroll-hint mb-2 text-xs text-[var(--color-muted)]"
      >
        {locale === 'zh' ? '左右滑动查看全年' : 'Swipe to see the full year'}
      </p>
      {/* Year grid(s) */}
      <div
        className={
          selectedYear === 'all' ? 'heatmap-all-years space-y-8' : 'space-y-6'
        }
        key={String(selectedYear)}
      >
        {yearData.map(({ year: yr, grid, max, monthPositions, stats }, idx) => (
          <div
            key={yr}
            className="heatmap-year-row min-w-[810px]"
            style={{ animationDelay: `${idx * 60}ms` }}
          >
            {/* Year label when showing all */}
            {selectedYear === 'all' && (
              <div className="mb-2 flex items-center gap-2">
                <span className="text-xs font-semibold text-[var(--color-accent)]">
                  {yr}
                </span>
                <span className="text-xs text-[var(--color-muted)]">
                  {stats.count} {locale === 'zh' ? '次' : 'sessions'}
                  {!isGym && ` · ${formatDistance(stats.distance)} km`}
                </span>
              </div>
            )}
            <div className="ml-5 flex">
              {monthPositions.map((m, i) => {
                const nextStart = monthPositions[i + 1]?.weekIdx ?? grid.length;
                const span = nextStart - m.weekIdx;
                return (
                  <div
                    key={m.label}
                    className="text-xs text-[var(--color-muted)]"
                    style={{
                      width: `${span * 14}px`,
                      minWidth: `${span * 14}px`,
                    }}
                  >
                    {locale === 'zh'
                      ? `${m.label}月`
                      : [
                          'Jan',
                          'Feb',
                          'Mar',
                          'Apr',
                          'May',
                          'Jun',
                          'Jul',
                          'Aug',
                          'Sep',
                          'Oct',
                          'Nov',
                          'Dec',
                        ][Number(m.label) - 1]}
                  </div>
                );
              })}
            </div>
            <div className="mt-1 flex gap-[3px]">
              <div className="mr-1 flex flex-col gap-[3px]">
                {dayLabels.map((d, i) => (
                  <div
                    key={weekdayIds[i]}
                    className="flex h-3 w-3 items-center justify-center text-[10px] text-[var(--color-muted)]"
                  >
                    {d}
                  </div>
                ))}
              </div>
              {grid.map((week) => (
                <div key={week[0].date} className="flex flex-col gap-[3px]">
                  {week.map((day) => {
                    const bgColor =
                      day.distance === 0
                        ? 'var(--color-border)'
                        : isAll
                          ? getColorAll(day.typeRatio, day.domType)
                          : getColor(day.distance, max, filter);
                    const titleText =
                      day.activities.length === 0
                        ? day.date
                        : isGym
                          ? `${day.date}: ${day.distance} session(s)`
                          : day.domType === 'Training'
                            ? `${day.date}: ${Math.round(day.timeSecs / 60)}min`
                            : `${day.date}: ${(day.activities.reduce((s, a) => s + a.distance, 0) / 1000).toFixed(1)} km`;
                    return (
                      <button
                        type="button"
                        disabled={!day.activities.length}
                        aria-label={titleText}
                        key={day.date}
                        className="heatmap-day h-3 w-3 shrink-0 rounded-sm transition-colors hover:ring-1 hover:ring-[var(--color-muted)]"
                        style={{ backgroundColor: bgColor }}
                        title={titleText}
                        onClick={() => {
                          setDayActivities(day.activities);
                          if (day.activities.length === 1)
                            onSelectActivity?.(day.activities[0]);
                        }}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {exportMessage && (
        <p
          role="status"
          data-export-hidden
          className="mt-3 text-xs text-[var(--color-muted)]"
        >
          {exportMessage}
          {exportUrl && (
            <a
              href={exportUrl}
              download={`heatmap-${selectedYear}.png`}
              className="ml-3 underline"
            >
              {locale === 'zh' ? '下载图片' : 'Download image'}
            </a>
          )}
        </p>
      )}
      {dayActivities.length > 0 && (
        <div
          data-export-hidden
          className="mt-3 flex flex-wrap items-center gap-2 border-t border-[var(--color-border)] pt-3"
        >
          <span className="text-xs text-[var(--color-muted)]">
            {dayActivities[0].start_date_local.slice(0, 10)}
          </span>
          {dayActivities.map((activity) => (
            <button
              key={activity.run_id}
              className="rounded-md border border-[var(--color-border)] px-2 text-xs hover:bg-[var(--color-bg)]"
              onClick={() => onSelectActivity?.(activity)}
            >
              {activity.start_date_local.slice(11, 16)} · {activity.name} ·{' '}
              {(activity.distance / 1000).toFixed(1)} km
            </button>
          ))}
          <button
            aria-label={
              locale === 'zh' ? '关闭当日活动' : 'Close daily activities'
            }
            className="px-2 text-sm"
            onClick={() => setDayActivities([])}
          >
            ×
          </button>
        </div>
      )}
      {/* Legend */}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {isAll ? (
          presentDisplayTypes.map((tp) => (
            <span
              key={tp}
              className="flex items-center gap-1.5 text-[11px] text-[var(--color-muted)]"
            >
              <span className="flex gap-[2px]">
                {TYPE_PALETTES[tp].map((c) => (
                  <span
                    key={c}
                    className="inline-block h-2.5 w-2.5 rounded-sm"
                    style={{ backgroundColor: c }}
                  />
                ))}
              </span>
              {typeLabel(tp, locale)}
            </span>
          ))
        ) : (
          <>
            <span className="text-xs text-[var(--color-muted)]">
              {t('less')}
            </span>
            {[0.1, 0.35, 0.6, 0.82, 1].map((ratio) => (
              <div
                key={ratio}
                className="h-3 w-3 rounded-sm"
                style={{
                  backgroundColor: getColor(
                    ratio * (yearData[0]?.max || 1),
                    yearData[0]?.max || 1,
                    filter
                  ),
                }}
              />
            ))}
            <span className="text-xs text-[var(--color-muted)]">
              {t('more')}
            </span>
          </>
        )}
      </div>

      {/* Stats row */}
      {selectedYear === 'all'
        ? allStats && (
            <div className="mt-4 flex items-center justify-end gap-4 border-t border-[var(--color-border)] pt-4 text-sm text-[var(--color-muted)]">
              <span className="mr-auto text-xs text-[var(--color-muted)]">
                {locale === 'zh' ? '全部年份汇总' : 'All-time total'}
              </span>
              <span className="flex items-center gap-1 font-mono">
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                {allStats.count} {locale === 'zh' ? '次' : 'sessions'}
              </span>
              <span className="flex items-center gap-1 font-mono">
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
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {(allStats.time / 3600).toFixed(0)}h
              </span>
              {!isGym && (
                <span className="flex items-center gap-1 font-mono">
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
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    />
                  </svg>
                  {formatDistance(allStats.distance)} km
                </span>
              )}
            </div>
          )
        : yearData[0] && (
            <div className="mt-4 flex items-center justify-end gap-4 border-t border-[var(--color-border)] pt-4 text-sm text-[var(--color-muted)]">
              <span className="flex items-center gap-1 font-mono">
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                {yearData[0].stats.count} {locale === 'zh' ? '次' : 'sessions'}
              </span>
              <span className="flex items-center gap-1 font-mono">
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
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {(yearData[0].stats.time / 3600).toFixed(0)}h
              </span>
              {!isGym && (
                <span className="flex items-center gap-1 font-mono">
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
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    />
                  </svg>
                  {formatDistance(yearData[0].stats.distance)} km
                </span>
              )}
              {filter === 'Run' && yearData[0].stats.pace > 0 && (
                <span className="flex items-center gap-1 font-mono">
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
                      d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                    />
                  </svg>
                  {formatPace(yearData[0].stats.pace)}
                </span>
              )}
            </div>
          )}

      {/* Gym: monthly frequency bars */}
      {isGym && gymMonthlyData.length > 0 && (
        <div className="mt-4 border-t border-[var(--color-border)] pt-4">
          <p className="mb-3 text-xs text-[var(--color-muted)]">
            {locale === 'zh' ? '月度频次' : 'Monthly Frequency'}
          </p>
          <div className="flex items-end gap-1.5" style={{ height: '64px' }}>
            {gymMonthlyData.map((m) => {
              const maxMonthTotal = Math.max(
                ...gymMonthlyData.map((x) => x.total),
                1
              );
              const barH =
                m.total > 0
                  ? Math.max(Math.round((m.total / maxMonthTotal) * 52), 6)
                  : 0;
              return (
                <div
                  key={m.month}
                  className="group flex flex-1 flex-col items-center gap-1"
                >
                  <div
                    className="flex w-full items-end justify-center"
                    style={{ height: '52px' }}
                  >
                    {m.total > 0 && (
                      <div
                        className="relative w-full overflow-hidden rounded-t-sm"
                        style={{ height: `${barH}px` }}
                      >
                        {([] as string[])
                          .filter(
                            (t) => (m.byType as Record<string, number>)[t] > 0
                          )
                          .map((t) => {
                            const segPct =
                              ((m.byType as Record<string, number>)[t] /
                                m.total) *
                              100;
                            return (
                              <div
                                key={t}
                                className="w-full"
                                style={{
                                  height: `${segPct}%`,
                                  backgroundColor: gymTypeColors[t],
                                }}
                              />
                            );
                          })}
                        <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[8px] whitespace-nowrap text-[var(--color-accent)] opacity-0 transition-opacity group-hover:opacity-100">
                          {m.total}
                        </span>
                      </div>
                    )}
                  </div>
                  <span className="text-[9px] text-[var(--color-muted)]">
                    {
                      [
                        'J',
                        'F',
                        'M',
                        'A',
                        'M',
                        'J',
                        'J',
                        'A',
                        'S',
                        'O',
                        'N',
                        'D',
                      ][m.month]
                    }
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4">
            {([] as string[])
              .filter((t) => activities.some((a) => a.type === t))
              .map((t) => (
                <span
                  key={t}
                  className="flex items-center gap-1 text-[10px] text-[var(--color-muted)]"
                >
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-sm"
                    style={{ backgroundColor: gymTypeColors[t] }}
                  />
                  {typeLabel(t, locale)}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
});
