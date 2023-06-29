import React, { useEffect, useState } from 'react';
import useActivities from 'src/hooks/useActivities';
import styles from './style.module.scss';

const RunMapButtons = ({ changeYear, thisYear }) => {
  const { years } = useActivities();
  const yearsButtons = years.slice();
  yearsButtons.push('Total');

  return (
    <div>
      <ul className={styles.buttons}>
        {yearsButtons.map((year) => (
          <li
            key={`${year}button`}
            className={styles.button + ` ${year === thisYear ? styles.selected : ''}`}
            onClick={() => {
              changeYear(year);
            }}
          >
            {year}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RunMapButtons;
