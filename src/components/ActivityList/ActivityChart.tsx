import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { DIST_UNIT } from '@/utils/utils';

interface ChartData {
  day: number;
  distance: string;
}

interface ActivityChartProps {
  data: ChartData[];
  yAxisMax: number;
  yAxisTicks: number[];
}

const ActivityChart = ({ data, yAxisMax, yAxisTicks }: ActivityChartProps) => (
  <ResponsiveContainer>
    <BarChart data={data} margin={{ top: 20, right: 20, left: -20, bottom: 5 }}>
      <CartesianGrid
        strokeDasharray="3 3"
        stroke="var(--color-run-row-hover-background)"
      />
      <XAxis dataKey="day" tick={{ fill: 'var(--color-run-table-thead)' }} />
      <YAxis
        label={{
          value: DIST_UNIT,
          angle: -90,
          position: 'insideLeft',
          fill: 'var(--color-run-table-thead)',
        }}
        domain={[0, yAxisMax]}
        ticks={yAxisTicks}
        tick={{ fill: 'var(--color-run-table-thead)' }}
      />
      <Tooltip
        formatter={(value) => `${value} ${DIST_UNIT}`}
        contentStyle={{
          backgroundColor: 'var(--color-run-row-hover-background)',
          border: '1px solid var(--color-run-row-hover-background)',
          color: 'var(--color-run-table-thead)',
        }}
        labelStyle={{ color: 'var(--color-primary)' }}
      />
      <Bar dataKey="distance" fill="var(--color-primary)" />
    </BarChart>
  </ResponsiveContainer>
);

export default ActivityChart;
