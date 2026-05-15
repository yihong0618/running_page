import { useState, useEffect } from 'react'
import type { Activity, SportFilter } from '../types'
import { formatDistance, formatDuration, formatPace } from '../hooks/useActivities'
import { useLocale } from '../hooks/useLocale'

interface ActivityLogProps {
  activities: Activity[]
  years: number[]
  year: number | null
  setYear: (y: number | null) => void
  selectedActivity?: Activity | null
  onSelectActivity?: (a: Activity | null) => void
  filter?: SportFilter
}

const PAGE_SIZE = 16

type DistanceFilter = 'all' | '10' | '20' | '40'

export function ActivityLog({ activities, years, year, setYear, selectedActivity, onSelectActivity, filter = 'all' }: ActivityLogProps) {
  const { t, locale } = useLocale()
  const [page, setPage] = useState(0)
  const [distFilter, setDistFilter] = useState<DistanceFilter>('all')

  const distFiltered = activities.filter((a) => {
    const km = a.distance / 1000
    switch (distFilter) {
      case '10': return km >= 10 && km < 20
      case '20': return km >= 20 && km < 40
      case '40': return km >= 40
      default: return true
    }
  })

  const sorted = [...distFiltered].sort(
    (a, b) =>
      new Date(b.start_date_local).getTime() -
      new Date(a.start_date_local).getTime()
  )

  // Auto-navigate to the page containing selectedActivity
  useEffect(() => {
    if (selectedActivity) {
      const idx = sorted.findIndex(a => a.run_id === selectedActivity.run_id)
      if (idx >= 0) {
        const targetPage = Math.floor(idx / PAGE_SIZE)
        setPage(targetPage)
      } else {
        // Activity not in current filter, reset distance filter
        setDistFilter('all')
      }
    }
  }, [selectedActivity?.run_id])

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold">
          {filter === 'Run' ? (locale === 'zh' ? '跑步记录' : 'Run Log')
            : filter === 'Ride' ? (locale === 'zh' ? '骑行记录' : 'Ride Log')
            : t('activityLog')}
        </h2>
        <span className="text-sm text-[var(--color-muted)]">
          {t('showing')} {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, sorted.length)} {t('of')}{' '}
          {sorted.length}
        </span>
      </div>

      {/* Year tabs */}
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={() => setYear(null)}
          className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
            year === null
              ? 'bg-[var(--color-accent)] text-white'
              : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'
          }`}
        >
          All
        </button>
        {years.map((y) => (
          <button
            key={y}
            onClick={() => { setYear(y); setPage(0) }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              year === y
                ? 'bg-[var(--color-accent)] text-white'
                : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {y}
          </button>
        ))}
      </div>

      {/* Distance filter tabs */}
      <div className="flex items-center gap-2 mb-5">
        {([['all', t('all')], ['10', '10km+'], ['20', '20km+'], ['40', '40km+']] as [DistanceFilter, string][]).map(([val, label]) => (
          <button
            key={val}
            onClick={() => { setDistFilter(val); setPage(0) }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              distFilter === val
                ? 'bg-[var(--color-accent)] text-white'
                : 'bg-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--color-muted)] border-b border-[var(--color-border)]">
              <th className="pb-3 font-medium">{t('date')}</th>
              <th className="pb-3 font-medium">{t('type')}</th>
              <th className="pb-3 font-medium">{t('name')}</th>
              <th className="pb-3 font-medium">{t('distance')}</th>
              <th className="pb-3 font-medium">{t('duration')}</th>
              <th className="pb-3 font-medium">{t('pace')}</th>
              <th className="pb-3 font-medium">{t('hr')}</th>
            </tr>
          </thead>
          <tbody>
            {pageData.map((a) => (
              <tr
                key={a.run_id}
                onClick={() => onSelectActivity?.(selectedActivity?.run_id === a.run_id ? null : a)}
                className={`border-b border-[var(--color-border)]/30 cursor-pointer transition-colors ${
                  selectedActivity?.run_id === a.run_id
                    ? 'bg-[var(--color-accent)]/10 border-l-2 border-l-[var(--color-accent)]'
                    : 'hover:bg-[var(--color-bg)]'
                }`}
              >
                <td className="py-3 text-[var(--color-muted)]">
                  {a.start_date_local.slice(0, 16).replace('T', ' ')}
                </td>
                <td className="py-3 text-[var(--color-muted)]">{a.type}</td>
                <td className="py-3">{a.name || (a.type === 'Run' ? t('run') : t('ride'))}</td>
                <td className="py-3 font-mono font-medium">
                  {formatDistance(a.distance)}
                  <span className="text-[var(--color-muted)] ml-1 font-normal text-xs">km</span>
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {formatDuration(a.moving_time)}
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {a.type === 'Run'
                    ? formatPace(a.average_speed)
                    : `${(a.average_speed * 3.6).toFixed(1)} km/h`}
                </td>
                <td className="py-3 text-[var(--color-muted)]">
                  {a.average_heartrate ? Math.round(a.average_heartrate) : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border)]">
        <button
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          className="text-[var(--color-muted)] hover:text-[var(--color-text)] disabled:opacity-30 transition-colors"
        >
          ←
        </button>
        <span className="text-sm text-[var(--color-muted)]">
          {t('page')} {page + 1} {t('pageOf')} {totalPages} {t('pages')}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
          disabled={page >= totalPages - 1}
          className="text-[var(--color-muted)] hover:text-[var(--color-text)] disabled:opacity-30 transition-colors"
        >
           →
        </button>
      </div>
    </div>
  )
}
