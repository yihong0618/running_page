import type { Activity, SportFilter } from '../types'
import { formatDistance, parseMovingTime } from '../hooks/useActivities'
import { useLocale } from '../hooks/useLocale'

interface StatsCardsProps {
  activities: Activity[]
  allActivities: Activity[]
  year: number | null
  filter: SportFilter
}

export function StatsCards({ activities, allActivities, year, filter }: StatsCardsProps) {
  const { t, locale } = useLocale()

  // Current year stats (for yearly goal)
  const now = new Date()
  const currentYear = year ?? now.getFullYear()
  const yearActivities = activities.filter((a) => {
    const d = new Date(a.start_date_local)
    return d.getFullYear() === currentYear
  })
  const yearDistance = yearActivities.reduce((s, a) => s + a.distance, 0)
  const yearCount = yearActivities.length
  const yearSeconds = yearActivities.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  )

  // Last year same period comparison
  const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 86400000)
  const lastYearActivities = allActivities.filter((a) => {
    const d = new Date(a.start_date_local)
    if (d.getFullYear() !== currentYear - 1) return false
    if (filter !== 'all' && a.type !== filter) return false
    const aDayOfYear = Math.floor((d.getTime() - new Date(d.getFullYear(), 0, 1).getTime()) / 86400000)
    return aDayOfYear <= dayOfYear
  })
  const lastYearDistance = lastYearActivities.reduce((s, a) => s + a.distance, 0)
  const yearDiff = yearDistance - lastYearDistance

  // Current month stats
  const monthActivities = activities.filter((a) => {
    const d = new Date(a.start_date_local)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  })
  const monthDistance = monthActivities.reduce((s, a) => s + a.distance, 0)
  const monthCount = monthActivities.length
  const monthSeconds = monthActivities.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  )

  // Last month same period comparison
  const lastMonthActivities = allActivities.filter((a) => {
    const d = new Date(a.start_date_local)
    const targetMonth = now.getMonth() === 0 ? 11 : now.getMonth() - 1
    const targetYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
    if (d.getFullYear() !== targetYear || d.getMonth() !== targetMonth) return false
    if (filter !== 'all' && a.type !== filter) return false
    return d.getDate() <= now.getDate()
  })
  const lastMonthDistance = lastMonthActivities.reduce((s, a) => s + a.distance, 0)
  const monthDiff = monthDistance - lastMonthDistance

  // Current week stats
  const dayOfWeek = now.getDay() // 0=Sun
  const weekStart = new Date(now.getTime() - dayOfWeek * 86400000)
  weekStart.setHours(0, 0, 0, 0)
  const weekActivities = activities.filter((a) => {
    const d = new Date(a.start_date_local)
    return d >= weekStart
  })
  const weekDistance = weekActivities.reduce((s, a) => s + a.distance, 0)
  const weekCount = weekActivities.length
  const weekSeconds = weekActivities.reduce((s, a) => s + parseMovingTime(a.moving_time), 0)

  // Last week same period comparison
  const lastWeekStart = new Date(weekStart.getTime() - 7 * 86400000)
  const lastWeekSamePoint = new Date(now.getTime() - 7 * 86400000)
  const lastWeekActivities = allActivities.filter((a) => {
    const d = new Date(a.start_date_local)
    if (d < lastWeekStart || d > lastWeekSamePoint) return false
    if (filter !== 'all' && a.type !== filter) return false
    return true
  })
  const lastWeekDistance = lastWeekActivities.reduce((s, a) => s + a.distance, 0)
  const weekDiff = weekDistance - lastWeekDistance

  // Streak calculation (consecutive days with activity)
  const sortedDates = [...new Set(
    activities.map((a) => a.start_date_local.slice(0, 10))
  )].sort().reverse()

  let currentStreak = 0
  if (sortedDates.length > 0) {
    const today = now.toISOString().slice(0, 10)
    const yesterday = new Date(now.getTime() - 86400000).toISOString().slice(0, 10)
    if (sortedDates[0] === today || sortedDates[0] === yesterday) {
      let expected = new Date(sortedDates[0])
      for (const dateStr of sortedDates) {
        const d = new Date(dateStr + 'T00:00:00')
        if (d.toISOString().slice(0, 10) === expected.toISOString().slice(0, 10)) {
          currentStreak++
          expected = new Date(expected.getTime() - 86400000)
        } else {
          break
        }
      }
    }
  }

  // Week streak (consecutive weeks with activity) using simple week number
  function getWeekNumber(d: Date): number {
    const start = new Date(d.getFullYear(), 0, 1)
    return Math.floor(((d.getTime() - start.getTime()) / 86400000 + start.getDay()) / 7)
  }

  const weekSet = new Set(
    activities.map((a) => {
      const d = new Date(a.start_date_local)
      return `${d.getFullYear()}-${getWeekNumber(d)}`
    })
  )

  let currentWeekStreak = 0
  {
    let d = new Date(now)
    // Check current week first
    const currKey = `${d.getFullYear()}-${getWeekNumber(d)}`
    if (weekSet.has(currKey)) {
      // Count backwards from current week
      while (true) {
        const key = `${d.getFullYear()}-${getWeekNumber(d)}`
        if (weekSet.has(key)) {
          currentWeekStreak++
          d = new Date(d.getTime() - 7 * 86400000)
        } else {
          break
        }
      }
    } else {
      // Try last week
      d = new Date(now.getTime() - 7 * 86400000)
      if (weekSet.has(`${d.getFullYear()}-${getWeekNumber(d)}`)) {
        while (true) {
          const key = `${d.getFullYear()}-${getWeekNumber(d)}`
          if (weekSet.has(key)) {
            currentWeekStreak++
            d = new Date(d.getTime() - 7 * 86400000)
          } else {
            break
          }
        }
      }
    }
  }

  // Longest streak ever
  let longestStreak = 0
  if (sortedDates.length > 0) {
    const ascending = [...sortedDates].reverse()
    let streak = 1
    for (let i = 1; i < ascending.length; i++) {
      const prev = new Date(ascending[i - 1] + 'T00:00:00')
      const curr = new Date(ascending[i] + 'T00:00:00')
      const diff = (curr.getTime() - prev.getTime()) / 86400000
      if (diff === 1) {
        streak++
      } else {
        longestStreak = Math.max(longestStreak, streak)
        streak = 1
      }
    }
    longestStreak = Math.max(longestStreak, streak)
  }

  // Longest week streak - iterate all weeks from earliest to latest
  let longestWeekStreak = 0
  {
    // Get all activity dates, find range, check each week
    if (activities.length > 0) {
      const earliest = new Date(Math.min(...activities.map(a => new Date(a.start_date_local).getTime())))
      const latest = new Date(Math.max(...activities.map(a => new Date(a.start_date_local).getTime())))
      let streak = 0
      let d = new Date(earliest)
      while (d <= latest) {
        const key = `${d.getFullYear()}-${getWeekNumber(d)}`
        if (weekSet.has(key)) {
          streak++
          longestWeekStreak = Math.max(longestWeekStreak, streak)
        } else {
          streak = 0
        }
        d = new Date(d.getTime() + 7 * 86400000)
      }
    }
  }

  const formatHours = (secs: number) => {
    const h = (secs / 3600).toFixed(1)
    return `${h}h`
  }

  const unit = filter === 'Run' ? t('runs') : filter === 'Ride' ? t('rides') : t('activities')

  return (
    <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_1fr_1.5fr] gap-4">
      {/* Yearly Goal */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
        <p className="text-xs uppercase tracking-wider text-[var(--color-muted)] mb-2 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          {t('yearlyGoal')}
        </p>
        <p className="text-3xl font-bold font-mono">
          {formatDistance(yearDistance)}
          <span className="text-base font-normal text-[var(--color-muted)] ml-1">/ 2000 km</span>
        </p>
        <div className="mt-3 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-accent)] rounded-full transition-all"
            style={{ width: `${Math.min((yearDistance / 2000000) * 100, 100)}%` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-[var(--color-muted)]">
          <span className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {yearCount} {unit}
          </span>
          <span>{formatHours(yearSeconds)}</span>
        </div>
        <p className={`mt-1.5 text-xs ${yearDiff >= 0 ? 'text-emerald-500' : 'text-red-400'}`}>
          {yearDiff >= 0 ? '↗' : '↘'} {formatDistance(Math.abs(yearDiff))} km {t('vsLastYear')}
        </p>
      </div>

      {/* Monthly Goal */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
        <p className="text-xs uppercase tracking-wider text-[var(--color-muted)] mb-2 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {t('monthlyGoal')}
        </p>
        <p className="text-3xl font-bold font-mono">
          {formatDistance(monthDistance)}
          <span className="text-base font-normal text-[var(--color-muted)] ml-1">/ 120 km</span>
        </p>
        <div className="mt-3 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-accent)] rounded-full transition-all"
            style={{ width: `${Math.min((monthDistance / 120000) * 100, 100)}%` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-[var(--color-muted)]">
          <span className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {monthCount} {unit}
          </span>
          <span>{formatHours(monthSeconds)}</span>
        </div>
        <p className={`mt-1.5 text-xs ${monthDiff >= 0 ? 'text-emerald-500' : 'text-red-400'}`}>
          {monthDiff >= 0 ? '↗' : '↘'} {formatDistance(Math.abs(monthDiff))} km {t('vsLastMonth')}
        </p>
      </div>

      {/* Weekly Goal */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
        <p className="text-xs uppercase tracking-wider text-[var(--color-muted)] mb-2 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {locale === 'zh' ? '周目标' : 'WEEKLY GOAL'}
        </p>
        <p className="text-3xl font-bold font-mono">
          {formatDistance(weekDistance)}
          <span className="text-base font-normal text-[var(--color-muted)] ml-1">/ 30 km</span>
        </p>
        <div className="mt-3 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-accent)] rounded-full transition-all"
            style={{ width: `${Math.min((weekDistance / 30000) * 100, 100)}%` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-[var(--color-muted)]">
          <span className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {weekCount} {unit}
          </span>
          <span>{formatHours(weekSeconds)}</span>
        </div>
        <p className={`mt-1.5 text-xs ${weekDiff >= 0 ? 'text-emerald-500' : 'text-red-400'}`}>
          {weekDiff >= 0 ? '↗' : '↘'} {formatDistance(Math.abs(weekDiff))} km {locale === 'zh' ? 'vs 上周同期' : 'vs last week'}
        </p>
      </div>

      {/* Streak */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
        <p className="text-xs uppercase tracking-wider text-[var(--color-muted)] mb-2 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
          </svg>
          {t('streak')}
        </p>
        <div className="flex items-baseline gap-3">
          <p className="text-3xl font-bold font-mono">
            {currentStreak}
            <span className="text-base font-normal text-[var(--color-muted)] ml-1">{t('days')}</span>
          </p>
          <p className="text-3xl font-bold font-mono">
            {currentWeekStreak}
            <span className="text-base font-normal text-[var(--color-muted)] ml-1">{t('weeks')}</span>
          </p>
        </div>

        {/* Week days visual */}
        {(() => {
          const today = now.getDay()
          const weekStart = new Date(now.getTime() - today * 86400000)
          const weekLabels = locale === 'zh' ? ['日','一','二','三','四','五','六'] : ['S','M','T','W','T','F','S']
          const weekDays = Array.from({ length: 7 }, (_, i) => {
            const date = new Date(weekStart.getTime() + i * 86400000)
            const key = date.toISOString().slice(0, 10)
            const hasAct = activities.some((a) => a.start_date_local.slice(0, 10) === key)
            return { day: date.getDate(), hasActivity: hasAct, isToday: i === today }
          })
          return (
            <div className="mt-3 flex items-center gap-2">
              <svg className="w-6 h-6 text-[#f97316] shrink-0 self-center mt-3" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 23c-3.866 0-7-3.134-7-7 0-2.468 1.5-5.093 3.03-6.97.44-.54 1.47-.36 1.64.3.17.66.54 1.44 1.13 2.07.26-.94.76-2.06 1.57-3.04.81-.98 1.49-2.09 1.78-3.36.12-.53.71-.78 1.15-.46C17.09 6.46 19 9.58 19 13.5c0 5.247-3.134 9.5-7 9.5z"/>
              </svg>
              <div className="flex items-center gap-1.5 flex-1">
                {weekDays.map((wd, i) => {
                  const isPast = new Date(weekStart.getTime() + i * 86400000) < now || wd.isToday
                  return (
                  <div key={i} className="flex flex-col items-center gap-0.5">
                    <span className="text-[9px] text-[var(--color-muted)]">{weekLabels[i]}</span>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-medium ${
                      wd.hasActivity
                        ? 'bg-[var(--color-text)] text-[var(--color-bg)]'
                        : wd.isToday
                          ? 'ring-1.5 ring-[var(--color-text)] text-[var(--color-text)]'
                          : isPast
                            ? 'bg-[var(--color-border)] text-[var(--color-muted)]'
                            : 'text-[var(--color-muted)]'
                    }`}>
                      {wd.day}
                    </div>
                  </div>
                  )
                })}
              </div>
            </div>
          )
        })()}

        <div className="mt-3 flex items-center gap-2 text-sm text-[var(--color-muted)]">
          <svg className="w-3.5 h-3.5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
          {t('longest')}: {longestStreak} {t('days')} / {longestWeekStreak} {t('weeks')}
        </div>
      </div>
    </div>
  )
}
