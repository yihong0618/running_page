import { useMemo } from 'react';
import { locationForRun, titleForRun } from '@/utils/utils';
import activities from '@/static/activities.json';

// standardize country names for consistency between mapbox and activities data
const standardizeCountryName = (country: string): string => {
  switch (country) {
    case '英国 / 英國':
      return '英国';
    case '美利坚合众国/美利堅合眾國':
      return '美国';
    default:
      return country;
  }
};

const useActivities = () => {
  const processedData = useMemo(() => {
    const cities: Record<string, number> = {};
    const runPeriod: Record<string, number> = {};
    const provinces: Set<string> = new Set();
    const countries: Set<string> = new Set();
    const years: Set<string> = new Set();

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
        cities[city] = cities[city]
          ? cities[city] + run.distance
          : run.distance;
      }
      if (province) provinces.add(province);
      if (country) countries.add(standardizeCountryName(country));
      const year = run.start_date_local.slice(0, 4);
      years.add(year);
    });

    const yearsArray = [...years].sort().reverse();
    const thisYear = yearsArray[0] || '';

    return {
      activities,
      years: yearsArray,
      countries: [...countries],
      provinces: [...provinces],
      cities,
      runPeriod,
      thisYear,
    };
  }, []); // Empty dependency array since activities is static

  return processedData;
};

export default useActivities;
