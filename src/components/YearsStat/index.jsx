import React from 'react';
import YearStat from 'src/components/YearStat';
import useActivities from 'src/hooks/useActivities';
import { INFO_MESSAGE } from 'src/utils/const';

const YearsStat = ({ year, onClick }) => {
  const { years } = useActivities();
  // make sure the year click on front
  let yearsArrayUpdate = years.slice();
  yearsArrayUpdate.push('Total');
  yearsArrayUpdate = yearsArrayUpdate.filter((x) => x !== year);
  yearsArrayUpdate.unshift(year);

  // for short solution need to refactor
  return (
    <div className="fl w-100 w-30-l pb5 pr5-l">
      <section className="pb4" style={{ paddingBottom: '0rem' }}>
        <p style={{ lineHeight: 1.8 }}>
          {INFO_MESSAGE(years.length, year)}
          <br />
          <br />
          "明明这么痛苦，这么难过，为什么就是不能放弃跑步？因为全身细胞都在蠢蠢欲动，想要感受强风迎面吹拂的滋味。"
          <br />
          <p style={quoteStyle}>&ndash;&ndash;《强风吹拂》</p>
        </p>
      </section>
      <hr color="red" />
      {yearsArrayUpdate.map((year) => (
        <YearStat key={year} year={year} onClick={onClick} />
      ))}
      {yearsArrayUpdate.hasOwnProperty('Total') ? (
        <YearStat key="Total" year="Total" onClick={onClick} />
      ) : (
        <div />
      )}
    </div>
  );
};

const quoteStyle = {
  fontWeight:"bold",
  textAlign: "right"
};

export default YearsStat;
