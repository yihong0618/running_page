import './index.css';
import {
  lazy,
  startTransition,
  Suspense,
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
import { Header } from './components/Header';
import { StatsCards } from './components/StatsCards';
import { ContributionHeatmap } from './components/ContributionHeatmap';
import { ActivityLog } from './components/ActivityLog';
import { DualCalendarWidget } from './components/DualCalendarWidget';
import { ProfileCard } from './components/ProfileCard';
import {
  PrivacyUnlockProvider,
  usePrivacyUnlock,
} from '@/contexts/PrivacyUnlockContext';
import { resolveActivityTitle } from '@/core/privacyTitles';
import {
  PRIVACY_MODE,
  PRIVACY_ANONYMOUS_TITLES,
  GITHUB_URL,
} from '@/core/config';
import { CAN_PRIVACY_UNLOCK } from '@/core/privacyUnlock';
import { DashboardContentSkeleton } from '@/components/PageSkeleton';
import { TrendChart } from './components/TrendChart';

const loadRouteMap = () =>
  import('./components/RouteMap').then((m) => ({ default: m.RouteMap }));
const loadTracksPage = () =>
  import('./components/TracksPage').then((m) => ({ default: m.TracksPage }));
const loadSummaryPage = () =>
  import('./components/SummaryPage').then((m) => ({ default: m.SummaryPage }));
const loadChinaMap = () =>
  import('./components/ChinaMap').then((m) => ({ default: m.ChinaMap }));

const RouteMap = lazy(loadRouteMap);
const TracksPage = lazy(loadTracksPage);
const SummaryPage = lazy(loadSummaryPage);
const ChinaMap = lazy(loadChinaMap);
const RunAnalysisLauncher = lazy(() =>
  import('./components/RunAnalysis').then((m) => ({
    default: m.RunAnalysisLauncher,
  }))
);

// Prefetch secondary pages so navigating home → summary/tracks does not flash Suspense.
void loadSummaryPage();
void loadTracksPage();
void loadRouteMap();
void loadChinaMap();

type Page = 'home' | 'tracks' | 'summary';

const FOOTER_YEAR = new Date().getFullYear();
const ACTIVITY_LOG_PAGE_SIZE = { mobile: 7, desktop: 16 } as const;

function MapFallback({
  className = 'h-[220px] md:h-[380px]',
}: {
  className?: string;
}) {
  return (
    <div
      className={`card flex items-center justify-center text-sm text-[var(--color-muted)] ${className}`}
    >
      …
    </div>
  );
}

function DashboardProContent({
  page,
  dark,
  filter,
  onNavigateHome,
}: {
  page: Page;
  dark: boolean;
  filter: 'all';
  onNavigateHome: () => void;
}) {
  const activities = getActivityData() as Activity[];
  const isUnlocked = usePrivacyUnlock();
  const { locale } = useLocale();
  const years = getAvailableYears(activities);
  /** Default to the latest year that has data (falls back to ALL if none). */
  const [year, setYear] = useState<number | null>(() => years[0] ?? null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(
    null
  );
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);

  const filtered = useFilteredActivities(activities, filter, year);
  /** Fallback year for components that require a concrete calendar year (e.g. TrendChart). */
  const chartYear = year ?? years[0] ?? FOOTER_YEAR;
  const privacyActive = PRIVACY_MODE && !isUnlocked;
  const useAnonymousTitles = privacyActive && PRIVACY_ANONYMOUS_TITLES;
  const activityTitle = (a: Activity) =>
    resolveActivityTitle(a, locale, useAnonymousTitles);

  const provinceFiltered = useMemo(() => {
    if (!selectedProvince) return filtered;
    return filtered.filter(
      (a) => extractProvince(a.location_country) === selectedProvince
    );
  }, [filtered, selectedProvince]);

  const allYears = year == null;
  const mapSlotRef = useRef<HTMLDivElement>(null);
  const [mapOutOfView, setMapOutOfView] = useState(false);
  const [mapFrame, setMapFrame] = useState<{
    left: number;
    width: number;
    height: number;
  } | null>(null);
  const pinRouteMap =
    page === 'home' && allYears && mapOutOfView && mapFrame != null;
  if ((page !== 'home' || !allYears) && mapOutOfView) setMapOutOfView(false);

  useEffect(() => {
    if (page !== 'home' || !allYears) return;
    const slot = mapSlotRef.current;
    if (!slot) return;
    const readFrame = () => {
      const rect = slot.getBoundingClientRect();
      setMapFrame({ left: rect.left, width: rect.width, height: rect.height });
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) readFrame();
        setMapOutOfView(!entry.isIntersecting);
      },
      { rootMargin: '-64px 0px 0px 0px', threshold: 0 }
    );
    observer.observe(slot);
    return () => observer.disconnect();
  }, [page, allYears]);

  useEffect(() => {
    if (!pinRouteMap) return;
    const slot = mapSlotRef.current;
    if (!slot) return;
    const readFrame = () => {
      const rect = slot.getBoundingClientRect();
      setMapFrame({ left: rect.left, width: rect.width, height: rect.height });
    };
    const resizeObserver = new ResizeObserver(readFrame);
    resizeObserver.observe(slot);
    window.addEventListener('resize', readFrame);
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', readFrame);
    };
  }, [pinRouteMap]);

  if (page === 'tracks') {
    return (
      <Suspense>
        <TracksPage
          activities={activities}
          filter={filter}
          onSelectActivity={setSelectedActivity}
          onBack={onNavigateHome}
          getTitle={activityTitle}
          lightsOff={privacyActive}
          dark={dark}
        />
      </Suspense>
    );
  }

  if (page === 'summary') {
    return (
      <Suspense>
        <SummaryPage onBack={onNavigateHome} />
      </Suspense>
    );
  }

  const activityLog = (
    <ActivityLog
      activities={filtered}
      years={years}
      year={year}
      setYear={setYear}
      selectedActivity={selectedActivity}
      onSelectActivity={setSelectedActivity}
      filter={filter}
      getTitle={activityTitle}
      pageSize={ACTIVITY_LOG_PAGE_SIZE}
      variant="pro"
    />
  );

  const routeMap = (
    <div
      ref={mapSlotRef}
      className={
        allYears
          ? 'order-3 min-h-[220px] md:min-h-[260px] lg:order-none'
          : 'sticky top-16 z-40 order-3 -my-2 py-2 lg:static lg:z-auto lg:order-none lg:my-0 lg:shrink-0 lg:py-0'
      }
    >
      <div
        className={pinRouteMap ? 'fixed top-20 z-40' : undefined}
        style={
          pinRouteMap && mapFrame
            ? {
                left: mapFrame.left,
                width: mapFrame.width,
                height: mapFrame.height,
              }
            : undefined
        }
      >
        <Suspense fallback={<MapFallback className="h-[220px] lg:h-[260px]" />}>
          <RouteMap
            activities={provinceFiltered}
            allActivities={activities}
            selectedActivity={selectedActivity}
            dark={dark}
            lightsOff={privacyActive}
            onClearSelection={() => setSelectedActivity(null)}
            className={
              pinRouteMap
                ? 'h-full shadow-lg [--card-shadow:var(--shadow-card-hover)]'
                : 'h-[220px] [--card-shadow:var(--shadow-card-hover)] md:h-[260px] lg:[--card-shadow:var(--shadow-card)]'
            }
          />
        </Suspense>
      </div>
    </div>
  );

  const calendar = (
    <div className="order-4 min-w-0 overflow-hidden lg:order-none lg:shrink-0">
      <DualCalendarWidget
        activities={activities}
        selectedActivity={selectedActivity}
        onSelectActivity={setSelectedActivity}
      />
    </div>
  );

  const trend = (
    <div
      className={`order-7 flex min-w-0 flex-col lg:order-none ${
        allYears ? 'lg:shrink-0' : 'lg:min-h-0 lg:flex-1'
      }`}
    >
      <TrendChart
        activities={filtered}
        year={chartYear}
        className={
          allYears
            ? 'h-[260px]'
            : 'h-[260px] lg:h-auto lg:min-h-[220px] lg:flex-1'
        }
      />
    </div>
  );

  return (
    <main
      className="mx-auto max-w-[1400px] px-4 py-6 md:px-6"
      // Reserve room for the floating run-analysis button so it never covers
      // the last row of content or map controls.
      style={
        selectedActivity
          ? { paddingBottom: 'calc(4.5rem + env(safe-area-inset-bottom, 0px))' }
          : undefined
      }
    >
      {/*
        Mobile order: Profile → Stats → sticky RouteMap → Calendar → ActivityLog
        → ChinaMap → Yearly Distance → Heatmap (bottom).
        Desktop, one year (2×2, each row stretches):
          [Stats+Heatmap] [Profile + Map]
          [ActivityLog  ] [RouteMap+Calendar+Distance]
        Desktop, all years: one left column and one right column.
        The China map and yearly distance chart keep a fixed height.
      */}
      <div
        className={`flex flex-col gap-6 lg:grid lg:grid-cols-[1fr_380px] lg:items-stretch xl:grid-cols-[1fr_400px] ${
          allYears ? '' : 'lg:grid-rows-[auto_auto]'
        }`}
      >
        {/* Left: stats + heatmap, plus the log when every year is shown */}
        <div className="contents min-w-0 lg:col-start-1 lg:row-start-1 lg:flex lg:min-h-0 lg:flex-col lg:gap-6">
          <div className="order-2 min-w-0 lg:order-none lg:shrink-0">
            <StatsCards
              activities={filtered}
              allActivities={activities}
              year={year}
              filter={filter}
              onSelectActivity={setSelectedActivity}
              compact
            />
          </div>
          <div className="order-9 min-w-0 overflow-hidden lg:order-none lg:shrink-0">
            <ContributionHeatmap
              activities={activities}
              year={year}
              filter={filter}
              onSelectActivity={setSelectedActivity}
              onYearChange={setYear}
            />
          </div>
          {allYears ? (
            <div className="order-5 flex min-w-0 flex-col overflow-hidden lg:order-none lg:min-h-0 lg:flex-1">
              {activityLog}
            </div>
          ) : null}
        </div>

        {/* Right: profile + map. All years also stacks route, calendar, chart. */}
        <div
          className={`contents min-w-0 lg:col-start-2 lg:row-start-1 lg:flex lg:min-h-0 lg:flex-col lg:gap-4 ${
            allYears ? '' : 'lg:h-full lg:overflow-hidden'
          }`}
        >
          <div className="order-1 min-w-0 overflow-hidden lg:order-none lg:shrink-0">
            <ProfileCard
              activities={activities}
              filter={filter}
              getTitle={activityTitle}
              onSelectActivity={setSelectedActivity}
              showRouteIcon
              showPersonalBest
              showLocationStats
            />
          </div>
          <div
            className={`order-6 min-w-0 overflow-hidden lg:order-none ${
              allYears ? 'lg:shrink-0' : 'lg:min-h-0 lg:flex-1'
            }`}
          >
            <Suspense
              fallback={
                <MapFallback
                  className={
                    allYears
                      ? 'h-[220px] lg:h-[260px]'
                      : 'h-[200px] lg:h-full lg:min-h-[180px]'
                  }
                />
              }
            >
              <ChinaMap
                activities={filtered}
                filter={filter}
                selectedProvince={selectedProvince}
                onSelectProvince={(p) => {
                  setSelectedProvince(p);
                  setSelectedActivity(null);
                }}
                className={
                  allYears ? 'h-[220px] lg:h-[260px]' : 'h-[200px] lg:h-full'
                }
              />
            </Suspense>
          </div>
          {allYears ? (
            <>
              {routeMap}
              {calendar}
              {trend}
            </>
          ) : null}
        </div>

        {allYears ? null : (
          <div className="order-5 flex min-w-0 flex-col overflow-hidden lg:order-none lg:col-start-1 lg:row-start-2 lg:min-h-0">
            {activityLog}
          </div>
        )}

        {allYears ? null : (
          <div className="contents min-w-0 lg:col-start-2 lg:row-start-2 lg:flex lg:min-h-0 lg:flex-col lg:gap-4 lg:overflow-hidden">
            {routeMap}
            {calendar}
            {trend}
          </div>
        )}
      </div>
      <Suspense fallback={null}>
        <RunAnalysisLauncher activity={selectedActivity} />
      </Suspense>
    </main>
  );
}

