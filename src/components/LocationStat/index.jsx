import React from 'react';
import YearStat from 'src/components/YearStat';
import {
  CHINESE_LOCATION_INFO_MESSAGE_FIRST,
  CHINESE_LOCATION_INFO_MESSAGE_SECOND,
} from '../../utils/const';
import CitiesStat from './CitiesStat';
import LocationSummary from './LocationSummary';
import PeriodStat from './PeriodStat';

const LocationStat = ({ changeYear, changeCity, changeTitle }) => (
  <div className="fl w-100 w-30-l pb5 pr5-l">
    <section className="pb4" style={{ paddingBottom: '0rem' }}>
      <p style={{ lineHeight: 1.8 }}>
        {CHINESE_LOCATION_INFO_MESSAGE_FIRST}
        .
        <br />
        {CHINESE_LOCATION_INFO_MESSAGE_SECOND}
        .
        <br />
        <br />
        Yesterday you said tomorrow.
      </p>
    </section>
    <hr color="red" />
    <LocationSummary />
    <CitiesStat onClick={changeCity} />
    <PeriodStat onClick={changeTitle} />
    <YearStat year="Total" onClick={changeYear} />
  </div>
);

export default LocationStat;
