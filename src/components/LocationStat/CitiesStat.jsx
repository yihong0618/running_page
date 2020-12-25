import React from 'react';
import Stat from 'src/components/Stat';
import useActivities from 'src/hooks/useActivities';

// only support China for now
const CitiesStat = ({ onClick }) => {
  const { cities } = useActivities();

  const citiesArr = Object.entries(cities);
  citiesArr.sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {citiesArr.map(([city, distance]) => (
          <Stat
            key={city}
            value={city}
            description={` ${(distance / 1000).toFixed(0)} KM`}
            citySize={3}
            onClick={() => onClick(city)}
          />
        ))}
      </section>
      <hr color="red" />
    </div>
  );
};

export default CitiesStat;
