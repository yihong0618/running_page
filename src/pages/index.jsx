import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import MapboxLanguage from '@mapbox/mapbox-gl-language';
import ReactMapGL, { Source, Layer, Marker } from 'react-map-gl';

import Layout from '../components/layout';
import { activities } from '../static/activities';
import GitHubSvg from '../../assets/github.svg';
import GridSvg from '../../assets/grid.svg';
import StartSvg from '../../assets/start.svg';
import EndSvg from '../../assets/end.svg';
import {
  titleForShow, formatPace, scrollToMap, locationForRun, intComma, geoJsonForRuns, geoJsonForMap,
  titleForRun, filterAndSortRuns, sortDateFunc, sortDateFuncReverse, getBoundsForGeoData,
} from '../utils/utils';
import {
  MAPBOX_TOKEN,
  IS_CHINESE,
  INFO_MESSAGE,
  MAIN_COLOR,
  PROVINCE_FILL_COLOR,
} from '../utils/const';

import styles from './running.module.scss';

const cities = {};
const runPeriod = {};
let provinces = [];
let countries = [];
let yearsArr = [];

// generate base attr
((runs) => {
  const locationsList = [];
  runs.forEach(
    (run) => {
      const location = locationForRun(run);
      const periodName = titleForRun(run);
      if (periodName) {
        runPeriod[periodName] = runPeriod[periodName] === undefined ? 1 : runPeriod[periodName] + 1;
      }
      locationsList.push(location);
      const { city, province, country } = location;
      // drop only one char city
      if (city.length > 1) {
        cities[city] = (cities[city] === undefined ? run.distance : cities[city] + run.distance);
      }
      if (province) {
        provinces.push(province);
      }
      if (country) {
        countries.push(country);
      }
      const y = run.start_date_local.slice(0, 4);
      yearsArr.push(y);
    },
  );
  yearsArr = [...new Set(yearsArr)].sort().reverse();
  provinces = [...new Set(provinces)];
  countries = [...new Set(countries)];
})(activities);
const totalActivitiesLength = activities.length;

let thisYear = '';
if (yearsArr) {
  [thisYear] = yearsArr;
}

// Hooks
const useHover = () => {
  const [hovered, setHovered] = useState();
  const [timer, setTimer] = useState();

  const eventHandlers = {
    onMouseOver() { setTimer(setTimeout(() => setHovered(true), 700)); },
    onMouseOut() { clearTimeout(timer); setHovered(false); },
  };

  return [hovered, eventHandlers];
};

