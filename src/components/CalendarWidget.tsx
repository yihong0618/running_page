import { useMemo, useState } from 'react';
import type { Activity } from '../types';
import { formatDistance } from '../hooks/useActivities';
import { useLocale } from '../hooks/useLocale';

interface CalendarWidgetProps {
  activities: Activity[];
  selectedActivity?: Activity | null;
  onSelectActivity: (activity: Activity | null) => void;
}

export function CalendarWidget({
  activities,
  selectedActivity,
  onSelectActivity,
}: CalendarWidgetProps) {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const [today] = useState(() => new Date());
  const latest = useMemo(
    () =>
      activities.reduce(
        (last, a) => (a.start_date_local > last ? a.start_date_local : last),
        ''
      ),
    [activities]
  );
  const initial = selectedActivity?.start_date_local || latest;
  const [month, setMonth] = useState(() => {
    const date = initial ? new Date(initial) : today;
    return new Date(date.getFullYear(), date.getMonth(), 1);
  });
  const [day, setDay] = useState<number | null>(() =>
    selectedActivity
      ? new Date(selectedActivity.start_date_local).getDate()
      : null
  );
  const [previousSelection, setPreviousSelection] = useState(
    selectedActivity?.run_id
  );
  if (previousSelection !== selectedActivity?.run_id) {
    setPreviousSelection(selectedActivity?.run_id);
    if (selectedActivity) {
      const date = new Date(selectedActivity.start_date_local);
      setMonth(new Date(date.getFullYear(), date.getMonth(), 1));
      setDay(date.getDate());
    }
  }
  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const byDay = useMemo(() => {
    const result = new Map<number, Activity[]>();
    for (const activity of activities) {
      const date = new Date(activity.start_date_local);
      if (date.getFullYear() === year && date.getMonth() === monthIndex) {
        const list = result.get(date.getDate()) ?? [];
        list.push(activity);
        result.set(date.getDate(), list);
      }
    }
    for (const list of result.values())
      list.sort((a, b) => a.start_date_local.localeCompare(b.start_date_local));
    return result;
  }, [activities, year, monthIndex]);
  const monthActivities = [...byDay.values()].flat();
  const distance = monthActivities.reduce((sum, a) => sum + a.distance, 0);
  const offset = (month.getDay() + 6) % 7;
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const dayActivities = day === null ? [] : (byDay.get(day) ?? []);
  const moveMonth = (delta: number) => {
    setMonth(new Date(year, monthIndex + delta, 1));
    setDay(null);
  };
  const goToDate = (date: Date) => {
    setMonth(new Date(date.getFullYear(), date.getMonth(), 1));
    setDay(null);
  };
  const monthLabel = month.toLocaleDateString(zh ? 'zh-CN' : 'en-US', {
    year: 'numeric',
    month: 'long',
  });
  return (
    <section
      aria-label={zh ? '活动日历' : 'Activity calendar'}
      className="w-full min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold">{monthLabel}</h2>
        <div className="flex items-center gap-1">
          <button
            className="rounded px-2 text-sm"
            onClick={() => moveMonth(-1)}
            aria-label={zh ? '上个月' : 'Previous month'}
          >
            ←
          </button>
          <button
            className="rounded px-2 text-sm"
            onClick={() => moveMonth(1)}
            aria-label={zh ? '下个月' : 'Next month'}
          >
            →
          </button>
        </div>
      </div>
      <div className="mb-3 flex items-center gap-2 text-xs text-[var(--color-muted)]">
        <span className="mr-auto">
          {monthActivities.length} {zh ? '次活动' : 'activities'} ·{' '}
          {formatDistance(distance)} km
        </span>
        <button
          className="rounded px-2 hover:bg-[var(--color-bg)]"
          onClick={() => goToDate(today)}
        >
          {zh ? '本月' : 'This month'}
        </button>
        {latest && (
          <button
            className="rounded px-2 hover:bg-[var(--color-bg)]"
            onClick={() => goToDate(new Date(latest))}
          >
            {zh ? '最近活动' : 'Latest'}
          </button>
        )}
      </div>
      <div className="mb-1 grid grid-cols-7 text-center text-xs text-[var(--color-muted)]">
        {(zh
          ? ['一', '二', '三', '四', '五', '六', '日']
          : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ).map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 42 }, (_, i) => {
          const number = i - offset + 1;
          if (number < 1 || number > daysInMonth)
            return <span key={i} className="h-9" />;
          const list = byDay.get(number) ?? [];
          const km = list.reduce((sum, a) => sum + a.distance, 0) / 1000;
          return (
            <button
              key={i}
              type="button"
              disabled={!list.length}
              aria-pressed={day === number}
              aria-label={`${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(number).padStart(2, '0')} · ${list.length} ${zh ? '次活动' : 'activities'} · ${km.toFixed(1)} km`}
              className={`calendar-day relative flex h-9 flex-col items-center justify-center rounded-md text-xs ${list.length ? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)] hover:bg-[var(--color-accent)]/30' : 'text-[var(--color-muted)]'} ${day === number ? 'ring-2 ring-[var(--color-accent)]' : ''}`}
              onClick={() => {
                setDay(number);
                if (list.length === 1) onSelectActivity(list[0]);
              }}
            >
              <span>{number}</span>
              {list.length > 0 && (
                <span className="text-[9px] leading-tight">
                  {km.toFixed(1)}k
                </span>
              )}
            </button>
          );
        })}
      </div>
      {day !== null && dayActivities.length > 0 && (
        <div className="mt-3 space-y-1 border-t border-[var(--color-border)] pt-3">
          <p className="mb-2 text-xs text-[var(--color-muted)]">
            {monthIndex + 1}/{day} ·{' '}
            {zh ? '选择活动查看路线' : 'Select an activity to view its route'}
          </p>
          {dayActivities.map((activity) => (
            <button
              key={activity.run_id}
              aria-pressed={selectedActivity?.run_id === activity.run_id}
              className="flex w-full items-center justify-between gap-2 rounded-md px-2 py-2 text-left text-xs hover:bg-[var(--color-bg)] aria-pressed:bg-[var(--color-accent)]/10"
              onClick={() => onSelectActivity(activity)}
            >
              <span className="min-w-0 truncate">
                {activity.start_date_local.slice(11, 16)} · {activity.name}
              </span>
              <span className="shrink-0 font-mono">
                {(activity.distance / 1000).toFixed(1)} km
              </span>
            </button>
          ))}
        </div>
      )}
      {!monthActivities.length && (
        <p className="mt-3 text-center text-xs text-[var(--color-muted)]">
          {zh ? '本月没有活动' : 'No activities this month'}
        </p>
      )}
    </section>
  );
}
