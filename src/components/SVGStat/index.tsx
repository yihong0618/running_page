import React from 'react';
import { ReactComponent as GitHubSvg } from '@assets/github.svg';
import { ReactComponent as GridSvg } from '@assets/grid.svg';
import styles from './style.module.scss';

const SVGStat = () => (
  <div id="svgStat">
    <GridSvg className={styles.runSVG} />
    <GitHubSvg className={styles.runSVG} />
  </div>
);

export default SVGStat;
