import React from 'react';
import Stat from 'src/components/Stat';
import useActivities from 'src/hooks/useActivities';

const PeriodStat = ({ onClick }) => {
  const { workoutsCounts } = useActivities();
  const periodArr = Object.entries(workoutsCounts);
  periodArr.sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {periodArr.map(([type, times]) => (
          <Stat
            key={type}
            value={times}
            description={` ${type}`+"s"}
            citySize={1}
            onClick={() => onClick(type)}
          />
        ))}
      </section>
      <hr color="red" />
    </div>
  );
};

export default PeriodStat;
