import { useMemo } from 'react';
import {
  SHOW_TRAINING_ALERTS,
  MONTHLY_MILEAGE_THRESHOLD,
  WEEKLY_INCREASE_THRESHOLD,
  TRAINING_ALERT_MESSAGES,
} from '@/utils/const';
import { Activity } from '@/utils/utils';

interface TrainingAlertsProps {
  activities: Activity[];
}

interface Alert {
  id: string;
  type: 'warning' | 'info';
  message: string;
}

// Returns ISO week info using local date (not UTC) to match start_date_local
const getWeekInfo = (
  date: Date
): { year: number; week: number; key: string } => {
  // Create a copy using local date components
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  // ISO week starts on Monday (day 1), Sunday is day 7
  const dayNum = d.getDay() || 7;
  // Set to nearest Thursday (ISO week date algorithm)
  d.setDate(d.getDate() + 4 - dayNum);
  const year = d.getFullYear();
  const yearStart = new Date(year, 0, 1);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7
  );
  return {
    year,
    week: weekNo,
    key: `${year}-W${weekNo.toString().padStart(2, '0')}`,
  };
};

// Check if two weeks are consecutive (handles year boundaries)
const areConsecutiveWeeks = (
  week1: { year: number; week: number },
  week2: { year: number; week: number }
): boolean => {
  // Same year, consecutive weeks
  if (week1.year === week2.year && week1.week === week2.week + 1) {
    return true;
  }
  // Year boundary: week1 is W01 of new year, week2 is last week of previous year
  if (week1.year === week2.year + 1 && week1.week === 1 && week2.week >= 52) {
    return true;
  }
  return false;
};

const getMonthKey = (date: Date): string => {
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
};

const TrainingAlerts = ({ activities }: TrainingAlertsProps) => {
  const alerts = useMemo(() => {
    if (!SHOW_TRAINING_ALERTS || activities.length === 0) {
      return [];
    }

    const alertList: Alert[] = [];

    const weeklyDistance: Record<
      string,
      { distance: number; year: number; week: number }
    > = {};
    const monthlyDistance: Record<string, number> = {};

    activities.forEach((activity) => {
      const activityDate = new Date(activity.start_date_local);
      const weekInfo = getWeekInfo(activityDate);
      const monthKey = getMonthKey(activityDate);
      const distanceKm = (activity.distance || 0) / 1000;

      if (!weeklyDistance[weekInfo.key]) {
        weeklyDistance[weekInfo.key] = {
          distance: 0,
          year: weekInfo.year,
          week: weekInfo.week,
        };
      }
      weeklyDistance[weekInfo.key].distance += distanceKm;
      monthlyDistance[monthKey] = (monthlyDistance[monthKey] || 0) + distanceKm;
    });

    const months = Object.keys(monthlyDistance).sort().reverse();
    const latestMonth = months[0];

    if (
      latestMonth &&
      monthlyDistance[latestMonth] > MONTHLY_MILEAGE_THRESHOLD
    ) {
      alertList.push({
        id: 'monthly-overtraining',
        type: 'warning',
        message: TRAINING_ALERT_MESSAGES.MONTHLY_OVERTRAINING.replace(
          '{threshold}',
          MONTHLY_MILEAGE_THRESHOLD.toString()
        ),
      });
    }

    // Sort weeks by year and week number (handles year boundaries correctly)
    const sortedWeeks = Object.entries(weeklyDistance).sort((a, b) => {
      if (a[1].year !== b[1].year) return b[1].year - a[1].year;
      return b[1].week - a[1].week;
    });

    if (sortedWeeks.length >= 2) {
      const [, latestWeekData] = sortedWeeks[0];
      const [, previousWeekData] = sortedWeeks[1];

      // Only alert if weeks are actually consecutive
      if (
        areConsecutiveWeeks(
          { year: latestWeekData.year, week: latestWeekData.week },
          { year: previousWeekData.year, week: previousWeekData.week }
        ) &&
        previousWeekData.distance > 0
      ) {
        const increasePercent =
          ((latestWeekData.distance - previousWeekData.distance) /
            previousWeekData.distance) *
          100;

        if (increasePercent > WEEKLY_INCREASE_THRESHOLD) {
          alertList.push({
            id: 'weekly-increase',
            type: 'warning',
            message: TRAINING_ALERT_MESSAGES.WEEKLY_INCREASE.replace(
              '{threshold}',
              WEEKLY_INCREASE_THRESHOLD.toString()
            ),
          });
        }
      }
    }

    return alertList;
  }, [activities]);

  if (!SHOW_TRAINING_ALERTS || alerts.length === 0) {
    return null;
  }

  return (
    <div className="my-4">
      <h3 className="mb-2 text-lg font-semibold italic">
        {TRAINING_ALERT_MESSAGES.TRAINING_ALERTS_TITLE}
      </h3>
      <div className="space-y-2">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            role="alert"
            aria-live="polite"
            className={`rounded-lg border p-3 text-sm ${
              alert.type === 'warning'
                ? 'border-amber-500/50 bg-amber-500/10 text-amber-600 dark:text-amber-400'
                : 'border-blue-500/50 bg-blue-500/10 text-blue-600 dark:text-blue-400'
            }`}
          >
            <span className="mr-2" aria-hidden="true">
              {alert.type === 'warning' ? '⚠️' : 'ℹ️'}
            </span>
            <span className="sr-only">
              {alert.type === 'warning' ? 'Warning: ' : 'Info: '}
            </span>
            {alert.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrainingAlerts;