// Page
export default () => {
  const [year, setYear] = useState(thisYear);
  const [runs, setActivity] = useState(filterAndSortRuns(activities, year, sortDateFunc));
  const [title, setTitle] = useState('');
  const [geoData, setGeoData] = useState(
    geoJsonForRuns(runs),
  );
  // for auto zoom
  const bounds = getBoundsForGeoData(geoData);
  const [intervalId, setIntervalId] = useState();

  const [viewport, setViewport] = useState({
    width: '100%',
    height: 400,
    ...bounds,
  });
  const changeYear = (y) => {
    setYear(y);
    scrollToMap();
    setActivity(filterAndSortRuns(activities, y, sortDateFunc));
    if (viewport.zoom > 3) {
      setViewport({
        width: '100%',
        height: 400,
        ...bounds,
      });
    }
    setTitle(`${y} Running Heatmap`);
    clearInterval(intervalId);
  };

  const locateActivity = (run) => {
    setGeoData(geoJsonForRuns([run]));
    setTitle(titleForShow(run));
    clearInterval(intervalId);
    scrollToMap();
  };

  useEffect(() => {
    setViewport({
      width: '100%',
      height: 400,
      ...bounds,
    });
  }, [geoData]);

  useEffect(() => {
    const runsNum = runs.length;
    // maybe change 20 ?
    const sliceNume = runsNum >= 20 ? runsNum / 20 : 1;
    let i = sliceNume;
    const id = setInterval(() => {
      if (i >= runsNum) {
        clearInterval(id);
      }
      const tempRuns = runs.slice(0, i);
      setGeoData(geoJsonForRuns(tempRuns));
      i += sliceNume;
    }, 100);
    setIntervalId(id);
  }, [year]);

  // TODO refactor
  useEffect(() => {
    if (year !== 'Total') {
      return;
    }
    let rectArr = document.querySelectorAll('rect');
    if (rectArr.length !== 0) {
      rectArr = Array.from(rectArr).slice(1);
    }

    rectArr.forEach((rect) => {
      const rectColor = rect.getAttribute('fill');
      // not run has no click event
      if (rectColor !== '#444444') {
        const runDate = rect.innerHTML;
        // ingnore the error
        const [runName] = runDate.match(/\d{4}-\d{1,2}-\d{1,2}/) || [];
        const runLocate = runs.filter(
          (r) => r.start_date_local.slice(0, 10) === runName,
        ).sort((a, b) => b.distance - a.distance)[0];

        // do not add the event next time
        // maybe a better way?
        if (runLocate) {
          rect.addEventListener('click', () => locateActivity(runLocate), false);
        }
      }
    });
    let polylineArr = document.querySelectorAll('polyline');
    if (polylineArr.length !== 0) {
      polylineArr = Array.from(polylineArr).slice(1);
    }
    // add picked runs svg event
    polylineArr.forEach((polyline) => {
      // not run has no click event
      const runDate = polyline.innerHTML;
      // `${+thisYear + 1}` ==> 2021
      const [runName] = runDate.match(/\d{4}-\d{1,2}-\d{1,2}/) || [`${+thisYear + 1}`];
      const run = runs.filter(
        (r) => r.start_date_local.slice(0, 10) === runName,
      ).sort((a, b) => b.distance - a.distance)[0];

      // do not add the event next time
      // maybe a better way?
      if (run) {
        polyline.addEventListener('click', () => locateActivity(run), false);
      }
    });
  }, [year]);

  return (
    <>
      <Helmet bodyAttributes={{ class: styles.body }} />
      <Layout>
        <div className="mb5">
          <div className="w-100">
            <h1 className="f1 fw9 i">Running</h1>
          </div>
          {viewport.zoom <= 3 && IS_CHINESE ? <LocationStat runs={activities} location="a" onClick={changeYear} /> : <YearsStat runs={activities} year={year} onClick={changeYear} />}
          <div className="fl w-100 w-70-l">
            <RunMap
              runs={runs}
              year={year}
              title={title}
              viewport={viewport}
              geoData={geoData}
              setViewport={setViewport}
              changeYear={changeYear}
            />
            {year === 'Total' ? <SVGStat />
              : (
                <RunTable
                  runs={runs}
                  year={year}
                  locateActivity={locateActivity}
                  setActivity={setActivity}
                />
              )}
          </div>
        </div>
      </Layout>
    </>
  );
};

const SVGStat = () => (
  <div>
    <GitHubSvg className={styles.runSVG} />
    <GridSvg className={styles.runSVG} />
  </div>
);

// Child components
const YearsStat = ({ runs, year, onClick }) => {
  // make sure the year click on front
  let yearsArrayUpdate = yearsArr.slice();
  yearsArrayUpdate = yearsArrayUpdate.filter((x) => x !== year);
  yearsArrayUpdate.unshift(year);

  // for short solution need to refactor
  return (
    <div className="fl w-100 w-30-l pb5 pr5-l">
      <section className="pb4" style={{ paddingBottom: '0rem' }}>
        <p>
          {INFO_MESSAGE(yearsArr.length, year)}
          <br />
        </p>
      </section>
      <hr color="red" />
      {yearsArrayUpdate.map((year) => (
        <YearStat key={year} runs={runs} year={year} onClick={onClick} />
      ))}
      <YearStat key="Total" runs={runs} year="Total" onClick={onClick} />
    </div>
  );
};

const LocationStat = ({ runs, onClick }) => (
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
    <LocationSummary key="locationsSummary" />
    <CitiesStat />
    <PeriodStat />
    <YearStat key="Total" runs={runs} year="Total" onClick={onClick} />
  </div>
);

const YearStat = ({ runs, year, onClick }) => {
  // for hover
  const [hovered, eventHandlers] = useHover();
  // lazy Component
  const YearSVG = React.lazy(() => import(`../../assets/year_${year}.svg`)
    .catch(() => ({ default: () => <div /> })));

  if (yearsArr.includes(year)) {
    runs = runs.filter((run) => run.start_date_local.slice(0, 4) === year);
  }
  let sumDistance = 0;
  let streak = 0;
  let pace = 0;
  let paceNullCount = 0;
  let heartRate = 0;
  let heartRateNullCount = 0;
  runs.forEach((run) => {
    sumDistance += run.distance || 0;
    if (run.average_speed) {
      pace += run.average_speed;
    } else {
      paceNullCount++;
    }
    if (run.average_heartrate) {
      heartRate += run.average_heartrate;
    } else {
      heartRateNullCount++;
    }
    if (run.streak) {
      streak = Math.max(streak, run.streak);
    }
  });
  sumDistance = (sumDistance / 1000.0).toFixed(1);
  const avgPace = formatPace(pace / (runs.length - paceNullCount));
  const hasHeartRate = !(heartRate === 0);
  const avgHeartRate = (heartRate / (runs.length - heartRateNullCount)).toFixed(
    0,
  );
  return (
    <div style={{ cursor: 'pointer' }} onClick={() => onClick(year)} {...eventHandlers}>
      <section>
        <Stat value={year} description=" Journey" />
        <Stat value={runs.length} description=" Runs" />
        <Stat value={sumDistance} description=" KM" />
        <Stat value={avgPace} description=" Avg Pace" />
        <Stat
          value={`${streak} day`}
          description=" Streak"
          className="mb0 pb0"
        />
        {hasHeartRate && (
          <Stat value={avgHeartRate} description=" Avg Heart Rate" />
        )}
      </section>
      {hovered && <React.Suspense fallback="loading..."><YearSVG className={styles.yearSVG} /></React.Suspense>}
      <hr color="red" />
    </div>
  );
};

