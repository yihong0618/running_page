import { Suspense, useMemo, useState } from 'react'
import './index.css'
import type { Activity } from './types'
import { useFilteredActivities, getAvailableYears, extractProvince, getActivityData } from './hooks/useActivities'
import { useTheme } from './hooks/useTheme'
import { LocaleProvider } from './hooks/useLocale'
import { Header } from './components/Header'
import { StatsCards } from './components/StatsCards'
import { ContributionHeatmap } from './components/ContributionHeatmap'
import { ActivityLog } from './components/ActivityLog'
import { RouteMap } from './components/RouteMap'
import { CalendarWidget } from './components/CalendarWidget'
import { ProfileCard } from './components/ProfileCard'
import { PersonalBest } from './components/PersonalBest'
import { TracksPage } from './components/TracksPage'
import { ChinaMap } from './components/ChinaMap'

type Page = 'home' | 'tracks'

function Dashboard() {
  const activities = getActivityData() as Activity[]
  const { dark, toggle } = useTheme()
  const [filter] = useState('all' as const)
  const [year, setYear] = useState<number | null>(null)
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null)
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null)
  const [page, setPage] = useState<Page>('home')

  const years = getAvailableYears(activities)
  const filtered = useFilteredActivities(activities, filter, year)
  const heatmapYear = year ?? years[0] ?? new Date().getFullYear()

  // Activities filtered to the selected province (for RouteMap)
  const provinceFiltered = useMemo(() => {
    if (!selectedProvince) return filtered
    return filtered.filter(a => extractProvince(a.location_country) === selectedProvince)
  }, [filtered, selectedProvince])

  return (
    <div className="min-h-screen bg-[var(--color-bg)]" data-filter={filter}>
      <Header
        dark={dark}
        toggleTheme={toggle}
        activities={activities}
        page={page}
        onNavigate={setPage}
      />

      {page === 'tracks' ? (
        <TracksPage
          activities={filtered}
          filter={filter}
          onSelectActivity={setSelectedActivity}
          onBack={() => setPage('home')}
        />
      ) : (
        <main className="max-w-[1400px] mx-auto px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left column */}
            <div className="space-y-6 min-w-0 overflow-hidden">
              <StatsCards activities={filtered} allActivities={activities} year={year} filter={filter} onSelectActivity={setSelectedActivity} />
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
            <div className="flex flex-col gap-6 min-w-0 overflow-hidden">
              <ProfileCard activities={activities} filter={filter} />
              <ChinaMap
                activities={filtered}
                filter={filter}
                selectedProvince={selectedProvince}
                onSelectProvince={(p) => {
                  setSelectedProvince(p)
                  setSelectedActivity(null)
                }}
              />
              <RouteMap
                activities={provinceFiltered}
                selectedActivity={selectedActivity}
                dark={dark}
                onClearSelection={() => setSelectedActivity(null)}
              />
              <PersonalBest activities={activities} onSelectActivity={setSelectedActivity} />
              <CalendarWidget
                activities={filtered}
                onSelectActivity={setSelectedActivity}
              />
            </div>
          </div>
        </main>
      )}

      <footer className="text-center py-6 text-sm text-[var(--color-muted)] border-t border-[var(--color-border)]">
        &copy; {new Date().getFullYear()} Running Page 3.0
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <LocaleProvider>
      <Suspense fallback={
        <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center">
          <div className="text-[var(--color-muted)] text-sm">Loading...</div>
        </div>
      }>
        <Dashboard />
      </Suspense>
    </LocaleProvider>
  )
}
