import { intComma } from '@/utils/utils';

interface IStatProperties {
  value: string | number;
  description: string;
  className?: string;
  citySize?: number;
  onClick?: () => void;
  style?: React.CSSProperties; // 新增：用于接收动态样式的属性
}

const Stat = ({
  value,
  description,
  className = 'pb-2 w-full',
  citySize,
  onClick,
  style // 新增：解构出 style 属性
}: IStatProperties) => (
  <div className={`${className}`} onClick={onClick} style={style}> {/* 新增：应用传入的样式 */}
    <span className={`text-${citySize || 2}xl font-semibold italic`}>
      {intComma(value.toString())}
    </span>
    <span className="text-2xl font-semibold italic"> - {description}</span>
  </div>
);

export default Stat;
