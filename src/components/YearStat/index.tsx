import React from 'react';
import Stat from '@/components/Stat';
import WorkoutStat from '@/components/WorkoutStat';
import useActivities from '@/hooks/useActivities';
import { formatPace, colorFromType } from '@/utils/utils';
import styles from './style.module.scss';
import useHover from '@/hooks/useHover';
import { yearStats } from '@assets/index'

const YearStat = ({ year, onClick }: { year: string, onClick: (_year: string) => void }) => {
  let { activities: runs, years } = useActivities();
  // for hover
  const [hovered, eventHandlers] = useHover();
  // lazy Component
  const YearSVG = React.lazy(() => yearStats[`./year_${year}.svg`]()
    .then((res) => ({ default: res }))
    .catch((err) => {
      console.error(err);
      return { default: () => <div>Failed to load SVG</div> };
    })
  );

  if (years.includes(year)) {
    runs = runs.filter((run) => run.start_date_local.slice(0, 4) === year);
  }
  let sumDistance = 0;
  let streak = 0;
  let heartRate = 0;
  let heartRateNullCount = 0;
  const workoutsCounts = {};

  runs.forEach((run) => {
    sumDistance += run.distance || 0;
    if (run.average_speed) {
      if(workoutsCounts[run.type]){
        var [oriCount, oriSecondsAvail, oriMetersAvail] = workoutsCounts[run.type]
        workoutsCounts[run.type] = [oriCount + 1, oriSecondsAvail + (run.distance || 0) / run.average_speed, oriMetersAvail + (run.distance || 0)]
      }else{
        workoutsCounts[run.type] = [1, (run.distance || 0) / run.average_speed, run.distance]
      }
    }
    if (run.average_heartrate) {
      heartRate += run.average_heartrate;
    } else {
      heartRateNullCount++;
    }
    if (run.streak) {
      streak = Math.max(streak, run.streak);
    }
  });
  const hasHeartRate = !(heartRate === 0);
  const avgHeartRate = (heartRate / (runs.length - heartRateNullCount)).toFixed(
    0
  );

  const workoutsArr = Object.entries(workoutsCounts);
  workoutsArr.sort((a, b) => {
    return b[1][0] - a[1][0]
  });
  return (
    <div
      style={{ cursor: 'pointer' }}
      onClick={() => onClick(year)}
      {...eventHandlers}
    >
      <section>
        <Stat value={year} description=" Journey" />
        { sumDistance > 0 &&
          <WorkoutStat
            key='total'
            value={runs.length}
            description={" Total"}
            distance={(sumDistance / 1000.0).toFixed(0)}
          />
        }
        { workoutsArr.map(([type, count]) => (
          <WorkoutStat
            key={type}
            value={count[0]}
            description={` ${type}`+"s"}
            // pace={formatPace(count[2] / count[1])}
            distance={(count[2] / 1000.0).toFixed(0)}
            // color={colorFromType(type)}
          />
        ))}
        <Stat
          value={`${streak} day`}
          description=" Streak"
          className="mb0 pb0"
        />
        {hasHeartRate && (
          <Stat value={avgHeartRate} description=" Avg Heart Rate" />
        )}
      </section>
      {year !== "Total" && hovered && (
        <React.Suspense fallback="loading...">
          <YearSVG className={styles.yearSVG} />
        </React.Suspense>
      )}
      <hr color="red" />
    </div>
  );
};

export default YearStat;
