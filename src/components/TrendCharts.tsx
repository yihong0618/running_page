import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Scatter,
  Line,
  ComposedChart,
} from 'recharts'
import { useMemo } from 'react'
import type { Activity } from '../types'
import { useLocale } from '../hooks/useLocale'

interface TrendChartsProps {
  activities: Activity[]
}

export function TrendCharts({ activities }: TrendChartsProps) {
  const { locale } = useLocale()
  const monthlyData = useMemo(() => {
    const map = new Map<string, { run: number; ride: number }>()
    for (const a of activities) {
      const month = a.start_date_local.slice(0, 7) // YYYY-MM
      const cur = map.get(month) || { run: 0, ride: 0 }
      if (a.type === 'Run') cur.run += a.distance / 1000
      else cur.ride += a.distance / 1000
      map.set(month, cur)
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, data]) => ({
        month: month.slice(5), // MM
        run: Math.round(data.run),
        ride: Math.round(data.ride),
      }))
  }, [activities])

  const paceData = useMemo(() => {
    return activities
      .filter((a) => a.average_speed > 0)
      .sort(
        (a, b) =>
          new Date(a.start_date_local).getTime() -
          new Date(b.start_date_local).getTime()
      )
      .map((a) => ({
        date: a.start_date_local.slice(5, 10),
        pace: Number((a.average_speed * 3.6).toFixed(1)),
        type: a.type,
      }))
  }, [activities])

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      {/* Monthly distance */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5">
        <h3 className="text-base font-semibold mb-4">{locale === 'zh' ? '月度距离' : 'Monthly Distance'}</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="month" stroke="var(--color-muted)" fontSize={12} />
            <YAxis stroke="var(--color-muted)" fontSize={12} />
            <Tooltip />
            <Bar dataKey="run" stackId="a" fill="#f97316" name={locale === 'zh' ? '跑步 (km)' : 'Run (km)'} />
            <Bar dataKey="ride" stackId="a" fill="#3b82f6" name={locale === 'zh' ? '骑行 (km)' : 'Ride (km)'} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Speed trend */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5">
        <h3 className="text-base font-semibold mb-4">{locale === 'zh' ? '速度趋势' : 'Speed Trend'}</h3>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={paceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="date" stroke="var(--color-muted)" fontSize={12} />
            <YAxis stroke="var(--color-muted)" fontSize={12} />
            <Tooltip />
            <Scatter dataKey="pace" fill="var(--color-all)" name={locale === 'zh' ? '速度 (km/h)' : 'Speed (km/h)'} />
            <Line
              dataKey="pace"
              stroke="var(--color-all)"
              dot={false}
              strokeWidth={2}
              opacity={0.5}
              name={locale === 'zh' ? '趋势' : 'Trend'}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
