import React, { useState, useEffect } from 'react';
import { MAIN_COLOR } from 'src/utils/const';
import useActivities from 'src/hooks/useActivities';
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
  useEffect(() => {
    if (elements[index]) {
      elements[index].style.color = 'white';
    }
    if (elements[yearsButtons.indexOf(mapButtonYear)]) {
      elements[yearsButtons.indexOf(mapButtonYear)].style.color = MAIN_COLOR
    }
    setIndex(yearsButtons.indexOf(mapButtonYear));
  })
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
