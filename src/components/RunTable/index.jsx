import React, { useState } from 'react';
import { MAIN_COLOR } from 'src/utils/const';
import { sortDateFunc, sortDateFuncReverse } from 'src/utils/utils';
import RunRow from './RunRow';
import styles from './style.module.scss';

const RunTable = ({
  runs,
  locateActivity,
  setActivity,
  runIndex,
  setRunIndex,
}) => {
  const [sortFuncInfo, setSortFuncInfo] = useState('');
  // TODO refactor?
  const sortKMFunc = (a, b) =>
    sortFuncInfo === 'KM' ? a.distance - b.distance : b.distance - a.distance;
  const sortPaceFunc = (a, b) =>
    sortFuncInfo === 'Pace'
      ? a.average_speed - b.average_speed
      : b.average_speed - a.average_speed;
  const sortBPMFunc = (a, b) =>
    sortFuncInfo === 'BPM'
      ? a.average_heartrate - b.average_heartrate
      : b.average_heartrate - a.average_heartrate;
  const sortRunTimeFunc = (a, b) => {
    if (Number.isNaN(a.distance) || Number.isNaN(b.distance)
      || Number.isNaN(a.average_speed) || Number.isNaN(b.average_speed)) {
      return 0;
    }
    const aDistance = (a.distance / 1000.0).toFixed(1);
    const bDistance = (b.distance / 1000.0).toFixed(1);
    const aPace = (1000.0 / 60.0) * (1.0 / a.average_speed);
    const bPace = (1000.0 / 60.0) * (1.0 / b.average_speed);
    if (sortFuncInfo === 'Time') {
      return aDistance * aPace - bDistance * bPace;
    } else {
      return bDistance * bPace - aDistance * aPace;
    }
  };
  const sortDateFuncClick =
    sortFuncInfo === 'Date' ? sortDateFunc : sortDateFuncReverse;
  const sortFuncMap = new Map([
    ['KM', sortKMFunc],
    ['Pace', sortPaceFunc],
    ['BPM', sortBPMFunc],
    ['Time', sortRunTimeFunc],
    ['Date', sortDateFuncClick],
  ]);
  const handleClick = (e) => {
    const funcName = e.target.innerHTML;
    if (sortFuncInfo === funcName) {
      setSortFuncInfo('');
    } else {
      setSortFuncInfo(funcName);
    }
    const f = sortFuncMap.get(e.target.innerHTML);
    if (runIndex !== -1) {
      const el = document.getElementsByClassName(styles.runRow);
      el[runIndex].style.color = MAIN_COLOR;
    }
    setActivity(runs.sort(f));
  };

  return (
    <div className={styles.tableContainer}>
      <table className={styles.runTable} cellSpacing="0" cellPadding="0">
        <thead>
          <tr>
            <th />
            {Array.from(sortFuncMap.keys()).map((k) => (
              <th key={k} onClick={(e) => handleClick(e)}>
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow
              runs={runs}
              run={run}
              key={run.run_id}
              locateActivity={locateActivity}
              runIndex={runIndex}
              setRunIndex={setRunIndex}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RunTable;
