import { ComponentType } from 'react';

type SvgComponent = {
  default: ComponentType<any>;
};

const FailedLoadSvg = () => <div>Failed to load SVG</div>;

export const loadSvgComponent = async (
  stats: Record<string, () => Promise<unknown>>,
  path: string,
  year: string = 'Total'
): Promise<SvgComponent> => {
  // 新增参数
  let actualPath = path;
  if (year!== 'Total') {
    actualPath = path.replace('.svg', '_${year}.svg');
  }
  try {
    const module = await stats[path]();

    return { default: module as ComponentType<any> };
  } catch (error) {
    console.error(error);
    return { default: FailedLoadSvg };
  }
};
