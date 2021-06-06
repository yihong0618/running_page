import EndSvg from 'assets/end.svg';
import StartSvg from 'assets/start.svg';
import React from 'react';
import { Marker } from 'react-map-gl';
import styles from './style.module.scss';

const RunMarker = ({ startLon, startLat, endLon, endLat }) => {
  const size = 20;
  return (
    <div>
      <Marker key="maker_start" longitude={startLon} latitude={startLat}>
        <div
          style={{
            transform: `translate(${-size / 2}px,${-size}px)`,
            maxWidth: '25px',
          }}
        >
          <StartSvg className={styles.locationSVG} />
        </div>
      </Marker>
      <Marker key="maker_end" longitude={endLon} latitude={endLat}>
        <div
          style={{
            transform: `translate(${-size / 2}px,${-size}px)`,
            maxWidth: '25px',
          }}
        >
          <EndSvg className={styles.locationSVG} />
        </div>
      </Marker>
    </div>
  );
};

export default RunMarker;
