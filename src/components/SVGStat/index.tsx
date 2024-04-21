import { lazy, Suspense } from 'react';
import { totalStat } from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';

// Lazy load both github.svg and grid.svg
const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg'));

const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg'));

const SVGStat = () => (
  <div id="svgStat">
    <Suspense fallback={<div className="text-center">Loading...</div>}>
      <GridSvg className="mt-4 h-auto w-full" />
      <GithubSvg className="mt-4 h-auto w-full" />
    </Suspense>
  </div>
);

export default SVGStat;
