import React from 'react';
import LocationSummary from './LocationSummary';
import YearStat from 'src/components/YearStat';
import CitiesStat from './CitiesStat';
import PeriodStat from './PeriodStat';

const LocationStat = ({
  changeYear,
  changeCity,
  changeTitle,
  yearsArr,
  countries,
  provinces,
  cities,
  runPeriod,
}) => (
  <div className="fl w-100 w-30-l pb5 pr5-l">
    <section className="pb4" style={{ paddingBottom: '0rem' }}>
      <p>
        我跑过了一些地方，希望随着时间的推移，地图点亮的地方越来越多.
        <br />
        不要停下来，不要停下奔跑的脚步.
        <br />
        <br />
        Yesterday you said tomorrow.
      </p>
    </section>
    <hr color="red" />
    <LocationSummary
      key="locationsSummary"
      yearsArr={yearsArr}
      countries={countries}
      provinces={provinces}
      cities={cities}
    />
    <CitiesStat onClick={changeCity} cities={cities} />
    <PeriodStat onClick={changeTitle} runPeriod={runPeriod} />
    <YearStat
      key="Total"
      year="Total"
      onClick={changeYear}
      yearsArr={yearsArr}
    />
  </div>
);

export default LocationStat;
