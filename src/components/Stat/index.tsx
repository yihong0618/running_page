import { CSSProperties } from 'react';
import { intComma } from '@/utils/utils';

const divStyle: CSSProperties = {
  fontWeight: '700',
};

interface IStatProperties {
  value: string | number;
  description: string;
  className?: string;
  citySize?: number;
  onClick?: () => void;
}

const Stat = ({ value, description, className = 'pb-2 w-full', citySize, onClick }: IStatProperties) => (
  <div className={`${className}`} onClick={onClick}>
    <span className={`text-${citySize || 5}xl font-black italic`} style={divStyle}>
      {intComma(value.toString())}
    </span>
    <span className="text-lg font-semibold italic">{description}</span>
  </div>
);

export default Stat;
