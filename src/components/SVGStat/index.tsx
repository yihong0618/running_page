import React from 'react';
import { ReactComponent as GitHubSvg } from '@assets/github.svg';
import { ReactComponent as GridSvg } from '@assets/grid.svg';
import styles from './style.module.scss';

const SVGStat = () => (
  <div id="svgStat">
    <GitHubSvg className={styles.runSVG} />
    <GridSvg className={styles.runSVG} />
  </div>
);

export default SVGStat;
