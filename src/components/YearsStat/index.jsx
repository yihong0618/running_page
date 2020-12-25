import React from 'react';
import { INFO_MESSAGE } from 'src/utils/const';
import YearStat from 'src/components/YearStat';

const YearsStat = ({ year, onClick, yearsArr }) => {
  // make sure the year click on front
  let yearsArrayUpdate = yearsArr.slice();
  yearsArrayUpdate = yearsArrayUpdate.filter((x) => x !== year);
  yearsArrayUpdate.unshift(year);

  // for short solution need to refactor
  return (
    <div className="fl w-100 w-30-l pb5 pr5-l">
      <section className="pb4" style={{ paddingBottom: '0rem' }}>
        <p>
          {INFO_MESSAGE(yearsArr.length, year)}
          <br />
        </p>
      </section>
      <hr color="red" />
      {yearsArrayUpdate.map((year) => (
        <YearStat
          yearsArr={yearsArr}
          key={year}
          year={year}
          onClick={onClick}
        />
      ))}
      <YearStat
        yearsArr={yearsArr}
        key="Total"
        year="Total"
        onClick={onClick}
      />
    </div>
  );
};

export default YearsStat;
