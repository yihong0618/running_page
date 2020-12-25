import React from 'react';
import { intComma } from 'src/utils/utils';

const Stat = ({ value, description, className, citySize, onClick }) => (
  <div className={`${className} pb2 w-100`} onClick={onClick}>
    <span className={`f${citySize || 1} fw9 i`}>{intComma(value)}</span>
    <span className="f3 fw6 i">{description}</span>
  </div>
);

export default Stat;
