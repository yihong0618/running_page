import React from 'react';
import { intComma } from '@/utils/utils';

const divStyle: React.CSSProperties = {
  fontWeight: '700',
};

interface IStatProperties {
  value: string | number;
  description: string;
  className?: string;
  citySize?: number;
  onClick?: () => void;
}

const Stat = ({ value, description, className = 'pb2 w-100', citySize, onClick }: IStatProperties) => (
  <div className={`${className}`} onClick={onClick}>
    <span className={`f${citySize || 1} fw9 i`} style={divStyle}>
      {intComma(value.toString())}
    </span>
    <span className="f3 fw6 i">{description}</span>
  </div>
);

export default Stat;
