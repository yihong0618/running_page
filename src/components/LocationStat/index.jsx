import React from 'react';
import YearStat from 'src/components/YearStat';
import {
  CHINESE_LOCATION_INFO_MESSAGE_FIRST,
  CHINESE_LOCATION_INFO_MESSAGE_SECOND,
} from 'src/utils/const';
import CitiesStat from './CitiesStat';
import LocationSummary from './LocationSummary';
import PeriodStat from './PeriodStat';

const LocationStat = ({ changeYear, changeCity, changeTitle }) => (
<<<<<<< HEAD
  <div className="fl w-100 pb5 pr5-l">
=======
  <div className="fl w-100 w-100-l pb5 pr5-l">
>>>>>>> 49172726a76b05f751b090d8ceb001447282bd63
    <section className="pb4" style={{ paddingBottom: '0rem' }}>
      <p style={{ lineHeight: 1.8 }}>
        {CHINESE_LOCATION_INFO_MESSAGE_FIRST}
        .
        <br />
        {CHINESE_LOCATION_INFO_MESSAGE_SECOND}
        .
        <br />
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