// only support China for now
const LocationSummary = () => (
  <div style={{ cursor: 'pointer' }}>
    <section>
      <Stat value={`${yearsArr.length}`} description=" 年里我跑过" />
      <Stat value={countries.length} description=" 个国家" />
      <Stat value={provinces.length} description=" 个省份" />
      <Stat value={Object.keys(cities).length} description=" 个城市" />
    </section>
    <hr color="red" />
  </div>
);

// only support China for now
const CitiesStat = () => {
  const citiesArr = Object.entries(cities);
  citiesArr.sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {citiesArr.map(([city, distance]) => (
          <Stat key={city} value={city} description={` ${(distance / 1000).toFixed(0)} KM`} citySize={3} />
        ))}
      </section>
      <hr color="red" />
    </div>
  );
};

const PeriodStat = () => {
  const periodArr = Object.entries(runPeriod);
  periodArr.sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ cursor: 'pointer' }}>
      <section>
        {periodArr.map(([period, times]) => (
          <Stat key={period} value={period} description={` ${times} Runs`} citySize={3} />
        ))}
      </section>
      <hr color="red" />
    </div>
  );
};

const RunMap = ({
  title, viewport, setViewport, changeYear, geoData,
}) => {
  const addControlHandler = (event) => {
    const map = event && event.target;
    // set lauguage to Chinese if you use English please comment it
    if (map && IS_CHINESE) {
      map.addControl(
        new MapboxLanguage({
          defaultLanguage: 'zh',
        }),
      );
      map.setLayoutProperty('country-label-lg', 'text-field', [
        'get',
        'name_zh',
      ]);
    }
  };
  const filterProvinces = provinces.slice();
  // for geojson format
  filterProvinces.unshift('in', 'name');

  const isBigMap = (viewport.zoom <= 3);
  if (isBigMap && IS_CHINESE) {
    geoData = geoJsonForMap();
  }

  const isSingleRun = geoData.features.length === 1 && geoData.features[0].geometry.coordinates.length;
  let startLon; let
    startLat;
  let endLon; let
    endLat;
  if (isSingleRun) {
    const points = geoData.features[0].geometry.coordinates;
    [startLon, startLat] = points[0];
    [endLon, endLat] = points[points.length - 1];
  }

  return (
    <ReactMapGL
      {...viewport}
      mapStyle="mapbox://styles/mapbox/dark-v9"
      onViewportChange={setViewport}
      onLoad={addControlHandler}
      mapboxApiAccessToken={MAPBOX_TOKEN}
    >
      <RunMapButtons changeYear={changeYear} />
      <Source id="data" type="geojson" data={geoData}>
        <Layer
          id="prvince"
          type="fill"
          paint={{
            'fill-color': PROVINCE_FILL_COLOR,
          }}
          filter={filterProvinces}
        />
        <Layer
          id="runs2"
          type="line"
          paint={{
            'line-color': MAIN_COLOR,
            'line-width': isBigMap ? 1 : 2,
          }}
          layout={{
            'line-join': 'round',
            'line-cap': 'round',
          }}
        />
      </Source>
      {isSingleRun
      && <RunMarker startLat={startLat} startLon={startLon} endLat={endLat} endLon={endLon} /> }
      <span className={styles.runTitle}>{title}</span>
    </ReactMapGL>
  );
};

const RunMarker = ({
  startLon, startLat, endLon, endLat,
}) => {
  const size = 20;
  return (
    <div>
      <Marker key="maker_start" longitude={startLon} latitude={startLat}>
        <div style={{ transform: `translate(${-size / 2}px,${-size}px)` }}>
          <StartSvg className={styles.locationSVG} />
        </div>
      </Marker>
      <Marker key="maker_end" longitude={endLon} latitude={endLat}>
        <div style={{ transform: `translate(${-size / 2}px,${-size}px)` }}>
          <EndSvg className={styles.locationSVG} />
        </div>
      </Marker>
    </div>
  );
};

