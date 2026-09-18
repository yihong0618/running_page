import {
  formatPace,
  titleForRun,
  formatRunTime,
  getActivitySport,
  Activity,
  RunIds,
} from '../../utils/utils';
import { SHOW_ELEVATION_GAIN } from '../../utils/const';
import { M_TO_DIST, M_TO_ELEV } from '../../utils/utils';
import styles from './style.module.css';

interface IRunRowProperties {
  elementIndex: number;
  locateActivity: (_runIds: RunIds) => void;
  run: Activity;
  runIndex: number;
  setRunIndex: (_ndex: number) => void;
}

const getSportEmoji = (run: Activity): string => {
  const sport = getActivitySport(run);
  const type = run.type;
  if (type === 'Run' || type === 'VirtualRun' || type === 'TrailRun')
    return '🏃';
  if (type === 'cycling' || type === 'Ride' || type === 'VirtualRide')
    return '🚴';
  if (type === 'hiking') return '🥾';
  if (type === 'walking' || type === 'Walk') return '🚶';
  if (type === 'Swim') return '🏊';
  if (sport.includes('滑雪') || type.includes('ski')) return '⛷️';
  return '🏃';
};

const RunRow = ({
  elementIndex,
  locateActivity,
  run,
  runIndex,
  setRunIndex,
}: IRunRowProperties) => {
  const distance = (run.distance / M_TO_DIST).toFixed(2);
  const paceParts = run.average_speed ? formatPace(run.average_speed) : null;
  const heartRate = run.average_heartrate;
  const runTime = formatRunTime(run.moving_time);
  const handleClick = () => {
    if (runIndex === elementIndex) {
      setRunIndex(-1);
      locateActivity([]);
      return;
    }
    setRunIndex(elementIndex);
    locateActivity([run.run_id]);
  };

  return (
    <tr
      className={`${styles.runRow} ${runIndex === elementIndex ? styles.selected : ''}`}
      key={run.start_date_local}
      onClick={handleClick}
    >
      <td>
        <span className={styles.sportIndicator}>{getSportEmoji(run)}</span>
        {titleForRun(run)}
      </td>
      <td>{distance}</td>
      {SHOW_ELEVATION_GAIN && (
        <td>{((run.elevation_gain ?? 0) * M_TO_ELEV).toFixed(1)}</td>
      )}
      {paceParts && <td>{paceParts}</td>}
      <td>{heartRate && heartRate.toFixed(0)}</td>
      <td>{runTime}</td>
      <td className={styles.runDate}>{run.start_date_local}</td>
    </tr>
  );
};

export default RunRow;
