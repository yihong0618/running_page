import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import type { Activity } from '../types'
import { useLocale } from '../hooks/useLocale'

interface MonthlyChartProps {
  activities: Activity[]
  year: number
  onYearChange?: (year: number | null) => void
}

export function MonthlyChart({ activities, year, onYearChange }: MonthlyChartProps) {
  const { locale } = useLocale()
  const data = useMemo(() => {
    const months = Array.from({ length: 12 }, (_, i) => ({
      month: locale === 'zh' ? `${i + 1}月` : ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i],
      distance: 0,
    }))

    for (const a of activities) {
      const d = new Date(a.start_date_local)
      if (d.getFullYear() === year) {
        months[d.getMonth()].distance += a.distance / 1000
      }
    }

    return months.map((m) => ({ ...m, distance: Math.round(m.distance) }))
  }, [activities, year, locale])

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold">Monthly Distance</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onYearChange?.(year - 1)}
            className="text-[var(--color-muted)] hover:text-[var(--color-text)] text-sm"
          >
            ←
          </button>
          <span
            className="text-sm font-medium cursor-pointer hover:text-[var(--color-accent)]"
            onClick={() => onYearChange?.(year)}
          >
            {year}
          </span>
          <button
            onClick={() => onYearChange?.(year + 1)}
            className="text-[var(--color-muted)] hover:text-[var(--color-text)] text-sm"
          >
            →
          </button>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="month" stroke="var(--color-muted)" fontSize={11} tickLine={false} />
          <YAxis stroke="var(--color-muted)" fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '8px',
            }}
          />
          <Bar dataKey="distance" fill="var(--color-accent)" radius={[3, 3, 0, 0]} name="km" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
