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
  const [hoveredDay, setHoveredDay] = useState<number | null>(null)

  const { days, monthDistance, monthCount } = useMemo(() => {
    const firstDaySun = new Date(viewYear, viewMonth, 1).getDay() // 0=Sun
    const firstDay = (firstDaySun + 6) % 7 // convert to Mon=0
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()

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

  // 4 tiers: returns px size of circle
  const getCircleSize = (dist: number): number => {
    if (!dist) return 0
    const km = dist / 1000
    if (km < 5) return 20
    if (km < 10) return 26
    if (km < 20) return 32
    return 38
  }

  const dayNames = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
  const monthStr = `${String(viewMonth + 1).padStart(2, '0')}/${viewYear}`

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-4 w-full min-w-0">
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
          <div key={i} className="text-center text-xs text-[var(--color-muted)] py-1">{d}</div>
        ))}
      </div>

      {/* Calendar grid — fixed height so 5-row and 6-row months are identical */}
      <div className="grid grid-cols-7 gap-0.5" style={{ height: '240px', gridAutoRows: '1fr' }}>
        {days.map((d, i) => {
          const circleSize = getCircleSize(d.distance)
          const isHovered = hoveredDay === i && d.distance > 0
          return (
            <div
              key={i}
              onClick={() => { if (d.activities.length > 0) onSelectActivity(d.activities[0]) }}
              onMouseEnter={() => d.distance > 0 && setHoveredDay(i)}
              onMouseLeave={() => setHoveredDay(null)}
              className={`flex items-center justify-center relative ${
                d.day === 0 ? '' : d.activities.length > 0 ? 'cursor-pointer' : ''
              }`}
            >
              {d.day > 0 && (
                <>
                  {/* Sized circle */}
                  {circleSize > 0 && (
                    <div
                      className="absolute rounded-full bg-[var(--color-accent)]/25 transition-all duration-200"
                      style={{ width: `${circleSize}px`, height: `${circleSize}px` }}
                    />
                  )}
                  {/* Label: show km by default, show date on hover */}
                  <span className={`relative text-[10px] font-medium leading-none transition-all ${
                    isHovered
                      ? 'text-[var(--color-text)]'
                      : d.activities.length > 0
                        ? 'text-[var(--color-accent)]'
                        : 'text-[var(--color-muted)]'
                  }`}>
                    {isHovered
                      ? d.day
                      : d.activities.length > 0
                        ? `${(d.distance / 1000).toFixed(0)}k`
                        : d.day}
                  </span>
                </>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t border-[var(--color-border)] flex items-center justify-between text-xs text-[var(--color-muted)]">
        <span>{monthCount} {t('calendarActivities')}</span>
        <span>{formatDistance(monthDistance)} km</span>
      </div>
    </div>
  )
}
