import { locationForRun, titleForRun, Activity } from '@/utils/utils';
import { useEffect, useState } from 'react';

const emptyStat = {
  activities: [],
  years: [],
  countries: [],
  provinces: [],
  cities: {},
  runPeriod: {},
  thisYear: '',
}

const analyzeActivities = (activities: Activity[]) => {
  const cities: Record<string, number> = {};
  const runPeriod: Record<string, number> = {};
  const provinces: Set<string> = new Set();
  const countries: Set<string> = new Set();
  let years: Set<string> = new Set();
  let thisYear = '';

  activities.forEach((run) => {
    const location = locationForRun(run);

    const periodName = titleForRun(run);
    if (periodName) {
      runPeriod[periodName] = runPeriod[periodName]
        ? runPeriod[periodName] + 1
        : 1;
    }

    const { city, province, country } = location;
    // drop only one char city
    if (city.length > 1) {
      cities[city] = cities[city] ? cities[city] + run.distance : run.distance;
    }
    if (province) provinces.add(province);
    if (country) countries.add(country);
    const year = run.start_date_local.slice(0, 4);
    years.add(year);
  });

  let yearsArray = [...years].sort().reverse();
  if (years) [thisYear] = yearsArray; // set current year as first one of years array

  return {
    activities,
    years: yearsArray,
    countries: [...countries],
    provinces: [...provinces],
    cities,
    runPeriod,
    thisYear,
  };
};

type Stat = ReturnType<typeof analyzeActivities>;

function useActivities(): [Stat, boolean] {
  const [data, setData] = useState<Stat>(emptyStat);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    import('@/static/activities.json').then((res) => {
      setData(analyzeActivities(res.default));
      setLoading(false);
    });
  }, []);

  return [data, loading];
}

export default useActivities;
