import React from 'react';
import Stat from 'src/components/Stat';

const PeriodStat = ({ onClick, runPeriod }) => {
  const periodArr = Object.entries(runPeriod);
  periodArr.sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {periodArr.map(([period, times]) => (
          <Stat
            key={period}
            value={period}
            description={` ${times} Runs`}
            citySize={3}
            onClick={() => onClick(period)}
          />
        ))}
      </section>
      <hr color="red" />
    </div>
  );
};

export default PeriodStat;
