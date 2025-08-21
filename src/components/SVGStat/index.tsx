import { lazy, Suspense } from 'react';
import { totalStat } from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';

// Lazy load both github.svg and grid.svg
const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg'));

const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg'));

const SVGStat = () => (
  <div id="svgStat">
    <Suspense fallback={<div className="text-center">Loading...</div>}>
      <GithubSvg className="github-svg mt-4 h-auto w-full" />
      <GridSvg className="grid-svg mt-4 h-auto w-full" />
    </Suspense>
  </div>
);

export default SVGStat;
