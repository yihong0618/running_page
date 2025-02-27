import { useEffect, useState } from 'react';
import React, { useReducer  } from 'react';
import { Analytics } from '@vercel/analytics/react';
import Layout from '@/components/Layout';
import LocationStat from '@/components/LocationStat';
import RunMap from '@/components/RunMap';
import RunTable from '@/components/RunTable';
import SVGStat from '@/components/SVGStat';
import YearsStat from '@/components/YearsStat';
import useActivities from '@/hooks/useActivities';
import useSiteMetadata from '@/hooks/useSiteMetadata';
import { IS_CHINESE } from '@/utils/const';
import {
  Activity,
  IViewState,
  filterAndSortRuns,
  filterCityRuns,
  filterTitleRuns,
  filterTypeRuns,
  filterYearRuns,
  geoJsonForRuns,
  getBoundsForGeoData,
  scrollToMap,
  sortDateFunc,
  titleForShow,
  RunIds,
  RunId,
} from '@/utils/utils';

const SHOW_LOCATION_STAT = 'SHOW_LOCATION_STAT';
  const SHOW_YEARS_STAT = 'SHOW_YEARS_STAT';
  const reducer = (state: any, action: { type: any; }) => {
    switch (action.type) {
        case SHOW_LOCATION_STAT:
            return { showLocationStat: true };
        case SHOW_YEARS_STAT:
            return { showLocationStat: false };
        default:
            return state;
    }
};
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
  const bounds = getBoundsForGeoData(geoData);  // 计算当前 geoData 的边界
  const [intervalId, setIntervalId] = useState<number>();

  const [viewState, setViewState] = useState<IViewState>({
    ...bounds,
  });

  const changeByItem = (
    item: string,
    name: string,
    func: (_run: Activity, _value: string) => boolean
  ) => {
    scrollToMap();
    if (name != 'Year') {
      setYear(thisYear);
    }
    setActivity(filterAndSortRuns(activities, item, func, sortDateFunc));
    setRunIndex(-1);
    setTitle(`${item} ${name} Heatmap`);
  };

  const changeYear = (y: string) => {
    // default year
    setYear(y);

    if ((viewState.zoom ?? 0) > 5 && bounds) {
      setViewState({
        ...bounds,
      });
    }

    changeByItem(y, 'Year', filterYearRuns);
    clearInterval(intervalId);
  };

  const changeCity = (city: string) => {
    changeByItem(city, 'City', filterCityRuns);
  };

  const changeTitle = (title: string) => {
    changeByItem(title, 'Title', filterTitleRuns);
  };

  const changeType = (type: string) => {
    changeByItem(type, 'Type', filterTypeRuns);
  };

  const changeTypeInYear = (year:string, type: string) => {
    scrollToMap();
    // type in year, filter year first, then type
    if(year != 'Total'){
      setYear(year);
      setActivity(filterAndSortRuns(activities, year, filterYearRuns, sortDateFunc, type, filterTypeRuns));
    }
    else {
      setYear(thisYear);
      setActivity(filterAndSortRuns(activities, type, filterTypeRuns, sortDateFunc));
    }
    setRunIndex(-1);
    setTitle(`${year} ${type} Type Heatmap`);
  };
  
  // 新增状态保存选中ID
  const [selectedRunIds, setSelectedRunIds] = useState<RunIds>([]);

  // 修改后的 locateActivity
  const locateActivity = (runIds: RunIds) => {
     // 类型安全校验
    if (!Array.isArray(runIds)) return;
    const ids = new Set(runIds);
    const selectedRuns = !runIds.length
      ? runs
      : runs.filter((r: any) => ids.has(r.run_id));
    // console.log(selectedRuns)
    // setSelectedRunIds(runIds); // 👈 仅记录选中ID，不修改原始数据
    if (!selectedRuns.length) {
      return;
    } 
    const lastRun = selectedRuns.sort(sortDateFunc)[0];
    if (!lastRun) {
      return;
    }
    setTitle(titleForShow(lastRun));
    clearInterval(intervalId);
    scrollToMap();
    // setGeoData(geoJsonForRuns(selectedRuns)); // 👈 直接覆盖原有数据
    // 计算选中轨迹的边界
    const selectedGeoData = geoJsonForRuns(selectedRuns);
    console.log('选中记录：',selectedGeoData)
    if (selectedGeoData.features[0].geometry.coordinates.length > 0) {
      // 处理无数据的情况，可能提示用户或跳过缩放
      setSelectedRunIds(runIds);
      const selectedBounds = getBoundsForGeoData(selectedGeoData);
      setViewState(prev => ({
        ...prev,
        ...selectedBounds,
        // transitionDuration: 1000
      }));
      
    }
  }

  // useEffect(() => {
  //   setViewState({
  //     ...bounds,
  //   });
  // }, [geoData]); // 👈 自动设置经纬度中心点和缩放级别

  // useEffect(() => {
  //   const runsNum = runs.length;
  //   // maybe change 20 ?
  //   const sliceNum = runsNum >= 10 ? runsNum / 10 : 1;
  //   let i = sliceNum;
  //   const id = setInterval(() => {
  //     if (i >= runsNum) {
  //       clearInterval(id);
  //     }

  //     const tempRuns = runs.slice(0, i);
  //     setGeoData(geoJsonForRuns(tempRuns));
  //     i += sliceNum;
  //   }, 10);
  //   setIntervalId(id);
  // }, [runs]);
  useEffect(() => {
    // 生成包含所有轨迹且带 isSelected 标记的 geoData
    setGeoData(geoJsonForRuns(runs, selectedRunIds));
  }, [runs, selectedRunIds]); // 当 runs 或选中ID变化时触发
  // console.log('geoData:', geoData);
  useEffect(() => {
    if (year !== 'Total') {
      return;
    }

    let svgStat = document.getElementById('svgStat');
    if (!svgStat) {
      return;
    }

    const handleClick = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === 'path') {
        // Use querySelector to get the <desc> element and the <title> element.
        const descEl = target.querySelector('desc');
        if (descEl) {
          // If the runId exists in the <desc> element, it means that a running route has been clicked.
          const runId = Number(descEl.innerHTML);
          if (!runId) {
            return;
          }
          locateActivity([runId]);
          return;
        }

        const titleEl = target.querySelector('title');
        if (titleEl) {
          // If the runDate exists in the <title> element, it means that a date square has been clicked.
          const [runDate] = titleEl.innerHTML.match(
            /\d{4}-\d{1,2}-\d{1,2}/
          ) || [`${+thisYear + 1}`];
          const runIDsOnDate = runs
            .filter((r) => r.start_date_local.slice(0, 10) === runDate)
            .map((r) => r.run_id);
          if (!runIDsOnDate.length) {
            return;
          }
          locateActivity(runIDsOnDate);
        }
      }
    };
    svgStat.addEventListener('click', handleClick);
    return () => {
      svgStat && svgStat.removeEventListener('click', handleClick);
    };
  }, [year]);

  // 初始化 state 和 dispatch 函数
  const [state, dispatch] = useReducer(reducer, { showLocationStat: true });
  // 切换显示组件的函数
  const handleToggle = () => {
    if (state.showLocationStat) {
        dispatch({ type: SHOW_YEARS_STAT });
    } else {
        dispatch({ type: SHOW_LOCATION_STAT });
    }
};

