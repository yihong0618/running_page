import { useMemo } from 'react'
import type { Activity, SportFilter } from '../types'

export function useFilteredActivities(
  activities: Activity[],
  filter: SportFilter,
  year: number | null
) {
  return useMemo(() => {
    let filtered = activities
    if (filter !== 'all') {
      filtered = filtered.filter((a) => a.type === filter)
    }
    if (year) {
      filtered = filtered.filter((a) => {
        const d = new Date(a.start_date_local)
        return d.getFullYear() === year
      })
    }
    return filtered
  }, [activities, filter, year])
}

export function parseMovingTime(time: string): number {
  const parts = time.split(':').map(Number)
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  return parts[0]
}

export function formatDistance(meters: number): string {
  return Math.round(meters / 1000).toString()
}

export function formatPace(speedMs: number): string {
  if (!speedMs) return '--'
  const paceMin = 1000 / 60 / speedMs
  const min = Math.floor(paceMin)
  const sec = Math.round((paceMin - min) * 60)
  return `${min}'${sec.toString().padStart(2, '0')}"`
}

export function formatDuration(timeStr: string): string {
  const secs = parseMovingTime(timeStr)
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export function getAvailableYears(activities: Activity[]): number[] {
  const years = new Set(
    activities.map((a) => new Date(a.start_date_local).getFullYear())
  )
  return Array.from(years).sort((a, b) => b - a)
}
