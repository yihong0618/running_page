import { useState } from 'react'
import type { Activity } from '../types'
import { formatDistance, formatDuration, formatPace } from '../hooks/useActivities'

interface ActivityListProps {
  activities: Activity[]
}

type ViewMode = 'card' | 'table'
type SortKey = 'date' | 'distance' | 'pace'

export function ActivityList({ activities }: ActivityListProps) {
  const [view, setView] = useState<ViewMode>('card')
  const [sortKey, setSortKey] = useState<SortKey>('date')

  const sorted = [...activities].sort((a, b) => {
    if (sortKey === 'date')
      return (
        new Date(b.start_date_local).getTime() -
        new Date(a.start_date_local).getTime()
      )
    if (sortKey === 'distance') return b.distance - a.distance
    return b.average_speed - a.average_speed
  })

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">活动列表</h3>
        <div className="flex items-center gap-3">
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-2 py-1 text-sm"
          >
            <option value="date">按日期</option>
            <option value="distance">按距离</option>
            <option value="pace">按速度</option>
          </select>
          <div className="flex gap-1">
            <button
              onClick={() => setView('card')}
              className={`px-2 py-1 rounded text-sm ${view === 'card' ? 'bg-[var(--color-all)] text-white' : 'text-[var(--color-muted)]'}`}
            >
              ▦
            </button>
            <button
              onClick={() => setView('table')}
              className={`px-2 py-1 rounded text-sm ${view === 'table' ? 'bg-[var(--color-all)] text-white' : 'text-[var(--color-muted)]'}`}
            >
              ≡
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {view === 'card' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {sorted.slice(0, 30).map((a) => (
            <ActivityCard key={a.run_id} activity={a} />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--color-muted)] border-b border-[var(--color-border)]">
                <th className="pb-2 font-medium">日期</th>
                <th className="pb-2 font-medium">类型</th>
                <th className="pb-2 font-medium">距离</th>
                <th className="pb-2 font-medium">时间</th>
                <th className="pb-2 font-medium">速度</th>
              </tr>
            </thead>
            <tbody>
              {sorted.slice(0, 50).map((a) => (
                <tr
                  key={a.run_id}
                  className="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-bg)]"
                >
                  <td className="py-2">{a.start_date_local.slice(0, 10)}</td>
                  <td className="py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${a.type === 'Run' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}
                    >
                      {a.type === 'Run' ? '跑步' : '骑行'}
                    </span>
                  </td>
                  <td className="py-2 font-mono">
                    {formatDistance(a.distance)} km
                  </td>
                  <td className="py-2">{formatDuration(a.moving_time)}</td>
                  <td className="py-2 font-mono">
                    {a.type === 'Run'
                      ? formatPace(a.average_speed)
                      : `${(a.average_speed * 3.6).toFixed(1)} km/h`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function ActivityCard({ activity: a }: { activity: Activity }) {
  return (
    <div className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg p-4 hover:shadow-md hover:-translate-y-0.5 transition-all">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[var(--color-muted)]">
          {a.start_date_local.slice(0, 10)}
        </span>
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${a.type === 'Run' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}
        >
          {a.type === 'Run' ? '🏃 跑步' : '🚴 骑行'}
        </span>
      </div>
      <p className="text-2xl font-bold font-mono mb-1">
        {formatDistance(a.distance)}{' '}
        <span className="text-sm font-normal text-[var(--color-muted)]">km</span>
      </p>
      <div className="flex gap-3 text-xs text-[var(--color-muted)]">
        <span>{formatDuration(a.moving_time)}</span>
        <span>
          {a.type === 'Run'
            ? formatPace(a.average_speed)
            : `${(a.average_speed * 3.6).toFixed(1)} km/h`}
        </span>
      </div>
    </div>
  )
}
