import React from 'react';
import Stat from 'src/components/Stat';

// only support China for now
const LocationSummary = ({ yearsArr, countries, provinces, cities }) => (
  <div style={{ cursor: 'pointer' }}>
    <section>
      {yearsArr && (
        <Stat value={`${yearsArr.length}`} description=" 年里我跑过" />
      )}
      {countries && <Stat value={countries.length} description=" 个国家" />}
      {provinces && <Stat value={provinces.length} description=" 个省份" />}
      {cities && (
        <Stat value={Object.keys(cities).length} description=" 个城市" />
      )}
    </section>
    <hr color="red" />
  </div>
);

export default LocationSummary;