const buttonStyle = {
  backgroundColor: '#007BFF', // 背景色
  color: 'white', // 文字颜色
  border: 'none', // 去除边框
  borderRadius: '4px', // 圆角
  padding: '10px 20px', // 内边距
  fontSize: '16px', // 字体大小
  cursor: 'pointer', // 鼠标指针样式
  marginBottom: '20px' // 底部外边距
};
  return (
    <Layout>
      <div className="w-full lg:w-1/4">
        <h1 className="my-12 text-3xl font-extrabold italic">
          <a href="/">{siteTitle}</a>
        </h1>
        {/* {(viewState.zoom ?? 0) <= 5 && IS_CHINESE ? (
          <LocationStat
            changeYear={changeYear}
            changeCity={changeCity}
            changeType={changeType}
            onClickTypeInYear={changeTypeInYear}
          />
        ) : (
          <YearsStat year={year} onClick={changeYear} onClickTypeInYear={changeTypeInYear}/>
        )} */}
        <button onClick={handleToggle} style={buttonStyle}>
                {state.showLocationStat ? '切换至年份统计' : '切换至地点统计'}
            </button>
            {state.showLocationStat ? (
                <LocationStat
                    changeYear={changeYear}
                    changeCity={changeCity}
                    changeType={changeType}
                    onClickTypeInYear={changeTypeInYear}
                />
            ) : (
                <YearsStat year={year} onClick={changeYear} onClickTypeInYear={changeTypeInYear} />
            )}
      </div>
      <div className="w-full lg:w-4/5" >
        <RunMap 
          title={title}
          viewState={viewState}
          geoData={geoData}  // 👈 最终传递给 Mapbox
          setViewState={setViewState}
          changeYear={changeYear}
          thisYear={year}
          // 新增传递选中ID
          selectedRunIds={selectedRunIds}
          
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
      {import.meta.env.VERCEL && <Analytics /> }
    </Layout>
  );
};

export default Index;
