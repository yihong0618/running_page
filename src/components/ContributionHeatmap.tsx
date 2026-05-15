import { useMemo, useState } from 'react'
import type { Activity, SportFilter } from '../types'
import { getAvailableYears, formatDistance, parseMovingTime, formatPace } from '../hooks/useActivities'
import { useLocale } from '../hooks/useLocale'

interface HeatmapProps {
  activities: Activity[]
  year: number
  filter: SportFilter
  onSelectActivity?: (a: Activity | null) => void
}

function getColor(distance: number, max: number, filter: SportFilter): string {
  if (distance === 0) return 'var(--color-border)'
  const ratio = Math.min(distance / max, 1)
  const level = Math.ceil(ratio * 4)

  const colors = {
    all: ['#3b0764', '#7c3aed', '#a855f7', '#c084fc', '#e9d5ff'],
    Run: ['#431407', '#c2410c', '#f97316', '#fb923c', '#fed7aa'],
    Ride: ['#1e3a5f', '#1d4ed8', '#3b82f6', '#60a5fa', '#bfdbfe'],
  }
  return colors[filter][4 - level] || colors[filter][0]
}

export function ContributionHeatmap({ activities, year: defaultYear, filter, onSelectActivity }: HeatmapProps) {
  const { t, locale } = useLocale()
  const allYears = getAvailableYears(activities)
  const [selectedYear, setSelectedYear] = useState<number | 'all'>(defaultYear)

  // Build heatmap data for a single year
  function buildYearGrid(yr: number, acts: Activity[]) {
    const yearActivities = acts.filter((a) => {
      const d = new Date(a.start_date_local)
      return d.getFullYear() === yr
    })

    // Stats
    const totalDist = yearActivities.reduce((s, a) => s + a.distance, 0)
    const totalTime = yearActivities.reduce((s, a) => s + parseMovingTime(a.moving_time), 0)
    const runs = yearActivities.filter((a) => a.type === 'Run')
    const avgPace = runs.length > 0 ? runs.reduce((s, a) => s + a.average_speed, 0) / runs.length : 0

    const dayMap = new Map<string, number>()
    const dayActivitiesMap = new Map<string, Activity[]>()
    for (const a of yearActivities) {
      const day = a.start_date_local.slice(0, 10)
      dayMap.set(day, (dayMap.get(day) || 0) + a.distance)
      const arr = dayActivitiesMap.get(day) || []
      arr.push(a)
      dayActivitiesMap.set(day, arr)
    }

    const maxDist = Math.max(...dayMap.values(), 1)

    const startDate = new Date(yr, 0, 1)
    const startDay = startDate.getDay()
    const grid: { date: string; distance: number; activities: Activity[] }[][] = []
    const monthPositions: { label: string; weekIdx: number }[] = []

    let currentMonth = -1
    const endDate = new Date(yr, 11, 31)
    const totalDays = Math.round((endDate.getTime() - startDate.getTime()) / 86400000) + 1

    for (let d = 0; d < totalDays; d++) {
      const date = new Date(yr, 0, 1 + d)
      const weekIdx = Math.floor((d + startDay) / 7)
      while (grid.length <= weekIdx) grid.push([])

      const key = `${yr}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      grid[weekIdx].push({ date: key, distance: dayMap.get(key) || 0, activities: dayActivitiesMap.get(key) || [] })

      if (date.getMonth() !== currentMonth) {
        currentMonth = date.getMonth()
        monthPositions.push({ label: `${currentMonth + 1}`, weekIdx })
      }
    }

    return { grid, max: maxDist, monthPositions, stats: { count: yearActivities.length, distance: totalDist, time: totalTime, pace: avgPace } }
  }

  const yearData = useMemo(() => {
    if (selectedYear === 'all') {
      return allYears.map((yr) => ({ year: yr, ...buildYearGrid(yr, activities) }))
    }
    return [{ year: selectedYear, ...buildYearGrid(selectedYear, activities) }]
  }, [activities, selectedYear, filter, allYears])

  const dayLabels = locale === 'zh' ? ['', '一', '', '三', '', '五', ''] : ['', 'M', '', 'W', '', 'F', '']

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 overflow-x-auto">
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      {/* Header with year selector */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          {filter === 'Run' ? (locale === 'zh' ? '跑步热力图' : 'Run Heatmap')
            : filter === 'Ride' ? (locale === 'zh' ? '骑行热力图' : 'Ride Heatmap')
            : t('heatmapTitle')}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedYear('all')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
              selectedYear === 'all'
                ? 'bg-[var(--color-accent)] text-white'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            ALL
          </button>
          {allYears.map((y) => (
            <button
              key={y}
              onClick={() => setSelectedYear(y)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                selectedYear === y
                  ? 'bg-[var(--color-accent)] text-white'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {y}
            </button>
          ))}
        </div>
      </div>


      {/* Year grids */}
      <div className="space-y-6" key={selectedYear}>
        {yearData.map(({ year: yr, grid, max, monthPositions, stats }, idx) => (
          <div
            key={yr}
            className="animate-[fadeSlideIn_0.3s_ease-out_both]"
            style={{ animationDelay: `${idx * 80}ms` }}
          >
            {selectedYear === 'all' && (
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[var(--color-muted)]">{yr}</span>
                <span className="text-xs text-[var(--color-muted)] font-mono flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    {stats.count} {locale === 'zh' ? '次' : 'acts'}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                    {formatDistance(stats.distance)} km
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    {(stats.time / 3600).toFixed(0)}h
                  </span>
                  {filter === 'Run' && stats.pace > 0 && <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
                    {formatPace(stats.pace)}
                  </span>}
                </span>
              </div>
            )}

            {/* Month labels row */}
            <div className="flex ml-5">
              {monthPositions.map((m, i) => {
                const nextStart = monthPositions[i + 1]?.weekIdx ?? grid.length
                const span = nextStart - m.weekIdx
                return (
                  <div
                    key={i}
                    className="text-xs text-[var(--color-muted)]"
                    style={{ width: `${span * 14}px`, minWidth: `${span * 14}px` }}
                  >
                    {locale === 'zh' ? `${m.label}月` : ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][Number(m.label) - 1]}
                  </div>
                )
              })}
            </div>

            {/* Grid */}
            <div className="flex gap-[3px] mt-1">
              {/* Day labels */}
              <div className="flex flex-col gap-[3px] mr-1">
                {dayLabels.map((d, i) => (
                  <div key={i} className="w-3 h-3 flex items-center justify-center text-[10px] text-[var(--color-muted)]">
                    {d}
                  </div>
                ))}
              </div>

              {/* Weeks */}
              {grid.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-[3px]">
                  {week.map((day, di) => (
                    <div
                      key={di}
                      className="w-3 h-3 rounded-sm transition-colors hover:ring-1 hover:ring-[var(--color-muted)] cursor-pointer"
                      style={{ backgroundColor: getColor(day.distance, max, filter) }}
                      title={`${day.date}: ${(day.distance / 1000).toFixed(1)} km`}
                      onClick={() => {
                        if (day.activities.length > 0) onSelectActivity?.(day.activities[0])
                      }}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-1.5 mt-3 text-xs text-[var(--color-muted)]">
        <span>{t('less')}</span>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <div
            key={i}
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: getColor(ratio * (yearData[0]?.max || 1), yearData[0]?.max || 1, filter) }}
          />
        ))}
        <span>{t('more')}</span>
      </div>

      {/* Stats summary below */}
      {selectedYear === 'all' && (
        <div className="mt-4 pt-4 border-t border-[var(--color-border)] grid grid-cols-4 gap-4 text-center text-sm">
          <div>
            <p className="text-[var(--color-muted)] text-xs">{locale === 'zh' ? '活动' : 'Runs'}</p>
            <p className="font-bold font-mono">{activities.length}</p>
          </div>
          <div>
            <p className="text-[var(--color-muted)] text-xs">{locale === 'zh' ? '距离' : 'Dist'}</p>
            <p className="font-bold font-mono">{formatDistance(activities.reduce((s, a) => s + a.distance, 0))} km</p>
          </div>
          <div>
            <p className="text-[var(--color-muted)] text-xs">{locale === 'zh' ? '时间' : 'Time'}</p>
            <p className="font-bold font-mono">{(activities.reduce((s, a) => s + parseMovingTime(a.moving_time), 0) / 3600).toFixed(0)}h</p>
          </div>
          <div>
            <p className="text-[var(--color-muted)] text-xs">{locale === 'zh' ? '均配速' : 'Pace'}</p>
            <p className="font-bold font-mono">{(() => { const runs = activities.filter(a => a.type === 'Run' && a.average_speed > 0); return runs.length > 0 ? formatPace(runs.reduce((s, a) => s + a.average_speed, 0) / runs.length) : '--' })()}</p>
          </div>
        </div>
      )}
      {selectedYear !== 'all' && yearData[0] && (
        <div className="mt-4 pt-4 border-t border-[var(--color-border)] flex items-center justify-end gap-4 text-sm text-[var(--color-muted)]">
          <span className="font-mono flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            {yearData[0].stats.count} {locale === 'zh' ? '次' : 'acts'}
          </span>
          <span className="font-mono flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
            {formatDistance(yearData[0].stats.distance)} km
          </span>
          <span className="font-mono flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            {(yearData[0].stats.time / 3600).toFixed(0)}h
          </span>
          {filter === 'Run' && yearData[0].stats.pace > 0 && <span className="font-mono flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
            {formatPace(yearData[0].stats.pace)}
          </span>}
        </div>
      )}
    </div>
  )
}
