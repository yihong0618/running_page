import { useStaticQuery, graphql } from 'gatsby';

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
  return allActivitiesJson.nodes;
};

export default useActivities;
