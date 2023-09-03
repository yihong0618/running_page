import React from 'react';
import { intComma } from 'src/utils/utils';

const divStyle = {
  fontWeight: '700',
};

const Stat = ({ value, description, className = 'pb2 w-100', citySize, onClick }) => (
  <div className={`${className}`} onClick={onClick}>
    <span className={`f${citySize || 1} fw9 i`} style={divStyle}>
      {intComma(value)}
    </span>
    <span className="f3 fw6 i">{description}</span>
  </div>
);

export default Stat;
