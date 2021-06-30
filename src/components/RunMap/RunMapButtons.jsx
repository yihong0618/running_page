import React, { useEffect, useState } from 'react';
import useActivities from 'src/hooks/useActivities';
import { MAIN_COLOR } from 'src/utils/const';
import styles from './style.module.scss';

const RunMapButtons = ({ changeYear, thisYear, mapButtonYear }) => {
  const elements = document.getElementsByClassName(styles.button);
  const { years } = useActivities();
  const yearsButtons = years.slice();
  yearsButtons.push('Total');
  const [index, setIndex] = useState(0);
  const handleClick = (e, year) => {
    const elementIndex = yearsButtons.indexOf(year);
    e.target.style.color = MAIN_COLOR;

    if (index !== elementIndex) {
      elements[index].style.color = 'white';
    }
    setIndex(elementIndex);
  };
  return (
    <div>
      <ul className={styles.buttons}>
        {yearsButtons.map((year) => (
          <li
            key={`${year}button`}
            style={{ color: year === thisYear ? MAIN_COLOR : 'white' }}
            year={year}
            onClick={(e) => {
              changeYear(year);
              handleClick(e, year);
            }}
            className={styles.button}
          >
            {year}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RunMapButtons;
