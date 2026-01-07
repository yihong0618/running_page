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
  type: 'warning' | 'info';
  message: string;
}

const getWeekNumber = (date: Date): string => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${weekNo.toString().padStart(2, '0')}`;
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

    const weeklyMileage: Record<string, number> = {};
    const monthlyMileage: Record<string, number> = {};

    activities.forEach((activity) => {
      const activityDate = new Date(activity.start_date_local);
      const weekKey = getWeekNumber(activityDate);
      const monthKey = getMonthKey(activityDate);
      const distanceKm = (activity.distance || 0) / 1000;

      weeklyMileage[weekKey] = (weeklyMileage[weekKey] || 0) + distanceKm;
      monthlyMileage[monthKey] = (monthlyMileage[monthKey] || 0) + distanceKm;
    });

    const months = Object.keys(monthlyMileage).sort().reverse();
    const latestMonth = months[0];

    if (latestMonth && monthlyMileage[latestMonth] > MONTHLY_MILEAGE_THRESHOLD) {
      alertList.push({
        type: 'warning',
        message: TRAINING_ALERT_MESSAGES.MONTHLY_OVERTRAINING.replace(
          '{threshold}',
          MONTHLY_MILEAGE_THRESHOLD.toString()
        ),
      });
    }

    const weeks = Object.keys(weeklyMileage).sort().reverse();

    if (weeks.length >= 2) {
      const latestWeek = weeks[0];
      const previousWeek = weeks[1];
      const latestWeekMileage = weeklyMileage[latestWeek] || 0;
      const previousWeekMileage = weeklyMileage[previousWeek] || 0;

      if (previousWeekMileage > 0) {
        const increasePercent = ((latestWeekMileage - previousWeekMileage) / previousWeekMileage) * 100;

        if (increasePercent > WEEKLY_INCREASE_THRESHOLD) {
          alertList.push({
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
        {alerts.map((alert, index) => (
          <div
            key={index}
            className={`rounded-lg border p-3 text-sm ${
              alert.type === 'warning'
                ? 'border-amber-500/50 bg-amber-500/10 text-amber-600 dark:text-amber-400'
                : 'border-blue-500/50 bg-blue-500/10 text-blue-600 dark:text-blue-400'
            }`}
          >
            <span className="mr-2">{alert.type === 'warning' ? '⚠️' : 'ℹ️'}</span>
            {alert.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrainingAlerts;
