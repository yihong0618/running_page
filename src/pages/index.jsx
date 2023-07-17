import { Analytics } from '@vercel/analytics/react';
import React, { useEffect, useState } from 'react';
import Layout from 'src/components/Layout';
import LocationStat from 'src/components/LocationStat';
import RunMap from 'src/components/RunMap';
import RunTable from 'src/components/RunTable';
import SVGStat from 'src/components/SVGStat';
import YearsStat from 'src/components/YearsStat';
import useActivities from 'src/hooks/useActivities';
import useSiteMetadata from 'src/hooks/useSiteMetadata';
import { IS_CHINESE } from 'src/utils/const';
import {
  filterAndSortRuns,
  filterCityRuns,
  filterTitleRuns,
  filterYearRuns,
  geoJsonForRuns,
  getBoundsForGeoData,
  scrollToMap,
  sortDateFunc,
  titleForShow,
} from 'src/utils/utils';

const Index = () => {
  const { siteTitle } = useSiteMetadata();
  const { activities, thisYear } = useActivities();
  const [year, setYear] = useState(thisYear);
  const [runIndex, setRunIndex] = useState(-1);
  const [runs, setActivity] = useState(
    filterAndSortRuns(activities, year, filterYearRuns, sortDateFunc)
  );
  const [title, setTitle] = useState('');
  const [geoData, setGeoData] = useState(geoJsonForRuns(runs));
  // for auto zoom
  const bounds = getBoundsForGeoData(geoData);
  const [intervalId, setIntervalId] = useState();

  const [viewport, setViewport] = useState({
    ...bounds,
  });

  const changeByItem = (item, name, func, isChanged) => {
    scrollToMap();
    setActivity(filterAndSortRuns(activities, item, func, sortDateFunc));
    setRunIndex(-1);
    setTitle(`${item} ${name} Running Heatmap`);
  };

  const changeYear = (y) => {
    const isChanged = y === year;
    // default year
    setYear(y);

    if (viewport.zoom > 3) {
      setViewport({
        ...bounds,
      });
    }

    changeByItem(y, 'Year', filterYearRuns, isChanged);
    clearInterval(intervalId);
  };

  const changeCity = (city) => {
    changeByItem(city, 'City', filterCityRuns, false);
  };

  const changeTitle = (title) => {
    changeByItem(title, 'Title', filterTitleRuns, false);
  };

  const locateActivity = (runDate) => {
    const activitiesOnDate = runs.filter((r) => r.start_date_local.slice(0, 10) === runDate);

    if (!activitiesOnDate.length) {
      return;
    }

    const sortedActivities = activitiesOnDate.sort((a, b) => b.distance - a.distance);
    const info = sortedActivities[0];

    if (!info) {
      return;
    }

    setGeoData(geoJsonForRuns([info]));
    setTitle(titleForShow(info));
    clearInterval(intervalId);
    scrollToMap();
  };

  useEffect(() => {
    setViewport({
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
  }, [runs]);

  useEffect(() => {
    if (year !== 'Total') {
      return;
    }

    let svgStat = document.getElementById('svgStat')
    if (!svgStat) {
      return
    }
    svgStat.addEventListener('click', (e) => {
      const target = e.target;
      if (target) {
        const tagName = target.tagName.toLowerCase()

        if ((tagName === 'rect' &&
          parseFloat(target.getAttribute('width')) === 2.6 &&
          parseFloat(target.getAttribute('height')) === 2.6 &&
          target.getAttribute('fill') !== '#444444'
        ) || (
            tagName === 'polyline'
          )) {
          const [runDate] = target.innerHTML.match(/\d{4}-\d{1,2}-\d{1,2}/) || [`${+thisYear + 1}`];
          locateActivity(runDate)
        }
      }
    })
  }, [year]);

  return (
    <Layout>
      <div className="fl w-30-l">
        <h1 className="f1 fw9 i">
          <a href="/">{siteTitle}</a>
        </h1>
        {viewport.zoom <= 3 && IS_CHINESE ? (
          <LocationStat
            changeYear={changeYear}
            changeCity={changeCity}
            changeTitle={changeTitle}
          />
        ) : (
          <YearsStat year={year} onClick={changeYear} />
        )}
      </div>
      <div className="fl w-100 w-70-l">
        <RunMap
          title={title}
          viewport={viewport}
          geoData={geoData}
          setViewport={setViewport}
          changeYear={changeYear}
          thisYear={year}
        />
        {year === 'Total' ? (
          <SVGStat />
        ) : (
          <RunTable
            runs={runs}
            locateActivity={locateActivity}
            setActivity={setActivity}
            runIndex={runIndex}
            setRunIndex={setRunIndex}
          />
        )}
      </div>
      {/* Enable Audiences in Vercel Analytics: https://vercel.com/docs/concepts/analytics/audiences/quickstart */}
      <Analytics />
    </Layout>
  );
};

export default Index;
