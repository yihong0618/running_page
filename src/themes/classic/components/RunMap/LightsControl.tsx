import styles from './style.module.css';

interface ILightsProps {
  setLights: (_lights: boolean) => void;
  lights: boolean;
}

const LightsControl = ({ setLights, lights }: ILightsProps) => {
  return (
    <div className={'mapboxgl-ctrl mapboxgl-ctrl-group ' + styles.lights}>
      <button
        type="button"
        aria-label={lights ? 'Hide base map' : 'Show base map'}
        title={lights ? 'Hide base map' : 'Show base map'}
        aria-pressed={lights}
        className={`${lights ? styles.lightsOn : styles.lightsOff}`}
        onClick={() => setLights(!lights)}
      >
        <span
          className="mapboxgl-ctrl-icon"
          aria-hidden="true"
          title={'Turn ' + `${lights ? 'off' : 'on'}` + ' the Light'}
        ></span>
      </button>
    </div>
  );
};

export default LightsControl;
