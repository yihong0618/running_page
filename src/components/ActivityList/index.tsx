import React, { lazy, useState, Suspense, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import activities from '@/static/activities.json';
import styles from './style.module.css';
import { ACTIVITY_TOTAL } from '@/utils/const';
import { totalStat } from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';
import { SHOW_ELEVATION_GAIN, HOME_PAGE_TITLE } from '@/utils/const';
import RoutePreview from '@/components/RoutePreview';
import { Activity } from '@/utils/utils';

const MonthOfLifeSvg = (sportType: string) => {
  const path = sportType === 'all' ? './mol.svg' : `./mol_${sportType}.svg`;
  return lazy(() => loadSvgComponent(totalStat, path));
};

const RunningSvg = MonthOfLifeSvg('running');
const WalkingSvg = MonthOfLifeSvg('walking');
const HikingSvg = MonthOfLifeSvg('hiking');
const CyclingSvg = MonthOfLifeSvg('cycling');
const SwimmingSvg = MonthOfLifeSvg('swimming');
const SkiingSvg = MonthOfLifeSvg('skiing');
const AllSvg = MonthOfLifeSvg('all');

interface ActivitySummary {
  totalDistance: number;
  totalTime: number;
  totalElevationGain: number;
  count: number;
  dailyDistances: number[];
  maxDistance: number;
  maxSpeed: number;
  location: string;
  totalHeartRate: number; // Add heart rate statistics
  heartRateCount: number;
  activities: Activity[]; // Add activities array for day interval
}

interface DisplaySummary {
  totalDistance: number;
  averageSpeed: number;
  totalTime: number;
  count: number;
  maxDistance: number;
  maxSpeed: number;
  location: string;
  totalElevationGain?: number;
  averageHeartRate?: number; // Add heart rate display
}

interface ChartData {
  day: number;
  distance: string;
}

interface ActivityCardProps {
  period: string;
  summary: DisplaySummary;
  dailyDistances: number[];
  interval: string;
  activities?: Activity[]; // Add activities for day interval
}

interface ActivityGroups {
  [key: string]: ActivitySummary;
}

type IntervalType = 'year' | 'month' | 'week' | 'day' | 'life';

const ActivityCard: React.FC<ActivityCardProps> = ({
  period,
  summary,
  dailyDistances,
  interval,
  activities = [],
}) => {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleCardClick = () => {
    if (interval === 'day' && activities.length > 0) {
      setIsFlipped(!isFlipped);
    }
  };
  const generateLabels = (): number[] => {
    if (interval === 'month') {
      const [year, month] = period.split('-').map(Number);
      const daysInMonth = new Date(year, month, 0).getDate(); // Get the number of days in the month
      return Array.from({ length: daysInMonth }, (_, i) => i + 1);
    } else if (interval === 'week') {
      return Array.from({ length: 7 }, (_, i) => i + 1);
    } else if (interval === 'year') {
      return Array.from({ length: 12 }, (_, i) => i + 1); // Generate months 1 to 12
    }
    return [];
  };

  const data: ChartData[] = generateLabels().map((day) => ({
    day,
    distance: (dailyDistances[day - 1] || 0).toFixed(2), // Keep two decimal places
  }));

  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
  };

  const formatPace = (speed: number): string => {
    if (speed === 0) return '0:00 min/km';
    const pace = 60 / speed; // min/km
    const totalSeconds = Math.round(pace * 60); // Total seconds per km
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds} min/km`;
  };

  // Calculate Y-axis maximum value and ticks
  const yAxisMax = Math.ceil(
    Math.max(...data.map((d) => parseFloat(d.distance))) + 10
  ); // Round up and add buffer
  const yAxisTicks = Array.from(
    { length: Math.ceil(yAxisMax / 5) + 1 },
    (_, i) => i * 5
  ); // Generate arithmetic sequence

  return (
    <div
      className={`${styles.activityCard} ${interval === 'day' ? styles.activityCardFlippable : ''}`}
      onClick={handleCardClick}
      style={{
        cursor:
          interval === 'day' && activities.length > 0 ? 'pointer' : 'default',
      }}
    >
      <div className={`${styles.cardInner} ${isFlipped ? styles.flipped : ''}`}>
        {/* Front side - Activity details */}
        <div className={styles.cardFront}>
          <h2 className={styles.activityName}>{period}</h2>
          <div className={styles.activityDetails}>
            <p>
              <strong>{ACTIVITY_TOTAL.TOTAL_DISTANCE_TITLE}:</strong>{' '}
              {summary.totalDistance.toFixed(2)} km
            </p>
            {SHOW_ELEVATION_GAIN &&
              summary.totalElevationGain !== undefined && (
                <p>
                  <strong>{ACTIVITY_TOTAL.TOTAL_ELEVATION_GAIN_TITLE}:</strong>{' '}
                  {summary.totalElevationGain.toFixed(0)} m
                </p>
              )}
            <p>
              <strong>{ACTIVITY_TOTAL.AVERAGE_SPEED_TITLE}:</strong>{' '}
              {formatPace(summary.averageSpeed)}
            </p>
            <p>
              <strong>{ACTIVITY_TOTAL.TOTAL_TIME_TITLE}:</strong>{' '}
              {formatTime(summary.totalTime)}
            </p>
            {summary.averageHeartRate !== undefined && (
              <p>
                <strong>{ACTIVITY_TOTAL.AVERAGE_HEART_RATE_TITLE}:</strong>{' '}
                {summary.averageHeartRate.toFixed(0)} bpm
              </p>
            )}
            {interval !== 'day' && (
              <>
                <p>
                  <strong>{ACTIVITY_TOTAL.ACTIVITY_COUNT_TITLE}:</strong>{' '}
                  {summary.count}
                </p>
                <p>
                  <strong>{ACTIVITY_TOTAL.MAX_DISTANCE_TITLE}:</strong>{' '}
                  {summary.maxDistance.toFixed(2)} km
                </p>
                <p>
                  <strong>{ACTIVITY_TOTAL.MAX_SPEED_TITLE}:</strong>{' '}
                  {formatPace(summary.maxSpeed)}
                </p>
              </>
            )}
            {['month', 'week', 'year'].includes(interval) && (
              <div className={styles.chart}>
                <ResponsiveContainer>
                  <BarChart
                    data={data}
                    margin={{ top: 20, right: 20, left: -20, bottom: 5 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="var(--color-run-row-hover-background)"
                    />
                    <XAxis
                      dataKey="day"
                      tick={{ fill: 'var(--color-run-table-thead)' }}
                    />
                    <YAxis
                      label={{
                        value: 'km',
                        angle: -90,
                        position: 'insideLeft',
                        fill: 'var(--color-run-table-thead)',
                      }}
                      domain={[0, yAxisMax]}
                      ticks={yAxisTicks}
                      tick={{ fill: 'var(--color-run-table-thead)' }}
                    />
                    <Tooltip
                      formatter={(value) => `${value} km`}
                      contentStyle={{
                        backgroundColor:
                          'var(--color-run-row-hover-background)',
                        border:
                          '1px solid var(--color-run-row-hover-background)',
                        color: 'var(--color-run-table-thead)',
                      }}
                      labelStyle={{ color: 'var(--color-primary)' }}
                    />
                    <Bar dataKey="distance" fill="var(--color-primary)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Back side - Route preview */}
        {interval === 'day' && activities.length > 0 && (
          <div className={styles.cardBack}>
            <div className={styles.routeContainer}>
              <RoutePreview activities={activities} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ActivityList: React.FC = () => {
  const [interval, setInterval] = useState<IntervalType>('month');
  const [sportType, setSportType] = useState<string>('all');
  const [sportTypeOptions, setSportTypeOptions] = useState<string[]>([]);

  useEffect(() => {
    const sportTypeSet = new Set(activities.map((activity) => activity.type));
    if (sportTypeSet.has('Run')) {
      sportTypeSet.delete('Run');
      sportTypeSet.add('running');
    }
    if (sportTypeSet.has('Walk')) {
      sportTypeSet.delete('Walk');
      sportTypeSet.add('walking');
    }
    if (sportTypeSet.has('Ride')) {
      sportTypeSet.delete('Ride');
      sportTypeSet.add('cycling');
    }
    const uniqueSportTypes = [...sportTypeSet];
    uniqueSportTypes.unshift('all');
    setSportTypeOptions(uniqueSportTypes);
  }, []);

  // 添加useEffect监听interval变化
  useEffect(() => {
    if (interval === 'life' && sportType !== 'all') {
      setSportType('all');
    }
  }, [interval, sportType]);

  const navigate = useNavigate();

  const handleHomeClick = () => {
    navigate('/');
  };

  const toggleInterval = (newInterval: IntervalType): void => {
    setInterval(newInterval);
  };

  const convertTimeToSeconds = (time: string): number => {
    const [hours, minutes, seconds] = time.split(':').map(Number);
    return hours * 3600 + minutes * 60 + seconds;
  };

  const groupActivities = (
    interval: IntervalType,
    sportType: string
  ): ActivityGroups => {
    return (activities as Activity[])
      .filter((activity) => {
        if (sportType === 'all') {
          return true;
        }
        if (sportType === 'running') {
          return activity.type === 'running' || activity.type === 'Run';
        }
        if (sportType === 'walking') {
          return activity.type === 'walking' || activity.type === 'Walk';
        }
        if (sportType === 'cycling') {
          return activity.type === 'cycling' || activity.type === 'Ride';
        }
        return activity.type === sportType;
      })
      .reduce((acc: ActivityGroups, activity) => {
        const date = new Date(activity.start_date_local);
        let key: string;
        let index: number;
        switch (interval) {
          case 'year':
            key = date.getFullYear().toString();
            index = date.getMonth(); // Return current month (0-11)
            break;
          case 'month':
            key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`; // Zero padding
            index = date.getDate() - 1; // Return current day (0-30)
            break;
          case 'week': {
            const currentDate = new Date(date.valueOf());
            currentDate.setDate(
              currentDate.getDate() + 4 - (currentDate.getDay() || 7)
            ); // Set to nearest Thursday (ISO weeks defined by Thursday)
            const yearStart = new Date(currentDate.getFullYear(), 0, 1);
            const weekNum = Math.ceil(
              ((currentDate.getTime() - yearStart.getTime()) / 86400000 + 1) / 7
            );
            key = `${currentDate.getFullYear()}-W${weekNum.toString().padStart(2, '0')}`;
            index = (date.getDay() + 6) % 7; // Return current day (0-6, Monday-Sunday)
            break;
          }
          case 'day':
            key = date.toLocaleDateString('zh').replaceAll('/', '-'); // Format date as YYYY-MM-DD
            index = 0; // Return 0
            break;
          default:
            key = date.getFullYear().toString();
            index = 0; // Default return 0
        }

        if (!acc[key])
          acc[key] = {
            totalDistance: 0,
            totalTime: 0,
            totalElevationGain: 0,
            count: 0,
            dailyDistances: [],
            maxDistance: 0,
            maxSpeed: 0,
            location: '',
            totalHeartRate: 0,
            heartRateCount: 0,
            activities: [],
          };

        const distanceKm = activity.distance / 1000; // Convert to kilometers
        const timeInSeconds = convertTimeToSeconds(activity.moving_time);
        const speedKmh =
          timeInSeconds > 0 ? distanceKm / (timeInSeconds / 3600) : 0;

        acc[key].totalDistance += distanceKm;
        acc[key].totalTime += timeInSeconds;

        if (SHOW_ELEVATION_GAIN && activity.elevation_gain) {
          acc[key].totalElevationGain += activity.elevation_gain;
        }

        // Heart rate statistics
        if (activity.average_heartrate) {
          acc[key].totalHeartRate += activity.average_heartrate;
          acc[key].heartRateCount += 1;
        }

        acc[key].count += 1;

        // Store activity for day interval (for route display)
        if (interval === 'day') {
          acc[key].activities.push(activity);
        }

        // Accumulate daily distances
        acc[key].dailyDistances[index] =
          (acc[key].dailyDistances[index] || 0) + distanceKm;

        if (distanceKm > acc[key].maxDistance)
          acc[key].maxDistance = distanceKm;
        if (speedKmh > acc[key].maxSpeed) acc[key].maxSpeed = speedKmh;

        if (interval === 'day')
          acc[key].location = activity.location_country || '';

        return acc;
      }, {});
  };

  const activitiesByInterval = groupActivities(interval, sportType);

  return (
    <div className={styles.activityList}>
      <div className={styles.filterContainer}>
        <button className={styles.smallHomeButton} onClick={handleHomeClick}>
          {HOME_PAGE_TITLE}
        </button>
        <select
          onChange={(e) => setSportType(e.target.value)}
          value={sportType}
        >
          {sportTypeOptions.map((type) => (
            <option
              key={type}
              value={type}
              disabled={interval === 'life' && type !== 'all'}
            >
              {type}
            </option>
          ))}
        </select>
        <select
          onChange={(e) => toggleInterval(e.target.value as IntervalType)}
          value={interval}
        >
          <option value="year">{ACTIVITY_TOTAL.YEARLY_TITLE}</option>
          <option value="month">{ACTIVITY_TOTAL.MONTHLY_TITLE}</option>
          <option value="week">{ACTIVITY_TOTAL.WEEKLY_TITLE}</option>
          <option value="day">{ACTIVITY_TOTAL.DAILY_TITLE}</option>
          <option value="life">Life</option>
        </select>
      </div>

      {interval === 'life' && (
        <div className={styles.lifeContainer}>
          <Suspense fallback={<div>Loading SVG...</div>}>
            {(sportType === 'running' || sportType === 'Run') && <RunningSvg />}
            {sportType === 'walking' && <WalkingSvg />}
            {sportType === 'hiking' && <HikingSvg />}
            {sportType === 'cycling' && <CyclingSvg />}
            {sportType === 'swimming' && <SwimmingSvg />}
            {sportType === 'skiing' && <SkiingSvg />}
            {sportType === 'all' && <AllSvg />}
          </Suspense>
        </div>
      )}

      {interval !== 'life' && (
        <div className={styles.summaryContainer}>
          {Object.entries(activitiesByInterval)
            .sort(([a], [b]) => {
              if (interval === 'day') {
                return new Date(b).getTime() - new Date(a).getTime(); // Sort by date
              } else if (interval === 'week') {
                const [yearA, weekA] = a.split('-W').map(Number);
                const [yearB, weekB] = b.split('-W').map(Number);
                return yearB - yearA || weekB - weekA; // Sort by year and week number
              } else {
                const [yearA, monthA = 0] = a.split('-').map(Number);
                const [yearB, monthB = 0] = b.split('-').map(Number);
                return yearB - yearA || monthB - monthA; // Sort by year and month
              }
            })
            .map(([period, summary]) => (
              <ActivityCard
                key={period}
                period={period}
                summary={{
                  totalDistance: summary.totalDistance,
                  averageSpeed: summary.totalTime
                    ? summary.totalDistance / (summary.totalTime / 3600)
                    : 0,
                  totalTime: summary.totalTime,
                  count: summary.count,
                  maxDistance: summary.maxDistance,
                  maxSpeed: summary.maxSpeed,
                  location: summary.location,
                  totalElevationGain: SHOW_ELEVATION_GAIN
                    ? summary.totalElevationGain
                    : undefined,
                  averageHeartRate:
                    summary.heartRateCount > 0
                      ? summary.totalHeartRate / summary.heartRateCount
                      : undefined,
                }}
                dailyDistances={summary.dailyDistances}
                interval={interval}
                activities={interval === 'day' ? summary.activities : undefined}
              />
            ))}
        </div>
      )}
    </div>
  );
};

export default ActivityList;
