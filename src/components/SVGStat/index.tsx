import { ComponentType, lazy, Suspense } from 'react'
import styles from './style.module.scss';
import { totalStat } from '@assets/index'

// Lazy load both github.svg and grid.svg
const GithubSvg = lazy(() =>
  totalStat['./github.svg']()
    .then((res) => {
      return { default: res as ComponentType<any> }
    })
    .catch(() => {
      return { default: () => <div>Failed to load SVG</div> };
    })
)

const GridSvg = lazy(() =>
  totalStat['./grid.svg']()
    .then((res) => {
      return { default: res as ComponentType<any> }
    })
    .catch(() => {
      return { default: () => <div>Failed to load SVG</div> };
    })
)

const SVGStat = () => (
  <div id="svgStat">
    <Suspense fallback={<div className={styles.center}>Loading...</div>}>
      <GithubSvg className={styles.runSVG} />
      <GridSvg className={styles.runSVG} />
    </Suspense>
  </div>
);

export default SVGStat;
