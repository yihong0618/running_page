import { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { Analytics } from '@vercel/analytics/react';
import Layout from '@/components/Layout';
import LocationStat from '@/components/LocationStat';
import RunMap from '@/components/RunMap';
import RunTable from '@/components/RunTable';
import SVGStat from '@/components/SVGStat';
import YearsStat from '@/components/YearsStat';
import useActivities from '@/hooks/useActivities';
import useSiteMetadata from '@/hooks/useSiteMetadata';
import { IS_CHINESE } from '@/utils/const';
import {
  Activity,
  IViewState,
  filterAndSortRuns,
  filterCityRuns,
  filterTitleRuns,
  filterYearRuns,
  geoJsonForRuns,
  getBoundsForGeoData,
  scrollToMap,
  sortDateFunc,
  titleForShow,
  RunIds,
} from '@/utils/utils';

const Index = () => {
  const { siteTitle } = useSiteMetadata();
  const { activities, thisYear } = useActivities();
  const [year, setYear] = useState(thisYear);
  const [runIndex, setRunIndex] = useState(-1);
  const [title, setTitle] = useState('');
  const intervalIdRef = useRef<number | null>(null);
  const [currentFilter, setCurrentFilter] = useState<{
    item: string;
    func: (_run: Activity, _value: string) => boolean;
  }>({ item: thisYear, func: filterYearRuns });

  // State to track if we're showing a single run from URL hash
  const [singleRunId, setSingleRunId] = useState<number | null>(null);

  // Animation trigger for single runs - increment this to force animation replay
  const [animationTrigger, setAnimationTrigger] = useState(0);

  // Parse URL hash on mount to check for run ID
  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    if (hash && hash.startsWith('run_')) {
      const runId = parseInt(hash.replace('run_', ''), 10);
      if (!isNaN(runId)) {
        setSingleRunId(runId);
      }
    }

    // Listen for hash changes (browser back/forward buttons)
    const handleHashChange = () => {
      const newHash = window.location.hash.replace('#', '');
      if (newHash && newHash.startsWith('run_')) {
        const runId = parseInt(newHash.replace('run_', ''), 10);
        if (!isNaN(runId)) {
          setSingleRunId(runId);
        }
      } else {
        // Hash was cleared, reset to normal view
        setSingleRunId(null);
      }
    };

    window.addEventListener('hashchange', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  // Memoize expensive calculations
  const runs = useMemo(() => {
    return filterAndSortRuns(
      activities,
      currentFilter.item,
      currentFilter.func,
      sortDateFunc
    );
  }, [activities, currentFilter.item, currentFilter.func]);

  const geoData = useMemo(() => {
    return geoJsonForRuns(runs);
  }, [runs]);

  // for auto zoom
  const bounds = useMemo(() => {
    return getBoundsForGeoData(geoData);
  }, [geoData]);

  const [viewState, setViewState] = useState<IViewState>(() => ({
    ...bounds,
  }));

  // Add state for animated geoData to handle the animation effect
  const [animatedGeoData, setAnimatedGeoData] = useState(geoData);

  const changeByItem = useCallback(
    (
      item: string,
      name: string,
      func: (_run: Activity, _value: string) => boolean
    ) => {
      scrollToMap();
      if (name != 'Year') {
        setYear(thisYear);
      }
      setCurrentFilter({ item, func });
      setRunIndex(-1);
      setTitle(`${item} ${name} Running Heatmap`);
    },
    [thisYear]
  );

  const changeYear = useCallback(
    (y: string) => {
      // default year
      setYear(y);

      if ((viewState.zoom ?? 0) > 3 && bounds) {
        setViewState({
          ...bounds,
        });
      }

      changeByItem(y, 'Year', filterYearRuns);
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    },
    [viewState.zoom, bounds, changeByItem]
  );

  const changeCity = useCallback(
    (city: string) => {
      changeByItem(city, 'City', filterCityRuns);
    },
    [changeByItem]
  );

  const changeTitle = useCallback(
    (title: string) => {
      changeByItem(title, 'Title', filterTitleRuns);
    },
    [changeByItem]
  );

  // For RunTable compatibility - create a mock setActivity function
  const setActivity = useCallback((_newRuns: Activity[]) => {
    // Since we're using memoized runs, we can't directly set activity
    // This is used by RunTable but we can work around it by managing the filter instead
    console.warn('setActivity called but runs are now computed from filters');
  }, []);

  const locateActivity = useCallback(
    (runIds: RunIds) => {
      const ids = new Set(runIds);

      const selectedRuns = !runIds.length
        ? runs
        : runs.filter((r: any) => ids.has(r.run_id));

      if (!selectedRuns.length) {
        return;
      }

      const lastRun = selectedRuns.sort(sortDateFunc)[0];

      if (!lastRun) {
        return;
      }

      // Update URL hash when a single run is located
      if (runIds.length === 1) {
        const runId = runIds[0];
        const newHash = `#run_${runId}`;
        if (window.location.hash !== newHash) {
          window.history.pushState(null, '', newHash);
        }
        setSingleRunId(runId);
      } else {
        // If multiple runs or no runs, clear the hash and single run state
        if (window.location.hash) {
          window.history.pushState(null, '', window.location.pathname);
        }
        setSingleRunId(null);
      }

      // Create geoData for selected runs and calculate new bounds
      const selectedGeoData = geoJsonForRuns(selectedRuns);
      const selectedBounds = getBoundsForGeoData(selectedGeoData);

      // Clear any existing animation interval first
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }

      // Update the animated geoData immediately to trigger RunMap animation
      setAnimatedGeoData(selectedGeoData);

      // For single run, trigger animation by incrementing the trigger
      if (runIds.length === 1) {
        setAnimationTrigger((prev) => prev + 1);
      }

      // Update view state
      setViewState({
        ...selectedBounds,
      });
      setTitle(titleForShow(lastRun));
      scrollToMap();
    },
    [runs]
  );

  // Auto locate activity when singleRunId is set and activities are loaded
  useEffect(() => {
    if (singleRunId !== null && activities.length > 0) {
      // Check if the run exists in our activities
      const runExists = activities.some((run) => run.run_id === singleRunId);
      if (runExists) {
        // Automatically simulate clicking the single run
        locateActivity([singleRunId]);
      } else {
        // If run doesn't exist, clear the hash and show a warning
        console.warn(`Run with ID ${singleRunId} not found in activities`);
        window.history.replaceState(null, '', window.location.pathname);
        setSingleRunId(null);
      }
    }
  }, [singleRunId, activities, locateActivity]);

  // Update bounds when geoData changes
  useEffect(() => {
    setViewState((prev) => ({
      ...prev,
      ...bounds,
    }));
  }, [bounds]);

  // Animate geoData when runs change
  useEffect(() => {
    const runsNum = runs.length;
    if (runsNum === 0) {
      setAnimatedGeoData(geoData);
      return;
    }

    const sliceNume = runsNum >= 8 ? Math.ceil(runsNum / 8) : 1;
    let i = sliceNume;

    const id = setInterval(() => {
      if (i >= runsNum) {
        clearInterval(id);
        intervalIdRef.current = null;
        setAnimatedGeoData(geoData);
        return;
      }

      const tempRuns = runs.slice(0, i);
      setAnimatedGeoData(geoJsonForRuns(tempRuns));
      i += sliceNume;
    }, 300);

    intervalIdRef.current = id;

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [runs, geoData]); // Remove intervalId from deps to avoid stale closure

  useEffect(() => {
    if (year !== 'Total') {
      return;
    }

    let svgStat = document.getElementById('svgStat');
    if (!svgStat) {
      return;
    }

    const handleClick = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === 'path') {
        // Use querySelector to get the <desc> element and the <title> element.
        const descEl = target.querySelector('desc');
        if (descEl) {
          // If the runId exists in the <desc> element, it means that a running route has been clicked.
          const runId = Number(descEl.innerHTML);
          if (!runId) {
            return;
          }
          locateActivity([runId]);
          return;
        }

        const titleEl = target.querySelector('title');
        if (titleEl) {
          // If the runDate exists in the <title> element, it means that a date square has been clicked.
          const [runDate] = titleEl.innerHTML.match(
            /\d{4}-\d{1,2}-\d{1,2}/
          ) || [`${+thisYear + 1}`];
          const runIDsOnDate = runs
            .filter((r) => r.start_date_local.slice(0, 10) === runDate)
            .map((r) => r.run_id);
          if (!runIDsOnDate.length) {
            return;
          }
          locateActivity(runIDsOnDate);
        }
      }
    };
    svgStat.addEventListener('click', handleClick);
    return () => {
      svgStat && svgStat.removeEventListener('click', handleClick);
    };
  }, [year]);

  return (
    <Layout>
      <div className="w-full lg:w-1/3">
        <h1 className="my-12 mt-6 text-5xl font-extrabold italic">
          <a href="/">{siteTitle}</a>
        </h1>
        {(viewState.zoom ?? 0) <= 3 && IS_CHINESE ? (
          <LocationStat
            changeYear={changeYear}
            changeCity={changeCity}
            changeTitle={changeTitle}
          />
        ) : (
          <YearsStat year={year} onClick={changeYear} />
        )}
      </div>
      <div className="w-full lg:w-2/3" id="map-container">
        <RunMap
          title={title}
          viewState={viewState}
          geoData={animatedGeoData}
          setViewState={setViewState}
          changeYear={changeYear}
          thisYear={year}
          animationTrigger={animationTrigger}
        />
        {year === 'Total' ? (
          <SVGStat />
        ) : (
          <RunTable
            runs={runs}
            locateActivity={locateActivity}
            setActivity={setActivity}
            runIndex={runIndex}
            setRunIndex={setRunIndex}
          />
        )}
      </div>
      {/* Enable Audiences in Vercel Analytics: https://vercel.com/docs/concepts/analytics/audiences/quickstart */}
      {import.meta.env.VERCEL && <Analytics />}
    </Layout>
  );
};

export default Index;
