import React from 'react';
import Stat from '@/components/Stat';
import useActivities from '@/hooks/useActivities';
import { IS_CHINESE } from '@/utils/const';
import { titleForType } from '@/utils/utils';

const PeriodStat = ({ onClick }: { onClick: (_period: string) => void }) => {
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
