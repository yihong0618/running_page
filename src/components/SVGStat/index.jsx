import React from 'react';
import GitHubSvg from 'assets/github.svg';
import GridSvg from 'assets/grid.svg';
import styles from './style.module.scss';

const SVGStat = () => (
  <div>
    <GitHubSvg className={styles.runSVG} />
    <GridSvg className={styles.runSVG} />
  </div>
);

export default SVGStat;
