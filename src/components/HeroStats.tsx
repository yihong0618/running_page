import type { Activity } from '../types'
import { formatDistance, parseMovingTime } from '../hooks/useActivities'

interface HeroStatsProps {
  activities: Activity[]
}

export function HeroStats({ activities }: HeroStatsProps) {
  const totalDistance = activities.reduce((s, a) => s + a.distance, 0)
  const totalCount = activities.length
  const totalSeconds = activities.reduce(
    (s, a) => s + parseMovingTime(a.moving_time),
    0
  )
  const totalHours = Math.round(totalSeconds / 3600)
  const longestDistance = Math.max(...activities.map((a) => a.distance), 0)
  const bestSpeed = Math.max(...activities.map((a) => a.average_speed), 0)

  // Calculate streak
  const dates = new Set(
    activities.map((a) => a.start_date_local.slice(0, 10))
  )
  let streak = 0
  const today = new Date()
  for (let i = 0; i < 365; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    if (dates.has(key)) streak++
    else if (i > 0) break
  }

  const stats = [
    { label: '总距离', value: formatDistance(totalDistance), unit: 'km' },
    { label: '总次数', value: totalCount.toString(), unit: '次' },
    { label: '总时间', value: totalHours.toString(), unit: '小时' },
    {
      label: '最长单次',
      value: formatDistance(longestDistance),
      unit: 'km',
    },
    {
      label: '最快速度',
      value: (bestSpeed * 3.6).toFixed(1),
      unit: 'km/h',
    },
    { label: '连续打卡', value: streak.toString(), unit: '天' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all hover:shadow-lg hover:-translate-y-0.5"
        >
          <p className="text-sm text-[var(--color-muted)] mb-1">{s.label}</p>
          <p className="text-3xl font-bold font-mono">
            {s.value}
            <span className="text-base font-normal text-[var(--color-muted)] ml-1">
              {s.unit}
            </span>
          </p>
        </div>
      ))}
    </div>
  )
}
