import type { Activity, SportFilter } from '../types'
import { useLocale } from '../hooks/useLocale'
import { formatDistance, parseMovingTime } from '../hooks/useActivities'

interface ProfileCardProps {
  activities: Activity[]
  filter?: SportFilter
}

export function ProfileCard({ activities, filter = 'all' }: ProfileCardProps) {
  const { t, locale } = useLocale()

  // Filter activities by sport type for distance/count/time
  const filteredActivities = filter === 'all' ? activities : activities.filter(a => a.type === filter)

  const totalDistance = filteredActivities.reduce((s, a) => s + a.distance, 0)
  const totalCount = filteredActivities.length
  const totalSeconds = filteredActivities.reduce((s, a) => s + parseMovingTime(a.moving_time), 0)

  const allDates = activities.map((a) => new Date(a.start_date_local).getFullYear())
  const yearsActive = allDates.length > 0 ? (Math.max(...allDates) - Math.min(...allDates) + 1) : 0

  // Countries and provinces
  const countries = new Set<string>()
  const provinces = new Set<string>()
  const knownProvinces = ['上海市','北京市','浙江省','江苏省','河南省','广东省','福建省','安徽省','山东省','四川省','湖北省','湖南省','云南省','贵州省','海南省','天津市','重庆市']
  for (const a of activities) {
    const loc = a.location_country
    if (!loc || loc === 'None') continue
    if (loc.startsWith('{')) {
      try {
        const d = JSON.parse(loc.replace(/'/g, '"').replace(/None/g, 'null'))
        if (d.country) countries.add(d.country)
        if (d.province) provinces.add(d.province)
      } catch { /* ignore */ }
      continue
    }
    if (loc.includes(':') && !loc.includes(',')) {
      countries.add('中国')
    } else if (loc.includes('中国')) {
      countries.add('中国')
    } else if (loc.includes('泰国')) {
      countries.add('泰国')
    } else if (loc.includes('日本')) {
      countries.add('日本')
    } else if (loc.includes(',')) {
      countries.add('中国')
    }
    for (const p of knownProvinces) {
      if (loc.includes(p)) { provinces.add(p); break }
    }
    if (loc.includes('上海')) provinces.add('上海市')
    if (loc.includes('江苏')) provinces.add('江苏省')
    if (loc.includes('河南')) provinces.add('河南省')
  }

  const formatHours = (secs: number) => `${(secs / 3600).toFixed(1)}h`

  const latest = activities.length > 0
    ? [...activities].sort((a, b) =>
        new Date(b.start_date_local).getTime() - new Date(a.start_date_local).getTime()
      )[0]
    : null

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    if (locale === 'zh') {
      return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
    }
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.01] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
      {/* Avatar & Name */}
      <div className="flex flex-col items-center">
        <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-[var(--color-border)] mb-3">
          <img
            src="https://avatars.githubusercontent.com/u/8613196"
            alt="Hank Zhao"
            className="w-full h-full object-cover"
          />
        </div>
        <h3 className="text-lg font-bold">Hank Zhao</h3>
      </div>

      {/* Total Distance + Countries */}
      <div className="mt-4 text-center">
        <p className="text-3xl font-bold font-mono">
          {formatDistance(totalDistance)}
          <span className="text-base font-normal text-[var(--color-muted)] ml-1">km</span>
        </p>
        <p className="mt-1.5 text-sm text-[var(--color-muted)] flex items-center justify-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {countries.size} {t('countries')} ·
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          {provinces.size} {t('provinces')}
        </p>
      </div>

      {/* Stats row - Strava style */}
      <div className="grid grid-cols-3 gap-2 mt-4 text-center border-t border-[var(--color-border)] pt-4">
        <div>
          <p className="text-xs text-[var(--color-muted)] flex items-center justify-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {t('activities')}
          </p>
          <p className="text-lg font-bold">{totalCount.toLocaleString()}</p>
        </div>
        <div className="border-x border-[var(--color-border)]">
          <p className="text-xs text-[var(--color-muted)] flex items-center justify-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {t('years')}
          </p>
          <p className="text-lg font-bold">{yearsActive}</p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-muted)] flex items-center justify-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {locale === 'zh' ? '时间' : 'Time'}
          </p>
          <p className="text-lg font-bold">{formatHours(totalSeconds)}</p>
        </div>
      </div>

      {/* Latest Activity */}
      {latest && (
        <div className="mt-4 pt-4 border-t border-[var(--color-border)]">
          <p className="text-xs text-[var(--color-muted)] mb-1">{locale === 'zh' ? '最近活动' : 'Latest Activity'}</p>
          <p className="text-sm font-medium">
            {latest.type === 'Run' ? '🏃 ' : '🚴 '}
            {latest.name || (latest.type === 'Run' ? 'Run' : 'Ride')}
            <span className="text-[var(--color-muted)] font-normal"> · {formatDistance(latest.distance)} km · {formatDate(latest.start_date_local)}</span>
          </p>
        </div>
      )}
    </div>
  )
}