const RunMapButtons = ({ changeYear }) => {
  const yearsButtons = yearsArr.slice();
  yearsButtons.push('Total');
  const [index, setIndex] = useState(0);
  const handleClick = (e, year) => {
    const elementIndex = yearsButtons.indexOf(year);
    e.target.style.color = MAIN_COLOR;

    const elements = document.getElementsByClassName(styles.button);
    if (index !== elementIndex) {
      elements[index].style.color = 'white';
    }
    setIndex(elementIndex);
  };
  return (
    <div>
      <ul className={styles.buttons}>
        {yearsButtons.map((year) => (
          <li
            key={`${year}button`}
            style={{ color: year === thisYear ? MAIN_COLOR : 'white' }}
            year={year}
            onClick={(e) => {
              changeYear(year);
              handleClick(e, year);
            }}
            className={styles.button}
          >
            {year}
          </li>
        ))}
      </ul>
    </div>
  );
};

const RunTable = ({
  runs, year, locateActivity, setActivity,
}) => {
  const [runIndex, setRunIndex] = useState(-1);
  const [sortFuncInfo, setSortFuncInfo] = useState('');
  // TODO refactor?
  const sortKMFunc = (a, b) => (sortFuncInfo === 'KM' ? a.distance - b.distance : b.distance - a.distance);
  const sortPaceFunc = (a, b) => (sortFuncInfo === 'Pace' ? a.average_speed - b.average_speed : b.average_speed - a.average_speed);
  const sortBPMFunc = (a, b) => (sortFuncInfo === 'BPM' ? a.average_heartrate - b.average_heartrate : b.average_heartrate - a.average_heartrate);
  const sortDateFuncClick = sortFuncInfo === 'Date' ? sortDateFunc : sortDateFuncReverse;
  const sortFuncMap = new Map([
    ['KM', sortKMFunc],
    ['Pace', sortPaceFunc],
    ['BPM', sortBPMFunc],
    ['Date', sortDateFuncClick],
  ]);
  const handleClick = (e) => {
    const funcName = e.target.innerHTML;
    if (sortFuncInfo === funcName) {
      setSortFuncInfo('');
    } else {
      setSortFuncInfo(funcName);
    }
    const f = sortFuncMap.get(e.target.innerHTML);
    if (runIndex !== -1) {
      const el = document.getElementsByClassName(styles.runRow);
      el[runIndex].style.color = MAIN_COLOR;
    }
    setActivity(filterAndSortRuns(runs, year, f));
  };

  return (
    <div className={styles.tableContainer}>
      <table className={styles.runTable} cellSpacing="0" cellPadding="0">
        <thead>
          <tr>
            <th />
            {Array.from(sortFuncMap.keys()).map((k) => (
              <th onClick={(e) => handleClick(e)}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow
              runs={runs}
              run={run}
              key={run.run_id}
              locateActivity={locateActivity}
              runIndex={runIndex}
              setRunIndex={setRunIndex}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RunRow = ({
  runs, run, locateActivity, runIndex, setRunIndex,
}) => {
  const distance = (run.distance / 1000.0).toFixed(1);
  const pace = run.average_speed;

  const paceParts = pace ? formatPace(pace) : null;

  const heartRate = run.average_heartrate;

  // change click color
  const handleClick = (e, runs, run) => {
    const elementIndex = runs.indexOf(run);
    e.target.parentElement.style.color = 'red';

    const elements = document.getElementsByClassName(styles.runRow);
    if (runIndex !== -1 && elementIndex !== runIndex) {
      elements[runIndex].style.color = MAIN_COLOR;
    }
    setRunIndex(elementIndex);
  };

  return (
    <tr
      className={styles.runRow}
      key={run.start_date_local}
      onClick={(e) => {
        handleClick(e, runs, run);
        locateActivity(run);
      }}
    >
      <td>{titleForRun(run)}</td>
      <td>{distance}</td>
      {pace && <td>{paceParts}</td>}
      <td>{heartRate && heartRate.toFixed(0)}</td>
      <td className={styles.runDate}>{run.start_date_local}</td>
    </tr>
  );
};

const Stat = ({
  value, description, className, citySize,
}) => (
  <div className={`${className} pb2 w-100`}>
    <span className={`f${citySize || 1} fw9 i`}>{intComma(value)}</span>
    <span className="f3 fw6 i">{description}</span>
  </div>
);
