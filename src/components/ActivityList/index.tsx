import React, { lazy, useState, Suspense, useEffect, useRef } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import VirtualList from 'rc-virtual-list';
import { useNavigate } from 'react-router-dom';
import activities from '@/static/activities.json';
import styles from './style.module.css';
import { ACTIVITY_TOTAL } from '@/utils/const';
import { totalStat } from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';
import { SHOW_ELEVATION_GAIN, HOME_PAGE_TITLE } from '@/utils/const';
import RoutePreview from '@/components/RoutePreview';
import { Activity } from '@/utils/utils';
// import VariableSizeList from '../vitualList';
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
  const [calcGroup, setCalcGroup] = useState([])
  const [Row, setRow] = useState(null)

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
  // Build a pure data list (not JSX) so we can group into rows for VirtualList
  const dataList = Object.entries(activitiesByInterval)
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
    .map(([period, summary]) => ({ period, summary }));

  console.log('dataList', dataList);

  const itemWidth = 280
  const gap = 20
  const containerRef = useRef<HTMLDivElement | null>(null);
  const filterRef = useRef<HTMLDivElement | null>(null);
  const [itemsPerRow, setItemsPerRow] = useState(0);
  const [rowHeight, setRowHeight] = useState<number>(360); // will be measured by sampleRef
  const sampleRef = useRef<HTMLDivElement | null>(null);
  const [listHeight, setListHeight] = useState<number>(500);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    console.log('123container', container);
    const calculateItemsPerRow = () => {
      const containerWidth = container.clientWidth;
      // 计算一行能放多少个（考虑间距）
      const count = Math.floor((containerWidth + gap) / (itemWidth + gap));
      console.log('123count', count);
      setItemsPerRow(count);
    };

    // 立即计算一次
    calculateItemsPerRow();

    // 使用ResizeObserver监听容器尺寸变化
    const resizeObserver = new ResizeObserver(calculateItemsPerRow);
    resizeObserver.observe(container);

    return () => resizeObserver.disconnect();
  }, [itemWidth, gap]);

  // compute list height = viewport height - filter container height
  useEffect(() => {
    const updateListHeight = () => {
      const filterH = filterRef.current?.clientHeight || 0;
      const h = Math.max(100, window.innerHeight - filterH); // ensure some minimum
      setListHeight(h);
    };

    // initial
    updateListHeight();

    // window resize
    window.addEventListener('resize', updateListHeight);

    // observe filter size changes
    const ro = new ResizeObserver(updateListHeight);
    if (filterRef.current) ro.observe(filterRef.current);

    return () => {
      window.removeEventListener('resize', updateListHeight);
      ro.disconnect();
    };
  }, []);

  // measure representative card height using a hidden sample and ResizeObserver
  useEffect(() => {
    const el = sampleRef.current;
    if (!el) return;
    const update = () => {
      const h = el.offsetHeight;
      if (h && h !== rowHeight) setRowHeight(h);
    };
    // initial
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [dataList, rowHeight]);
  useEffect(() => {
    if (itemsPerRow < 1) return
    const groupLength = Math.ceil(dataList.length / itemsPerRow);
    const calc = () => {
      const calcGroup: Array<any> = []
      for (let i = 0; i < groupLength; i++) {
        const start = i * itemsPerRow;
        const end = start + itemsPerRow;
        const curGroup = dataList.slice(start, end);
        calcGroup.push(curGroup);
      }
      return calcGroup
    }
    console.log('123groupLength', groupLength);
    const calcGroupRows = calc()
    setCalcGroup(calcGroupRows)
    const Row = ({ index }) => calcGroupRows[index];
    setRow(() => Row)
    debugger
  }, [itemsPerRow, interval, sportType]);



  console.log('calcGroup', calcGroup);
  console.log('itemsPerRow', itemsPerRow)
  return (
    <div className={styles.activityList}>
      <div className={styles.filterContainer} ref={filterRef}>
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
        <div className={styles.summaryContainer} ref={containerRef}>
          {/* hidden sample card for measuring row height */}
          <div style={{ position: 'absolute', visibility: 'hidden', pointerEvents: 'none', height: 'auto' }} ref={sampleRef}>
            {dataList[0] && (
              <ActivityCard
                key={dataList[0].period}
                period={dataList[0].period}
                summary={{
                  totalDistance: dataList[0].summary.totalDistance,
                  averageSpeed: dataList[0].summary.totalTime
                    ? dataList[0].summary.totalDistance / (dataList[0].summary.totalTime / 3600)
                    : 0,
                  totalTime: dataList[0].summary.totalTime,
                  count: dataList[0].summary.count,
                  maxDistance: dataList[0].summary.maxDistance,
                  maxSpeed: dataList[0].summary.maxSpeed,
                  location: dataList[0].summary.location,
                  totalElevationGain: SHOW_ELEVATION_GAIN
                    ? dataList[0].summary.totalElevationGain
                    : undefined,
                  averageHeartRate:
                    dataList[0].summary.heartRateCount > 0
                      ? dataList[0].summary.totalHeartRate / dataList[0].summary.heartRateCount
                      : undefined,
                }}
                dailyDistances={dataList[0].summary.dailyDistances}
                interval={interval}
                activities={interval === 'day' ? dataList[0].summary.activities : undefined}
              />
            )}
          </div>
          {/* <VariableSizeList
            height="calc(100vh - 86px)"
            width="100%"
            itemCount={calcGroup.length}
            isDynamic
          >
          {Row}
          </VariableSizeList> */}
          <VirtualList
            data={calcGroup}
            height={listHeight}
            itemHeight={rowHeight}
            itemKey={(row, idx) => row[0]?.period ?? idx}
          >
            {(row) => (
              <div style={{ display: 'flex', gap: `${gap}px`, padding: '10px 0' }}>
                {row.map((cardData) => (
                  <ActivityCard
                    key={cardData.period}
                    period={cardData.period}
                    summary={{
                      totalDistance: cardData.summary.totalDistance,
                      averageSpeed: cardData.summary.totalTime
                        ? cardData.summary.totalDistance / (cardData.summary.totalTime / 3600)
                        : 0,
                      totalTime: cardData.summary.totalTime,
                      count: cardData.summary.count,
                      maxDistance: cardData.summary.maxDistance,
                      maxSpeed: cardData.summary.maxSpeed,
                      location: cardData.summary.location,
                      totalElevationGain: SHOW_ELEVATION_GAIN
                        ? cardData.summary.totalElevationGain
                        : undefined,
                      averageHeartRate:
                        cardData.summary.heartRateCount > 0
                          ? cardData.summary.totalHeartRate / cardData.summary.heartRateCount
                          : undefined,
                    }}
                    dailyDistances={cardData.summary.dailyDistances}
                    interval={interval}
                    activities={interval === 'day' ? cardData.summary.activities : undefined}
                  />
                ))}
              </div>
            )}
          </VirtualList>
        </div>
      )}
    </div>
  );
};

export default ActivityList;
