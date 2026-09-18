import { useMemo, useState } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { useThemeChangeCounter } from '@/themes/classic/hooks/useTheme';
import { TREND_CHART_LABELS } from '@/themes/classic/utils/const';
import { M_TO_DIST } from '@/themes/classic/utils/utils';
import type { Activity } from '@/themes/classic/utils/utils';
import styles from './style.module.css';

interface TrendChartProps {
  runs: Activity[];
}

const TrendChart = ({ runs }: TrendChartProps) => {
  const themeChangeCounter = useThemeChangeCounter();
  const [showDistance, setShowDistance] = useState(true);
  const [showPace, setShowPace] = useState(true);
  const [showHeartRate, setShowHeartRate] = useState(true);
  const [showElevation, setShowElevation] = useState(true);

  const monthlyData = useMemo(() => {
    void themeChangeCounter;
    const monthMap = new Map<
      string,
      {
        totalDistance: number;
        totalSpeed: number;
        speedCount: number;
        totalHeartRate: number;
        heartRateCount: number;
        totalElevation: number;
        count: number;
      }
    >();

    runs.forEach((run) => {
      const monthKey = run.start_date_local.slice(0, 7);
      const entry = monthMap.get(monthKey) ?? {
        totalDistance: 0,
        totalSpeed: 0,
        speedCount: 0,
        totalHeartRate: 0,
        heartRateCount: 0,
        totalElevation: 0,
        count: 0,
      };

      entry.totalDistance += run.distance / M_TO_DIST;
      entry.totalElevation += run.elevation_gain ?? 0;
      entry.count += 1;

      if (run.average_speed > 0) {
        entry.totalSpeed += run.average_speed;
        entry.speedCount += 1;
      }
      if (run.average_heartrate) {
        entry.totalHeartRate += run.average_heartrate;
        entry.heartRateCount += 1;
      }
      monthMap.set(monthKey, entry);
    });

    return Array.from(monthMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, data]) => ({
        month: month.slice(5),
        fullMonth: month,
        totalDistance: Math.round(data.totalDistance * 100) / 100,
        avgPace:
          data.speedCount > 0
            ? Math.round(
                (M_TO_DIST / 60) *
                  (1 / (data.totalSpeed / data.speedCount)) *
                  100
              ) / 100
            : null,
        avgHeartRate:
          data.heartRateCount > 0
            ? Math.round(data.totalHeartRate / data.heartRateCount)
            : null,
        totalElevationGain: Math.round(data.totalElevation * 100) / 100,
        activityCount: data.count,
      }));
  }, [runs, themeChangeCounter]);

  const chartColors = useMemo(() => {
    void themeChangeCounter;
    if (typeof window === 'undefined') {
      return {
        distance: '#e0ed5e',
        distanceBg: 'rgba(224,237,94,0.15)',
        pace: '#4dd2ff',
        heartRate: '#f56c6c',
        elevation: '#a78bfa',
        elevationBg: 'rgba(167,139,250,0.15)',
        grid: 'rgba(255,255,255,0.06)',
        text: '#d4d4d8',
      };
    }
    const isDark =
      document.documentElement.getAttribute('data-theme') !== 'light';
    return {
      distance: isDark ? '#e0ed5e' : '#0891b2',
      distanceBg: isDark ? 'rgba(224,237,94,0.12)' : 'rgba(8,145,178,0.1)',
      pace: isDark ? '#60a5fa' : '#2563eb',
      heartRate: isDark ? '#f87171' : '#dc2626',
      elevation: isDark ? '#a78bfa' : '#7c3aed',
      elevationBg: isDark ? 'rgba(167,139,250,0.12)' : 'rgba(124,58,237,0.1)',
      grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
      text: isDark ? '#a1a1aa' : '#52525b',
    };
  }, [themeChangeCounter]);

  if (runs.length === 0) {
    return (
      <div className={styles.emptyState}>{TREND_CHART_LABELS.NO_DATA}</div>
    );
  }

  const hasAnyData = showDistance || showPace || showHeartRate || showElevation;

  return (
    <div className={styles.container}>
      <div className={styles.toggles}>
        <button
          className={`${styles.toggle} ${showDistance ? styles.toggleActive : ''}`}
          style={
            showDistance
              ? {
                  backgroundColor: chartColors.distance,
                  borderColor: chartColors.distance,
                }
              : {
                  borderColor: chartColors.distance,
                  color: chartColors.distance,
                }
          }
          onClick={() => setShowDistance(!showDistance)}
        >
          {TREND_CHART_LABELS.DISTANCE}
        </button>
        <button
          className={`${styles.toggle} ${showPace ? styles.toggleActive : ''}`}
          style={
            showPace
              ? {
                  backgroundColor: chartColors.pace,
                  borderColor: chartColors.pace,
                }
              : { borderColor: chartColors.pace, color: chartColors.pace }
          }
          onClick={() => setShowPace(!showPace)}
        >
          {TREND_CHART_LABELS.PACE}
        </button>
        <button
          className={`${styles.toggle} ${showHeartRate ? styles.toggleActive : ''}`}
          style={
            showHeartRate
              ? {
                  backgroundColor: chartColors.heartRate,
                  borderColor: chartColors.heartRate,
                }
              : {
                  borderColor: chartColors.heartRate,
                  color: chartColors.heartRate,
                }
          }
          onClick={() => setShowHeartRate(!showHeartRate)}
        >
          {TREND_CHART_LABELS.HEART_RATE}
        </button>
        <button
          className={`${styles.toggle} ${showElevation ? styles.toggleActive : ''}`}
          style={
            showElevation
              ? {
                  backgroundColor: chartColors.elevation,
                  borderColor: chartColors.elevation,
                }
              : {
                  borderColor: chartColors.elevation,
                  color: chartColors.elevation,
                }
          }
          onClick={() => setShowElevation(!showElevation)}
        >
          {TREND_CHART_LABELS.ELEVATION}
        </button>
      </div>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart
            data={monthlyData}
            margin={{ top: 10, right: 10, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="distanceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={chartColors.distance}
                  stopOpacity={0.3}
                />
                <stop
                  offset="100%"
                  stopColor={chartColors.distance}
                  stopOpacity={0}
                />
              </linearGradient>
              <linearGradient
                id="elevationGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={chartColors.elevation}
                  stopOpacity={0.3}
                />
                <stop
                  offset="100%"
                  stopColor={chartColors.elevation}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={chartColors.grid}
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tick={{ fill: chartColors.text, fontSize: 11 }}
              axisLine={{ stroke: chartColors.grid }}
              tickLine={false}
              tickFormatter={(v: string) => `${v}月`}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: chartColors.text, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: chartColors.text, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-background)',
                border: '1px solid var(--color-run-row-hover-background)',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                fontSize: '13px',
              }}
              labelStyle={{
                color: 'var(--color-primary)',
                fontWeight: 600,
                marginBottom: 4,
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => (
                <span style={{ color: chartColors.text, fontSize: '12px' }}>
                  {value}
                </span>
              )}
            />
            {showDistance && (
              <Bar
                yAxisId="left"
                dataKey="totalDistance"
                fill={chartColors.distance}
                name={TREND_CHART_LABELS.DISTANCE}
                radius={[3, 3, 0, 0]}
                maxBarSize={28}
              />
            )}
            {showPace && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgPace"
                stroke={chartColors.pace}
                name={TREND_CHART_LABELS.PACE}
                strokeWidth={2.5}
                dot={false}
                connectNulls
                activeDot={{ r: 4, fill: chartColors.pace }}
              />
            )}
            {showHeartRate && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgHeartRate"
                stroke={chartColors.heartRate}
                name={TREND_CHART_LABELS.HEART_RATE}
                strokeWidth={2.5}
                dot={false}
                connectNulls
                activeDot={{ r: 4, fill: chartColors.heartRate }}
              />
            )}
            {showElevation && (
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="totalElevationGain"
                fill="url(#elevationGradient)"
                stroke={chartColors.elevation}
                name={TREND_CHART_LABELS.ELEVATION}
                strokeWidth={2}
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TrendChart;
