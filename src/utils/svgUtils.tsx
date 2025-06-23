import { ComponentType } from 'react';

type SvgComponent = {
  default: ComponentType<any>;
};

const FailedLoadSvg = () => {
  console.log('Failed to load SVG component');
  return <div></div>;
};

export const loadSvgComponent = async (
  stats: Record<string, () => Promise<unknown>>,
  path: string
): Promise<SvgComponent> => {
  try {
    const module = await stats[path]();
    return { default: module as ComponentType<any> };
  } catch (error) {
    console.error(error);
    return { default: FailedLoadSvg };
  }
};
