import React from 'react';
import Stat from 'src/components/Stat';
import useActivities from 'src/hooks/useActivities';

// only support China for now
const LocationSummary = () => {
  const { years, countries, provinces, cities } = useActivities();
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {years && <Stat value={`${years.length}`} description=" Years" />}
        {countries && <Stat value={countries.length} description=" Countries" />}
        {provinces && <Stat value={provinces.length} description=" Provinces" />}
        {cities && (
          <Stat value={Object.keys(cities).length} description=" Cities" />
        )}
      </section>
      <hr color="red" />
    </div>
  );
};

export default LocationSummary;
