import React from 'react';
import { intComma } from 'src/utils/utils';


const WorkoutStat = ({ value, description, pace, className, distance, onClick }) => (
  <div className={`${className} pb2 w-100`} onClick={onClick}>
    <span className={`f1 fw9 i`}>{intComma(value)}</span>
    <span className="f3 fw6 i">{description}</span>
    { pace && (<span className="f1 fw9 i">{ " " +pace}</span>)}
    { pace && (<span className="f3 fw6 i"> Pace</span>)}

    { distance && (<span className="f1 fw9 i">{ " " + distance}</span>)}
    { distance && (<span className="f3 fw6 i"> KM</span>)}

  </div>
);

export default WorkoutStat;
