import { lazy, Suspense } from 'react'
import styles from './style.module.scss';
import { totalStat } from '@assets/index'
import { loadSvgComponent } from '@/utils/svgUtils';

// Lazy load both github.svg and grid.svg
const GithubSvg = lazy(() => loadSvgComponent(totalStat, './github.svg'))

const GridSvg = lazy(() => loadSvgComponent(totalStat, './grid.svg'))

const SVGStat = () => (
  <div id="svgStat">
    <Suspense fallback={<div className={styles.center}>Loading...</div>}>
      <GithubSvg className={styles.runSVG} />
      <GridSvg className={styles.runSVG} />
    </Suspense>
  </div>
);

export default SVGStat;
