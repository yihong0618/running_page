import type { Activity } from '../types'
import { useLocale } from '../hooks/useLocale'
import { parseMovingTime } from '../hooks/useActivities'

interface PersonalBestProps {
  activities: Activity[]
  onSelectActivity?: (a: Activity | null) => void
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

const DISTANCES = [
  { key: '5K', min: 4.8, max: 5.5 },
  { key: '10K', min: 9.5, max: 11 },
  { key: 'Half Marathon', min: 20, max: 22.5 },
  { key: 'Marathon', min: 41, max: 44 },
]

export function PersonalBest({ activities, onSelectActivity }: PersonalBestProps) {
  const { locale } = useLocale()

  // Only outdoor runs with valid GPS tracks (polyline must be substantial, not just a point)
  const runs = activities.filter(a => a.type === 'Run' && a.summary_polyline && a.summary_polyline.length > 20)

  const labels: Record<string, string> = locale === 'zh'
    ? { '5K': '5公里', '10K': '10公里', 'Half Marathon': '半程马拉松', 'Marathon': '全程马拉松' }
    : { '5K': '5K', '10K': '10K', 'Half Marathon': 'Half Marathon', 'Marathon': 'Marathon' }

  const bests = DISTANCES.map(({ key, min, max }) => {
    const matching = runs.filter(a => {
      const km = a.distance / 1000
      if (km < min || km > max) return false
      // Filter out GPS drift: pace must be reasonable (3:00/km ~ 8:00/km)
      const time = parseMovingTime(a.moving_time)
      const pacePerKm = time / km // seconds per km
      return pacePerKm >= 180 && pacePerKm <= 480 // 3min/km to 8min/km
    })
    if (matching.length === 0) return { key, activity: null, time: 0 }
    const best = matching.reduce((b, a) => {
      return parseMovingTime(a.moving_time) < parseMovingTime(b.moving_time) ? a : b
    })
    return { key, activity: best, time: parseMovingTime(best.moving_time) }
  })

  const hasBests = bests.some(b => b.activity !== null)
  if (!hasBests) return null

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5 transition-all duration-300 hover:scale-[1.01] hover:shadow-lg hover:shadow-[var(--color-accent)]/5 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5">
      <h3 className="text-sm font-semibold flex items-center gap-1.5 mb-3">
        <svg className="w-4 h-4 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
        {locale === 'zh' ? '个人最佳' : 'Personal Best'}
      </h3>

      <div className="divide-y divide-[var(--color-border)]">
        {bests.map(({ key, activity, time }) => (
          <div
            key={key}
            className={`flex items-center justify-between py-2.5 ${
              activity ? 'cursor-pointer hover:bg-[var(--color-bg)] -mx-2 px-2 rounded-lg transition-colors' : ''
            }`}
            onClick={() => activity && onSelectActivity?.(activity)}
          >
            <span className="text-sm text-[var(--color-text)]">{labels[key]}</span>
            <span className={`text-sm font-mono font-bold ${activity ? 'text-[var(--color-accent)]' : 'text-[var(--color-muted)]'}`}>
              {activity ? formatTime(time) : '--'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
