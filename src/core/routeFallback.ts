import polyline from '@mapbox/polyline';

type MappedActivity = {
  start_date: string;
  summary_polyline?: string | null;
};

const hasRoute = (activity: MappedActivity): boolean => {
  if (!activity.summary_polyline) return false;
  try {
    const points = polyline.decode(activity.summary_polyline);
    return (
      points.length >= 2 &&
      points.every(
        ([lat, lng]) =>
          Number.isFinite(lat) &&
          Number.isFinite(lng) &&
          Math.abs(lat) <= 90 &&
          Math.abs(lng) <= 180
      )
    );
  } catch {
    return false;
  }
};

/** Choose a route for display without copying it into the selected activity. */
export function routeForActivity<T extends MappedActivity>(
  selected: T,
  activities: readonly T[]
): T | null {
  if (hasRoute(selected)) return selected;
  const selectedTime = Date.parse(selected.start_date.replace(' ', 'T'));
  let latest: T | null = null;
  let latestTime = -Infinity;
  for (const activity of activities) {
    const time = Date.parse(activity.start_date.replace(' ', 'T'));
    if (time < selectedTime && time > latestTime && hasRoute(activity)) {
      latest = activity;
      latestTime = time;
    }
  }
  return latest;
}
