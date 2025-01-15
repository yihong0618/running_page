export const yearStats = import.meta.glob('./year_*.svg', { import: 'ReactComponent' })
export const totalStat = import.meta.glob(['./github.svg', './grid.svg'], { import: 'ReactComponent' })
// export const generateTotalStat = (year: string = 'Total'): Record<string, () => Promise<unknown>> => {
//     let paths = ['./github.svg', './grid.svg'];
//     if (year!== 'Total') {
//       paths = paths.map(path => path.replace('.svg', `_${year}.svg`));
//     }
//     return import.meta.glob(paths, { import: 'ReactComponent' });
//   };

// export const generateTotalStat = async (year: string = 'Total', paths: string[] = []) => {
//     if (year!== 'Total') {
//       paths = paths.map(path => path.replace('.svg', `_${year}.svg`));
//     }
//     const stats: Record<string, () => Promise<unknown>> = {};
//     for (const path of paths) {
//       // 使用动态导入
//       stats[path] = async () => (await import(`./${path}`)).default;
//     }
//     return stats;
//   };