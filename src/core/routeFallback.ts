import polyline from '@mapbox/polyline';

type MappedActivity = {
  start_date_local: string;
  summary_polyline?: string | null;
};

const routeCache = new WeakMap<
  MappedActivity,
  { polyline: MappedActivity['summary_polyline']; valid: boolean }
>();

export const hasRoute = (activity: MappedActivity): boolean => {
  const cached = routeCache.get(activity);
  if (cached && cached.polyline === activity.summary_polyline)
    return cached.valid;
  const valid = validateRoute(activity);
  routeCache.set(activity, { polyline: activity.summary_polyline, valid });
  return valid;
};

const validateRoute = (activity: MappedActivity): boolean => {
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
  let latest: T | null = null;
  let latestLocal = '';
  for (const activity of activities) {
    // The generator exports zero-padded local timestamps in this same order.
    const local = activity.start_date_local;
    if (
      local < selected.start_date_local &&
      local > latestLocal &&
      hasRoute(activity)
    ) {
      latest = activity;
      latestLocal = local;
    }
  }
  return latest;
}
