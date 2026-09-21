import './index.css';
import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { Activity } from '@/types';
import {
  useFilteredActivities,
  getAvailableYears,
  extractProvince,
  getActivityData,
} from '@/hooks/useActivities';
import { useTheme } from '@/hooks/useTheme';
import { useLocale } from '@/hooks/useLocale';
import { Header } from '@/components/Header';
import { StatsCards } from '@/components/StatsCards';
import { ContributionHeatmap } from '@/components/ContributionHeatmap';
import { ActivityLog } from '@/components/ActivityLog';
import { RouteMap } from '@/components/RouteMap';
import { CalendarWidget } from '@/components/CalendarWidget';
import { ProfileCard } from '@/components/ProfileCard';
import { PersonalBest } from '@/components/PersonalBest';
import { ChinaMap } from '@/components/ChinaMap';

const TracksPage = lazy(() =>
  import('@/components/TracksPage').then((module) => ({
    default: module.TracksPage,
  }))
);
const SummaryPage = lazy(() =>
  import('@/components/SummaryPage').then((module) => ({
    default: module.SummaryPage,
  }))
);

type Page = 'home' | 'tracks' | 'summary';
const pageFromPath = (): Page =>
  window.location.pathname
    .slice(import.meta.env.BASE_URL.length)
    .replace(/\/$/, '') === 'summary'
    ? 'summary'
    : window.location.pathname
          .slice(import.meta.env.BASE_URL.length)
          .replace(/\/$/, '') === 'tracks'
      ? 'tracks'
      : 'home';

function Dashboard() {
  const routeSectionRef = useRef<HTMLDivElement>(null);
  const activities = getActivityData() as Activity[];
  const { dark, toggle } = useTheme();
  const { t } = useLocale();
  const [filter] = useState('all' as const);
  const [year, setYear] = useState<number | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(
    null
  );
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);
  const [page, setPage] = useState<Page>(pageFromPath);

  useEffect(() => {
    const onPopState = () => setPage(pageFromPath());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);
  const navigate = (next: Page) => {
    window.history.pushState(
      null,
      '',
      `${import.meta.env.BASE_URL}${next === 'home' ? '' : next}`
    );
    setPage(next);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  const selectProvince = useCallback((province: string | null) => {
    setSelectedProvince(province);
    setSelectedActivity(null);
  }, []);

  const [currentYear] = useState(() => new Date().getFullYear());
  const years = useMemo(() => getAvailableYears(activities), [activities]);
  const filtered = useFilteredActivities(activities, filter, year);
  const heatmapYear = year ?? years[0] ?? currentYear;

  // Activities filtered to the selected province (for RouteMap)
  const provinceFiltered = useMemo(() => {
    if (!selectedProvince) return filtered;
    return filtered.filter(
      (a) => extractProvince(a.location_country) === selectedProvince
    );
  }, [filtered, selectedProvince]);

  const selectActivity = useCallback(
    (activity: Activity | null) => {
      setSelectedActivity(activity);
      if (activity) {
        setSelectedProvince(null);
        if (window.matchMedia('(max-width: 1023px)').matches) {
          requestAnimationFrame(() =>
            routeSectionRef.current?.scrollIntoView({
              block: 'start',
              behavior: window.matchMedia('(prefers-reduced-motion: reduce)')
                .matches
                ? 'instant'
                : 'smooth',
            })
          );
        }
        if (
          year !== null &&
          new Date(activity.start_date_local).getFullYear() !== year
        ) {
          setYear(new Date(activity.start_date_local).getFullYear());
        }
      }
    },
    [year]
  );

  return (
    <div
      className="dashboard min-h-screen bg-[var(--color-bg)]"
      data-filter={filter}
    >
      <Header
        dark={dark}
        toggleTheme={toggle}
        activities={activities}
        page={page}
        onNavigate={navigate}
      />

      <Suspense
        fallback={
          <main
            className="mx-auto flex min-h-[60vh] max-w-[1400px] items-center justify-center p-6 text-sm text-[var(--color-muted)]"
            role="status"
          >
            {t('loading')}
          </main>
        }
      >
        {page === 'summary' ? (
          <SummaryPage
            activities={activities}
            onSelectActivity={(activity) => {
              navigate('home');
              setYear(null);
              selectActivity(activity);
            }}
          />
        ) : page === 'tracks' ? (
          <TracksPage
            activities={activities}
            dark={dark}
            filter={filter}
            onSelectActivity={selectActivity}
            onBack={() => {
              navigate('home');
              window.scrollTo({ top: 0, behavior: 'instant' });
            }}
          />
        ) : (
          <main className="mx-auto max-w-[1400px] px-4 py-5 sm:px-6 sm:py-6">
            <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_380px]">
              {/* Left column */}
              <div className="min-w-0 space-y-6 overflow-hidden">
                <StatsCards
                  activities={filtered}
                  allActivities={activities}
                  year={year}
                  filter={filter}
                  onSelectActivity={selectActivity}
                />
                <ContributionHeatmap
                  activities={activities}
                  year={heatmapYear}
                  filter={filter}
                  onSelectActivity={selectActivity}
                />
                <ActivityLog
                  activities={filtered}
                  years={years}
                  year={year}
                  setYear={(value) => {
                    setYear(value);
                    setSelectedActivity(null);
                    setSelectedProvince(null);
                  }}
                  selectedActivity={selectedActivity}
                  onSelectActivity={selectActivity}
                  filter={filter}
                />
              </div>

              {/* Right column */}
              <div className="flex min-w-0 flex-col gap-6 overflow-hidden">
                <ProfileCard activities={activities} filter={filter} />
                <ChinaMap
                  activities={filtered}
                  filter={filter}
                  selectedProvince={selectedProvince}
                  onSelectProvince={selectProvince}
                />
                <div ref={routeSectionRef} className="scroll-mt-28">
                  <RouteMap
                    activities={provinceFiltered}
                    selectedActivity={selectedActivity}
                    dark={dark}
                    onClearSelection={() => setSelectedActivity(null)}
                  />
                </div>
                <PersonalBest
                  activities={activities}
                  onSelectActivity={selectActivity}
                />
                <CalendarWidget
                  key={year ?? 'all'}
                  selectedActivity={selectedActivity}
                  activities={filtered}
                  onSelectActivity={selectActivity}
                />
              </div>
            </div>
          </main>
        )}
      </Suspense>

      <footer className="border-t border-[var(--color-border)] py-6 text-center text-sm text-[var(--color-muted)]">
        &copy; {currentYear} Running Page 3.0
      </footer>
    </div>
  );
}

export default Dashboard;
