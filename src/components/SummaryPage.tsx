import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Activity } from '../types';
import { useLocale } from '../hooks/useLocale';
import { formatPace } from '../hooks/useActivities';
import {
  groupSummary,
  summaryKey,
  summarize,
  summaryChart,
  type SummaryPeriod,
} from '../utils/summary';

const control =
  'rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text)]';
const panel =
  'rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 sm:p-6';
const number = (value: number) =>
  value.toLocaleString(undefined, { maximumFractionDigits: 2 });

function SummaryCard({
  activities,
  period,
  label,
  zh,
  onSelectActivity,
}: {
  activities: Activity[];
  period: SummaryPeriod;
  label: string;
  zh: boolean;
  onSelectActivity: (a: Activity) => void;
}) {
  const stats = summarize(activities);
  const chart = summaryChart(activities, period, label);
  const metrics = [
    [zh ? '活动次数' : 'Activities', String(stats.count)],
    [
      zh ? '运动时间' : 'Moving time',
      `${Math.floor(stats.seconds / 3600)}h ${Math.floor((stats.seconds % 3600) / 60)}m`,
    ],
    [
      zh ? '平均配速' : 'Average pace',
      stats.speed > 0 ? `${formatPace(stats.speed)} /km` : '—',
    ],
    [
      zh ? '平均心率' : 'Average heart rate',
      stats.heartRate ? `${Math.round(stats.heartRate)} bpm` : '—',
    ],
    [
      zh ? '最远距离' : 'Longest activity',
      `${number(stats.maxDistance / 1000)} km`,
    ],
    [
      zh ? '最快配速' : 'Fastest pace',
      stats.maxSpeed > 0 ? `${formatPace(stats.maxSpeed)} /km` : '—',
    ],
    [
      zh ? '平均距离' : 'Average distance',
      `${number(stats.distance / stats.count / 1000)} km`,
    ],
    [zh ? '累计爬升' : 'Elevation gain', `${number(stats.elevation)} m`],
  ];
  const chartUnit =
    period === 'life'
      ? zh
        ? '年'
        : 'Year'
      : period === 'year'
        ? zh
          ? '月'
          : 'Month'
        : period === 'week'
          ? zh
            ? '周一至周日'
            : 'Mon–Sun'
          : period === 'day'
            ? zh
              ? '开始时间'
              : 'Start time'
            : zh
              ? '日'
              : 'Day';
  return (
    <article className={panel}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">
          {label === 'Life'
            ? zh
              ? '全部历程 · Life'
              : 'All time · Life'
            : label}
        </h2>
        <p className="text-2xl font-semibold text-[var(--color-accent)] tabular-nums">
          {number(stats.distance / 1000)}{' '}
          <span className="text-sm font-normal text-[var(--color-muted)]">
            km
          </span>
        </p>
      </div>
      <dl className="my-5 grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-4">
        {metrics.map(([name, value]) => (
          <div key={name}>
            <dt className="text-xs text-[var(--color-muted)]">{name}</dt>
            <dd className="mt-1 text-sm font-medium tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
      <div
        role="img"
        aria-label={`${label}: ${chart.map((d) => `${d.label}: ${d.km} km`).join(', ')}`}
      >
        <div className="h-40 w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chart}
              margin={{ top: 8, right: 0, bottom: 0, left: -20 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="var(--color-border)"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="label"
                tick={{ fill: 'var(--color-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                minTickGap={12}
              />
              <YAxis
                tick={{ fill: 'var(--color-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: 'var(--color-border)', opacity: 0.3 }}
                contentStyle={{
                  background: 'var(--color-card)',
                  borderColor: 'var(--color-border)',
                  borderRadius: 8,
                  color: 'var(--color-text)',
                }}
              />
              <Bar
                dataKey="km"
                name="km"
                fill="var(--color-accent)"
                radius={[3, 3, 0, 0]}
                maxBarSize={32}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-1 text-right text-xs text-[var(--color-muted)]">
          {chartUnit} · km
        </p>
      </div>
      {period === 'day' && (
        <div className="mt-4 space-y-2 border-t border-[var(--color-border)] pt-4">
          {activities.map((a) => (
            <button
              key={a.run_id}
              className="flex w-full items-center justify-between gap-3 rounded-lg p-2 text-left text-sm hover:bg-[var(--color-bg)]"
              onClick={() => onSelectActivity(a)}
            >
              <span>
                {a.start_date_local.slice(11, 16)} · {a.name}
              </span>
              <span className="shrink-0 text-[var(--color-accent)]">
                {number(a.distance / 1000)} km ↗
              </span>
            </button>
          ))}
        </div>
      )}
    </article>
  );
}

export function SummaryPage({
  activities,
  onSelectActivity,
}: {
  activities: Activity[];
  onSelectActivity: (a: Activity) => void;
}) {
  const { locale, t } = useLocale();
  const zh = locale === 'zh';
  const [period, setPeriod] = useState<SummaryPeriod>('month');
  const [sport, setSport] = useState('all');
  const [year, setYear] = useState('all');
  const [limit, setLimit] = useState(12);
  const sports = useMemo(
    () => [...new Set(activities.map((a) => a.type))].sort(),
    [activities]
  );
  const years = useMemo(
    () =>
      [...new Set(activities.map((a) => a.start_date_local.slice(0, 4)))]
        .sort()
        .reverse(),
    [activities]
  );
  const groups = useMemo(
    () =>
      groupSummary(
        activities.filter(
          (a) =>
            (sport === 'all' || a.type === sport) &&
            (year === 'all' || summaryKeyYear(a, period) === year)
        ),
        period
      ),
    [activities, sport, year, period]
  );
  const periods: [SummaryPeriod, string][] = [
    ['year', zh ? '年' : 'Year'],
    ['month', zh ? '月' : 'Month'],
    ['week', zh ? '周' : 'Week'],
    ['day', zh ? '日' : 'Day'],
    ['life', 'Life'],
  ];
  return (
    <main className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{t('summary')}</h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {zh
              ? '按时间回看每一段运动历程。'
              : 'Your activity history, one period at a time.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="text-xs text-[var(--color-muted)]">
            {zh ? '运动类型' : 'Sport'}
            <select
              aria-label={zh ? '运动类型' : 'Sport'}
              className={`${control} ml-2`}
              value={sport}
              onChange={(e) => {
                setSport(e.target.value);
                setLimit(12);
              }}
            >
              <option value="all">{zh ? '全部运动' : 'All sports'}</option>
              {sports.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs text-[var(--color-muted)]">
            {zh ? '年份' : 'Year'}
            <select
              aria-label={zh ? '汇总年份' : 'Summary year'}
              className={`${control} ml-2`}
              value={year}
              onChange={(e) => {
                setYear(e.target.value);
                setLimit(12);
              }}
            >
              <option value="all">{zh ? '全部年份' : 'All years'}</option>
              {years.map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </label>
        </div>
      </div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div
          role="group"
          aria-label={zh ? '汇总周期' : 'Summary period'}
          className="flex gap-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-1"
        >
          {periods.map(([value, label]) => (
            <button
              key={value}
              aria-pressed={period === value}
              onClick={() => {
                setPeriod(value);
                setLimit(12);
              }}
              className={`rounded-lg px-4 py-2 text-sm ${period === value ? 'bg-[var(--color-accent)] text-[var(--color-on-accent)]' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}
            >
              {label}
            </button>
          ))}
        </div>
        <span className="text-sm text-[var(--color-muted)]">
          {groups.length} {zh ? '个周期' : 'periods'}
        </span>
      </div>
      {!groups.length ? (
        <p
          role="status"
          className={`${panel} py-16 text-center text-[var(--color-muted)]`}
        >
          {zh
            ? '这个筛选条件下暂无活动。'
            : 'No activities match these filters.'}
        </p>
      ) : (
        <div
          className={`grid min-w-0 gap-5 ${period === 'life' ? '' : 'xl:grid-cols-2'}`}
        >
          {groups.slice(0, limit).map(([key, items]) => (
            <SummaryCard
              key={key}
              label={key}
              activities={items}
              period={period}
              zh={zh}
              onSelectActivity={onSelectActivity}
            />
          ))}
        </div>
      )}
      {groups.length > limit && (
        <div className="mt-6 text-center">
          <button className={control} onClick={() => setLimit((n) => n + 12)}>
            {zh ? '加载更多' : 'Load more'} ({limit}/{groups.length})
          </button>
        </div>
      )}
    </main>
  );
}

function summaryKeyYear(activity: Activity, period: SummaryPeriod) {
  // Weekly filters use the ISO week-year, including dates across New Year.
  return summaryKey(
    activity.start_date_local,
    period === 'week' ? 'week' : 'year'
  ).slice(0, 4);
}
