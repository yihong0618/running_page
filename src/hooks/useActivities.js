import { useStaticQuery, graphql } from 'gatsby';
import { locationForRun, titleForRun } from 'src/utils/utils';

const useActivities = () => {
  const { allActivitiesJson } = useStaticQuery(
    graphql`
      query AllActivities {
        allActivitiesJson {
          nodes {
            id
            distance
            name
            run_id
            moving_time
            type
            average_speed
            location_country
            start_date
            start_date_local
            streak
            summary_polyline
          }
        }
      }
    `
  );

  const activities = allActivitiesJson.nodes;
  const cities = {};
  const runPeriod = {};
  let provinces = [];
  let countries = [];
  let years = [];
  let thisYear = '';

  activities.forEach((run) => {
    const location = locationForRun(run);
    const periodName = titleForRun(run);
    if (periodName) {
      runPeriod[periodName] =
        runPeriod[periodName] === undefined ? 1 : runPeriod[periodName] + 1;
    }
    const { city, province, country } = location;
    // drop only one char city
    if (city.length > 1) {
      cities[city] =
        cities[city] === undefined ? run.distance : cities[city] + run.distance;
    }
    if (province) {
      provinces.push(province);
    }
    if (country) {
      countries.push(country);
    }
    const y = run.start_date_local.slice(0, 4);
    years.push(y);
  });
  years = [...new Set(years)].sort().reverse();
  provinces = [...new Set(provinces)];
  countries = [...new Set(countries)];

  if (years) {
    [thisYear] = years;
  }

  return {
    activities,
    years,
    provinces,
    countries,
    cities,
    runPeriod,
    thisYear,
  };
};

export default useActivities;
