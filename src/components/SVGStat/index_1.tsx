import { lazy, Suspense } from 'react';
// import { totalStat } from '@assets/index';
// import {  generateTotalStat }from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';

// Lazy load both github.svg and grid.svg
// const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg'));

// const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg'));

// const SVGStat = () => (
//   <div id="svgStat">
//     <Suspense fallback={<div className="text-center">Loading...</div>}>
//       <GridSvg className="mt-4 h-auto w-full" />
//       <GithubSvg className="mt-4 h-auto w-full" />
//     </Suspense>
//   </div>
// );



const SVGStat = ({ year = 'Total' }) => {
  const totalStat = import.meta.glob(['./github.svg', './grid.svg'], { import: 'ReactComponent' });
  const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg'));

const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg'));

  // const totalStat = generateTotalStat(year);
  // const initialPaths = ['./github.svg', './grid.svg'];
  // const totalStat = await generateTotalStat(year, initialPaths);
  // const GithubSvg = lazy(() => loadSvgComponent(totalStat, year === 'Total'? './github.svg' : './github_${y}.svg'));
  // const GridSvg = lazy(() => loadSvgComponent(totalStat, year === 'Total'? './grid.svg' : './grid_${y}.svg'));
  // const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg', year));
  // const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg', year));
  return (
    <div id="svgStat">
      <Suspense fallback={<div className="text-center">Loading...</div>}>
        
        <GithubSvg className="mt-4 h-auto w-full" />
        <GridSvg className="mt-4 h-auto w-full" />
      </Suspense>
    </div>
  );
};

export default SVGStat;
