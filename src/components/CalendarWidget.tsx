import { useMemo, useState } from 'react'
import type { Activity } from '../types'
import { formatDistance } from '../hooks/useActivities'
import { useLocale } from '../hooks/useLocale'

interface CalendarWidgetProps {
  activities: Activity[]
  onSelectActivity: (activity: Activity | null) => void
}

export function CalendarWidget({ activities, onSelectActivity }: CalendarWidgetProps) {
  const { t } = useLocale()
  const now = new Date()
  const [viewYear, setViewYear] = useState(now.getFullYear())
  const [viewMonth, setViewMonth] = useState(now.getMonth())

  const { days, monthDistance, monthCount } = useMemo(() => {
    const firstDay = new Date(viewYear, viewMonth, 1).getDay()
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()

    // Get activities by day
    const dayActivities = new Map<number, Activity[]>()
    for (const a of activities) {
      const d = new Date(a.start_date_local)
      if (d.getFullYear() === viewYear && d.getMonth() === viewMonth) {
        const day = d.getDate()
        const arr = dayActivities.get(day) || []
        arr.push(a)
        dayActivities.set(day, arr)
      }
    }

    let totalDist = 0
    let totalCount = 0
    for (const acts of dayActivities.values()) {
      totalCount += acts.length
      totalDist += acts.reduce((s, a) => s + a.distance, 0)
    }

    const days: { day: number; activities: Activity[]; distance: number }[] = []
    // Empty slots
    for (let i = 0; i < firstDay; i++) {
      days.push({ day: 0, activities: [], distance: 0 })
    }
    for (let d = 1; d <= daysInMonth; d++) {
      const acts = dayActivities.get(d) || []
      const dist = acts.reduce((s, a) => s + a.distance, 0)
      days.push({ day: d, activities: acts, distance: dist })
    }

    return { days, monthDistance: totalDist, monthCount: totalCount }
  }, [activities, viewYear, viewMonth])

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11) }
    else setViewMonth(viewMonth - 1)
  }
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0) }
    else setViewMonth(viewMonth + 1)
  }

  const dayNames = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
  const monthStr = `${String(viewMonth + 1).padStart(2, '0')}/${viewYear}`

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-lg font-bold">{monthStr}</span>
          <span className="text-sm text-[var(--color-muted)] ml-3">
            {formatDistance(monthDistance)} km
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="text-[var(--color-muted)] hover:text-[var(--color-text)] px-1">←</button>
          <button onClick={nextMonth} className="text-[var(--color-muted)] hover:text-[var(--color-text)] px-1">→</button>
        </div>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {dayNames.map((d, i) => (
          <div key={i} className="text-center text-xs text-[var(--color-muted)] py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {days.map((d, i) => (
          <div
            key={i}
            onClick={() => {
              if (d.activities.length > 0) onSelectActivity(d.activities[0])
            }}
            className={`aspect-square flex flex-col items-center justify-center text-xs relative transition-all ${
              d.day === 0
                ? ''
                : d.activities.length > 0
                  ? 'cursor-pointer hover:opacity-80'
                  : 'text-[var(--color-muted)]'
            }`}
          >
            {d.day > 0 && (
              <>
                {d.distance > 0 && (
                  <div className="absolute inset-1.5 rounded-full bg-[var(--color-accent)]/20" />
                )}
                <span className={`relative text-[11px] ${d.activities.length > 0 ? 'font-medium text-[var(--color-text)]' : ''}`}>
                  {d.day}
                </span>
                {d.distance > 0 && (
                  <span className="relative text-[9px] text-[var(--color-accent)] font-mono leading-tight">
                    {(d.distance / 1000).toFixed(0)}k
                  </span>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t border-[var(--color-border)] flex items-center justify-between text-xs text-[var(--color-muted)]">
        <span>{monthCount} {t('calendarActivities')}</span>
        <span>{formatDistance(monthDistance)} km</span>
      </div>
    </div>
  )
}
