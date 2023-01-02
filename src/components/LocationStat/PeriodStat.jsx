import React from 'react';
import Stat from 'src/components/Stat';
import useActivities from 'src/hooks/useActivities';
import { IS_CHINESE } from 'src/utils/const';
import { titleForType } from 'src/utils/utils';

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
            value={`${IS_CHINESE && titleForType(type)} ${times} `}
            description={type + (times>1 ? "s" : "") }
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
