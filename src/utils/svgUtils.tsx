import { ComponentType } from 'react';

type SvgComponent = {
  default: ComponentType<any>;
};

const FailedLoadSvg = () => <div>Failed to load SVG</div>;

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
