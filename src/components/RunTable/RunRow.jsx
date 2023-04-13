import React from 'react';
import { MAIN_COLOR } from 'src/utils/const';
import { formatPace, titleForRun, colorFromType, formatRunTime } from 'src/utils/utils';
import styles from './style.module.scss';

const RunRow = ({ runs, run, locateActivity, runIndex, setRunIndex }) => {
  const distance = (run.distance / 1000.0).toFixed(1);
  const pace = run.average_speed;

  const paceParts = pace ? formatPace(pace) : null;

  const heartRate = run.average_heartrate;

  const type = run.type;

  const runTime = formatRunTime(run.moving_time);

  // change click color
  const handleClick = (e, runs, run) => {
    const elementIndex = runs.indexOf(run);
    e.target.parentElement.style.color = 'red';

    const elements = document.getElementsByClassName(styles.runRow);
    if (runIndex !== -1 && elementIndex !== runIndex) {
      elements[runIndex].style.color = colorFromType(runs[runIndex].type);
    }
    setRunIndex(elementIndex);
    locateActivity(run);
  };

  return (
    <tr
      className={styles.runRow}
      key={run.start_date_local}
      onClick={(e) => handleClick(e, runs, run) }
      style={{color: colorFromType(type)}}
    >
      <td>{run.name}</td>
      <td>{type}</td>
      <td>{distance}</td>
      {pace && <td>{paceParts}</td>}
      <td>{heartRate && heartRate.toFixed(0)}</td>
      <td>{runTime}</td>
      <td className={styles.runDate}>{run.start_date_local}</td>
    </tr>
  );
};

export default RunRow;