function DashboardProInner() {
  const { dark, toggle } = useTheme();
  const { locale } = useLocale();
  const [filter] = useState('all' as const);
  const [page, setPage] = useState<Page>('home');

  // Drives the `:lang(zh)` rules in index.css (e.g. the `eyebrow` utility,
  // where uppercase/wide tracking only makes sense for Latin labels).
  useEffect(() => {
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
  }, [locale]);

  const navigate = (next: Page) => {
    // Keep previous page painted while lazy chunks resolve (avoids Suspense flash).
    startTransition(() => setPage(next));
  };

  return (
    <div
      className={
        page === 'summary'
          ? 'flex h-svh flex-col bg-[var(--color-bg)]'
          : 'min-h-screen bg-[var(--color-bg)]'
      }
      data-filter={filter}
    >
      <Header
        dark={dark}
        toggleTheme={toggle}
        page={page}
        onNavigate={navigate}
        enablePrivacyUnlock={CAN_PRIVACY_UNLOCK}
        showSummary
      />

      <div
        className={
          page === 'summary'
            ? 'flex min-h-0 flex-1 flex-col overflow-hidden'
            : undefined
        }
      >
        <Suspense fallback={<DashboardContentSkeleton />}>
          <DashboardProContent
            page={page}
            dark={dark}
            filter={filter}
            onNavigateHome={() => navigate('home')}
          />
        </Suspense>
      </div>

      {page !== 'summary' ? (
        <footer className="flex items-center justify-center border-t border-[var(--color-border)] py-6 text-sm text-[var(--color-muted)]">
          <span>
            &copy; {FOOTER_YEAR} Running Page 3.0 ·{' '}
            {GITHUB_URL ? (
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-[var(--color-accent)]"
              >
                Dashboard Pro
              </a>
            ) : (
              'Dashboard Pro'
            )}
          </span>
        </footer>
      ) : null}
    </div>
  );
}

export default function DashboardProTheme() {
  return (
    <PrivacyUnlockProvider>
      <DashboardProInner />
    </PrivacyUnlockProvider>
  );
}
