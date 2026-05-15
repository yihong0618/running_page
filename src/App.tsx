import { useState } from 'react'
import './index.css'
import type { Activity, SportFilter } from './types'
import { useFilteredActivities, getAvailableYears } from './hooks/useActivities'
import { useTheme } from './hooks/useTheme'
import { LocaleProvider } from './hooks/useLocale'
import { Header } from './components/Header'
import { StatsCards } from './components/StatsCards'
import { ContributionHeatmap } from './components/ContributionHeatmap'
import { ActivityLog } from './components/ActivityLog'
import { RouteMap } from './components/RouteMap'
import { CalendarWidget } from './components/CalendarWidget'
import { MonthlyChart } from './components/MonthlyChart'
import { ProfileCard } from './components/ProfileCard'
import { PersonalBest } from './components/PersonalBest'
import rawActivities from './static/activities.json'

const activities = rawActivities as Activity[]

export default function App() {
  const { dark, toggle } = useTheme()
  const [filter, setFilter] = useState<SportFilter>('all')
  const [year, setYear] = useState<number | null>(null)
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null)

  const years = getAvailableYears(activities)
  const filtered = useFilteredActivities(activities, filter, year)
  const heatmapYear = year ?? years[0] ?? new Date().getFullYear()

  return (
    <LocaleProvider>
      <div className="min-h-screen bg-[var(--color-bg)]" data-filter={filter}>
      <Header
        filter={filter}
        setFilter={setFilter}
        dark={dark}
        toggleTheme={toggle}
      />

      <main className="max-w-[1400px] mx-auto px-6 py-6">
        {/* Single two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
          {/* Left column */}
          <div className="space-y-6">
            <StatsCards activities={filtered} allActivities={activities} year={year} filter={filter} />
            <ContributionHeatmap activities={filtered} year={heatmapYear} filter={filter} onSelectActivity={setSelectedActivity} />
            <ActivityLog
              activities={filtered}
              years={years}
              year={year}
              setYear={setYear}
              selectedActivity={selectedActivity}
              onSelectActivity={setSelectedActivity}
              filter={filter}
            />
          </div>

          {/* Right column */}
          <div className="space-y-6">
            <ProfileCard activities={activities} filter={filter} />
            <PersonalBest activities={activities} onSelectActivity={setSelectedActivity} />
            <CalendarWidget
              activities={filtered}
              onSelectActivity={setSelectedActivity}
            />
            <RouteMap
              activities={filtered}
              selectedActivity={selectedActivity}
              dark={dark}
              onClearSelection={() => setSelectedActivity(null)}
            />
            <MonthlyChart activities={filtered} year={heatmapYear} onYearChange={setYear} />
          </div>
        </div>
      </main>

      <footer className="text-center py-6 text-sm text-[var(--color-muted)] border-t border-[var(--color-border)]">
        &copy; {new Date().getFullYear()} Workout Dashboard. All miles counted.
      </footer>
      </div>
    </LocaleProvider>
  )
}
