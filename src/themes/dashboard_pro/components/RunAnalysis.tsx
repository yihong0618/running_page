import {
  Suspense,
  use,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent,
  type ReactNode,
} from 'react';
import type { Activity } from '@/types';
import { useLocale } from '@/hooks/useLocale';
import {
  formatClock,
  formatPaceSeconds,
  formatPaceZoneRange,
  loadSplits,
  loadSplitsIndex,
  paceZonesFromChart,
  thresholdPaceFromVo2max,
  type RunChart,
  type RunSplits,
  type SplitRow,
  type ZoneInfo,
} from '@/core/splits';

type N = number | null | undefined;
type Tr = (zh: string, en: string) => string;

const ZONE_COLORS = [
  '#9ca3af',
  '#5b9bd5',
  '#7cb342',
  '#f4c430',
  '#f59e0b',
  '#ef4444',
];

/** Garmin-ish metric colors */
const C = {
  pace: '#3b82f6',
  hr: '#ef4444',
  power: '#a855f7',
  cad: '#f97316',
  stride: '#14b8a6',
  vo: '#ec4899',
  gct: '#84cc16',
  alt: '#ca8a04',
  vr: '#a16207',
} as const;

const TE_GRADIENT =
  'linear-gradient(90deg,#3b82f6 0%,#22c55e 35%,#eab308 65%,#f97316 100%)';

const SHEET_MS = 200;

const CHART_W = 720;
const CHART_H = 112;
const PAD = { t: 6, r: 6, b: 16, l: 34 };

const has = (v: N): v is number => v != null && Number.isFinite(v);
const fmt = (v: N, d = 0) => (has(v) ? v.toFixed(d) : '--');

function useTr(): Tr {
  const { locale } = useLocale();
  return (zh, en) => (locale === 'zh' ? zh : en);
}

function smooth(values: (number | null)[], window = 5): (number | null)[] {
  return values.map((v, i) => {
    if (!has(v)) return v;
    const win = values
      .slice(Math.max(0, i - Math.floor(window / 2)), i + Math.ceil(window / 2))
      .filter((x): x is number => has(x));
    win.sort((a, b) => a - b);
    return win[Math.floor(win.length / 2)];
  });
}

function domain(values: number[], robust = true): [number, number] {
  const sorted = [...values].sort((a, b) => a - b);
  const q = (p: number) =>
    sorted[
      Math.min(
        sorted.length - 1,
        Math.max(0, Math.round(p * (sorted.length - 1)))
      )
    ];
  let lo = robust ? q(0.02) : sorted[0];
  let hi = robust ? q(0.98) : sorted[sorted.length - 1];
  if (hi - lo < 1e-6) {
    lo -= 1;
    hi += 1;
  }
  const pad = (hi - lo) * 0.12;
  return [lo - pad, hi + pad];
}

/** Colour index for an HR sample. Without FIT zone boundaries, falls back to
 * an estimate of 50/60/70/80/90 % of the max HR seen in this activity. */
function hrZoneIndex(
  hr: number,
  boundaries: (number | null)[] | null | undefined,
  maxHr?: number | null
): number {
  if (!boundaries?.length) {
    if (!maxHr || maxHr <= 0) return 2;
    const pct = hr / maxHr;
    if (pct < 0.5) return 0;
    if (pct < 0.6) return 1;
    if (pct < 0.7) return 2;
    if (pct < 0.8) return 3;
    if (pct < 0.9) return 4;
    return 5;
  }
  for (let i = 0; i < boundaries.length; i++) {
    const hi = boundaries[i];
    if (hi != null && hr <= hi) return i;
  }
  return Math.min(5, boundaries.length);
}

/** stride (m) from pace (s/km) and cadence (spm). */
function seriesMax(series?: (number | null)[]): number | null {
  const vals = (series ?? []).filter((v): v is number => has(v));
  return vals.length ? Math.max(...vals) : null;
}

/** Prefer the chart series max when summary cadence_max is a sensor spike. */
function cadenceChipMax(summaryMax: N, series?: (number | null)[]): N {
  const vals = (series ?? []).filter((v): v is number => has(v));
  const seriesMax = vals.length ? Math.max(...vals) : null;
  if (has(summaryMax) && has(seriesMax) && summaryMax > seriesMax * 1.15) {
    return Math.round(seriesMax);
  }
  return summaryMax;
}

function strideFrom(pace: N, cad: N): number | null {
  if (!has(pace) || !has(cad) || pace <= 0 || cad <= 0) return null;
  return 60000 / (pace * cad);
}

function enrichChart(
  chart: RunChart
): RunChart & { stride?: (number | null)[] } {
  const pace = chart.pace;
  const cad = chart.cad;
  if (!pace || !cad) return chart;
  const stride = pace.map((p, i) => strideFrom(p, cad[i]));
  if (!stride.some((v) => has(v))) return chart;
  return { ...chart, stride };
}

/** Build X values: distance (km) or time (seconds). Fallback: integrate pace. */
function chartAxis(
  chart: RunChart & { stride?: (number | null)[] },
  mode: 'distance' | 'time'
): number[] {
  if (mode === 'distance') return chart.d;
  if (chart.t && chart.t.length === chart.d.length) return chart.t;
  // Derive time from pace × Δdistance when FIT chart lacks t.
  const xs = [0];
  for (let i = 1; i < chart.d.length; i++) {
    const pace = chart.pace?.[i] ?? chart.pace?.[i - 1];
    const dd = Math.max(0, chart.d[i] - chart.d[i - 1]);
    const dt = has(pace) && pace > 0 ? pace * dd : 0;
    xs.push(xs[i - 1] + dt);
  }
  return xs;
}

function formatAxis(v: number, mode: 'distance' | 'time'): string {
  if (mode === 'distance') return v.toFixed(1);
  const s = Math.max(0, Math.round(v));
  const m = Math.floor(s / 60);
  const r = String(s % 60).padStart(2, '0');
  return m >= 60
    ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}:${r}`
    : `${m}:${r}`;
}

// ---------------------------------------------------------------- metric grid (Garmin 2-col)
function MetricCell({
  label,
  value,
  unit,
  sub,
}: {
  label: string;
  value: string;
  unit?: string;
  sub?: string;
}) {
  return (
    <div className="min-w-0 border-b border-[var(--color-border)]/70 py-2.5 pr-3">
      <p className="text-[11px] text-[var(--color-muted)]">{label}</p>
      <p className="metric mt-0.5 text-[17px] leading-tight font-semibold tracking-tight">
        {value}
        {unit ? (
          <span className="ml-1 text-[11px] font-normal text-[var(--color-muted)]">
            {unit}
          </span>
        ) : null}
      </p>
      {sub ? (
        <p className="metric mt-0.5 text-[10px] text-[var(--color-muted)]">
          {sub}
        </p>
      ) : null}
    </div>
  );
}

function MetricGrid({ data, tr }: { data: RunSplits; tr: Tr }) {
  const s = data.summary;
  const altPeak = seriesMax(data.chart?.alt);
  const cells: {
    key: string;
    label: string;
    value: string;
    unit?: string;
    sub?: string;
    show: boolean;
  }[] = [
    {
      key: 'cal',
      label: tr('卡路里', 'Calories'),
      value: fmt(s.calories),
      unit: 'kcal',
      show: has(s.calories),
    },
    {
      key: 'hr',
      label: tr('平均心率', 'Avg HR'),
      value: fmt(s.hr_avg),
      unit: 'bpm',
      sub: has(s.hr_max) ? `${tr('最大', 'Max')} ${s.hr_max}` : undefined,
      show: has(s.hr_avg),
    },
    {
      key: 'cad',
      label: tr('平均步频', 'Avg cadence'),
      value: fmt(s.cadence_avg),
      unit: 'spm',
      show: has(s.cadence_avg),
    },
    {
      key: 'elev',
      label: tr('累计爬升', 'Ascent'),
      value: fmt(s.elev_gain),
      unit: 'm',
      sub:
        [
          has(s.elev_loss)
            ? `${tr('下降', 'Descent')} ${fmt(s.elev_loss)} m`
            : null,
          has(altPeak)
            ? `${tr('最高海拔', 'Max elev.')} ${fmt(altPeak)} m`
            : null,
        ]
          .filter(Boolean)
          .join(' · ') || undefined,
      show: has(s.elev_gain) || has(s.elev_loss),
    },
    {
      key: 'te',
      label: tr('有氧训练效果', 'Aerobic TE'),
      value: fmt(s.aerobic_te, 1),
      sub: has(s.anaerobic_te)
        ? `${tr('无氧', 'Anaerobic')} ${fmt(s.anaerobic_te, 1)}`
        : undefined,
      show: has(s.aerobic_te),
    },
    {
      key: 'power',
      label: tr('平均功率', 'Avg power'),
      value: fmt(s.power_avg),
      unit: 'W',
      sub: has(s.power_max) ? `${tr('最大', 'Max')} ${s.power_max}` : undefined,
      show: has(s.power_avg),
    },
    {
      key: 'stride',
      label: tr('平均步幅', 'Avg stride'),
      value: fmt(s.stride_length, 2),
      unit: 'm',
      show: has(s.stride_length),
    },
    {
      key: 'vo',
      label: tr('垂直振幅', 'Vert. osc.'),
      value: fmt(s.vertical_oscillation, 1),
      unit: 'cm',
      show: has(s.vertical_oscillation),
    },
    {
      key: 'gct',
      label: tr('触地时间', 'Ground contact'),
      value: fmt(s.ground_contact_time),
      unit: 'ms',
      show: has(s.ground_contact_time),
    },
    {
      key: 'load',
      label: tr('训练负荷', 'Training load'),
      value: fmt(s.training_load),
      show: has(s.training_load),
    },
    {
      key: 'temp',
      label: tr('气温', 'Air temp'),
      value: fmt(s.temperature),
      unit: '°C',
      sub:
        has(s.temperature_min) || has(s.temperature_max)
          ? `${fmt(s.temperature_min)}–${fmt(s.temperature_max)}`
          : undefined,
      show: s.temperature_source === 'weather' && has(s.temperature),
    },
  ];
  const shown = cells.filter((c) => c.show);
  return (
    <div className="grid grid-cols-2 gap-x-4">
      {shown.map((c) => (
        <MetricCell
          key={c.key}
          label={c.label}
          value={c.value}
          unit={c.unit}
          sub={c.sub}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- TE scale (0–5)
function TeScaleRow({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, (value / 5) * 100));
  return (
    <div className="mb-2.5 last:mb-0">
      <div className="mb-1 flex items-baseline justify-between text-[12px]">
        <span className="text-[var(--color-muted)]">{label}</span>
        <span className="metric font-semibold">{value.toFixed(1)}</span>
      </div>
      <div className="relative h-2 rounded-full bg-[var(--color-sunken)]">
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: '100%', background: TE_GRADIENT, opacity: 0.35 }}
        />
        <div
          className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[var(--color-text)] shadow"
          style={{ left: `${pct}%` }}
        />
      </div>
      <div className="mt-0.5 flex justify-between text-[9px] text-[var(--color-muted)]">
        <span>0</span>
        <span>5.0</span>
      </div>
    </div>
  );
}

function TeScale({
  aerobic,
  anaerobic,
  tr,
}: {
  aerobic: N;
  anaerobic: N;
  tr: Tr;
}) {
  if (!has(aerobic) && !has(anaerobic)) return null;
  return (
    <div>
      <p className="mb-2 text-[13px] font-semibold">
        {tr('训练效果', 'Training effect')}
      </p>
      {has(aerobic) ? (
        <TeScaleRow label={tr('有氧', 'Aerobic')} value={aerobic} />
      ) : null}
      {has(anaerobic) ? (
        <TeScaleRow label={tr('无氧', 'Anaerobic')} value={anaerobic} />
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------- zones
/** HR/power: higher number = higher zone. */
function formatZoneRange(
  unit: string,
  lo: number | null | undefined,
  hi: number | null | undefined,
  i: number
): string {
  if (i === 0) return has(hi) ? `< ${Math.round(hi)}` : '';
  if (!has(lo)) return '';
  if (has(hi) && hi < 4000) {
    return `${Math.round(Number(lo) + (unit === 'bpm' ? 1 : 0))}–${Math.round(hi)}`;
  }
  return `≥ ${Math.round(lo)}`;
}

function ZoneTable({
  title,
  zone,
  colors,
  unit,
  tr,
  labels,
}: {
  title: string;
  zone: ZoneInfo;
  colors: string[];
  unit: string;
  tr: Tr;
  labels?: string[];
}) {
  const secs = zone.seconds;
  const total = secs.reduce((a, b) => a + b, 0);
  if (!total) return null;
  // Zones not configured on the device (HR % of max, chart-derived pace).
  const estimated = /estimated|derived/.test(zone.calc_type ?? '');
  const hb = zone.high_boundary ?? [];
  const rows = secs
    .map((sec, i) => {
      const lo = i === 0 ? null : hb[i - 1];
      const hi = hb[i];
      const range =
        unit === '/km'
          ? formatPaceZoneRange(lo, hi, i)
          : formatZoneRange(unit, lo, hi, i);
      const name = labels?.[i] ?? (i === 0 ? '<Z1' : `Z${i}`);
      return {
        i,
        sec,
        pct: (sec / total) * 100,
        range,
        name,
        color: colors[Math.min(i, colors.length - 1)],
      };
    })
    .filter((r) => r.sec > 0);
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <p className="flex items-center gap-1.5 text-[13px] font-semibold">
          {title}
          {estimated ? (
            <span
              className="rounded bg-[var(--color-sunken)] px-1.5 py-px text-[10px] font-normal text-[var(--color-muted)]"
              title={tr(
                '设备未提供区间，按本次数据估算',
                'No device zones; estimated from this activity'
              )}
            >
              {tr('估算', 'Estimated')}
            </span>
          ) : null}
        </p>
        {has(zone.max_hr) ? (
          <p className="text-[10px] text-[var(--color-muted)]">
            {tr('最大', 'Max')} {zone.max_hr}
            {has(zone.threshold_hr) && zone.threshold_hr > 0
              ? ` · LTHR ${zone.threshold_hr}`
              : ''}
          </p>
        ) : has(zone.ftp) ? (
          <p className="text-[10px] text-[var(--color-muted)]">
            FTP {zone.ftp} W
          </p>
        ) : has(zone.threshold_pace) ? (
          <p className="text-[10px] text-[var(--color-muted)]">
            LTP {formatPaceSeconds(zone.threshold_pace)}
          </p>
        ) : null}
      </div>
      <div className="space-y-2">
        {rows.map((r) => (
          <div
            key={r.i}
            className={`grid items-center gap-2 text-[11px] ${
              unit === '/km'
                ? 'grid-cols-[7.25rem_1fr_auto]'
                : 'grid-cols-[4.5rem_1fr_auto]'
            }`}
          >
            <div className="min-w-0">
              <p className="font-medium text-[var(--color-text)]">{r.name}</p>
              {r.range ? (
                <p className="truncate text-[10px] text-[var(--color-muted)]">
                  {r.range}
                  {unit === '/km' ? '' : ` ${unit}`}
                </p>
              ) : null}
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[var(--color-sunken)]">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.max(2, r.pct)}%`,
                  backgroundColor: r.color,
                }}
              />
            </div>
            <div className="metric w-[4.75rem] text-right text-[var(--color-muted)]">
              {formatClock(r.sec)}
              <span className="ml-1 text-[var(--color-text)]">
                {Math.round(r.pct)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function paceZoneLabels(zone: ZoneInfo): string[] | undefined {
  const n = zone.seconds.length;
  if (n <= 5) return zone.seconds.map((_, i) => `Z${i + 1}`);
  return undefined;
}

// ---------------------------------------------------------------- trend chart (佳速度-style cards)
type ChartKind = 'area' | 'hr-area' | 'scatter';

interface TrendDef {
  key: string;
  title: string;
  unit: string;
  color: string;
  kind: ChartKind;
  invert?: boolean;
  format: (v: number) => string;
  avg?: N;
  max?: N;
  extra?: N;
  avgLabel?: string;
  maxLabel?: string;
  extraLabel?: string;
  series: (number | null)[];
}

function MetricCard({
  def,
  xs,
  mode,
  hover,
  onHover,
  zoneBounds,
  footer,
}: {
  def: TrendDef;
  xs: number[];
  mode: 'distance' | 'time';
  hover: number | null;
  onHover: (i: number | null) => void;
  zoneBounds?: (number | null)[] | null;
  footer?: ReactNode;
}) {
  const ys = useMemo(() => {
    if (def.kind === 'scatter') return def.series;
    if (def.kind === 'hr-area') return def.series;
    return smooth(def.series, 5);
  }, [def.series, def.kind]);
  const valid = useMemo(() => ys.filter((v): v is number => has(v)), [ys]);
  const avgVal = has(def.avg)
    ? def.avg
    : valid.length
      ? valid.reduce((a, b) => a + b, 0) / valid.length
      : null;

  const geom = useMemo(() => {
    if (valid.length < 2 || xs.length < 2) return null;
    const [lo, hi] = domain(valid, def.kind !== 'area');
    const x0 = xs[0];
    const x1 = xs[xs.length - 1] || 1;
    const iw = CHART_W - PAD.l - PAD.r;
    const ih = CHART_H - PAD.t - PAD.b;
    const px = (x: number) => PAD.l + ((x - x0) / (x1 - x0 || 1)) * iw;
    const py = (v: number) => {
      const c = Math.min(hi, Math.max(lo, v));
      const t = (c - lo) / (hi - lo);
      return def.invert ? PAD.t + t * ih : PAD.t + (1 - t) * ih;
    };
    const ticks = [lo, (lo + hi) / 2, hi].map((v) => ({
      y: py(v),
      label: def.format(v),
    }));
    const xTicks = [0, 0.5, 1].map((frac) => {
      const x = x0 + frac * (x1 - x0);
      return { x: px(x), label: formatAxis(x, mode) };
    });
    return { px, py, lo, hi, ticks, xTicks, x0, x1, iw, ih };
  }, [xs, valid, def, mode]);

  if (!geom) return null;

  const handleMove = (e: PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const target = geom.x0 + frac * (geom.x1 - geom.x0);
    let best = 0;
    for (let i = 1; i < xs.length; i++) {
      if (Math.abs(xs[i] - target) < Math.abs(xs[best] - target)) best = i;
    }
    onHover(best);
  };

  let linePath = '';
  let areaPath = '';
  const hrSegs: { d: string; color: string }[] = [];
  const dots: { x: number; y: number; color: string }[] = [];

  if (def.kind === 'scatter') {
    ys.forEach((v, i) => {
      if (!has(v)) return;
      // Color outliers vs avg
      let color = def.color;
      if (has(avgVal)) {
        const rel = Math.abs(v - avgVal) / Math.max(1, Math.abs(avgVal));
        if (rel > 0.18) color = '#f97316';
        if (rel > 0.35) color = '#ef4444';
      }
      dots.push({ x: geom.px(xs[i]), y: geom.py(v), color });
    });
  } else if (def.kind === 'hr-area') {
    let cur = '';
    let color = ZONE_COLORS[1];
    let pen = false;
    ys.forEach((v, i) => {
      if (!has(v)) {
        if (pen && cur) hrSegs.push({ d: cur, color });
        pen = false;
        cur = '';
        return;
      }
      const c = ZONE_COLORS[hrZoneIndex(v, zoneBounds, def.max)];
      const pt = `${geom.px(xs[i]).toFixed(1)},${geom.py(v).toFixed(1)}`;
      if (pen && c !== color) {
        hrSegs.push({ d: cur, color });
        const prev = i > 0 && has(ys[i - 1]) ? ys[i - 1]! : v;
        cur = `M${geom.px(xs[i - 1] ?? xs[i]).toFixed(1)},${geom.py(prev).toFixed(1)}L${pt}`;
        color = c;
      } else {
        if (!pen) color = c;
        cur += `${pen ? 'L' : 'M'}${pt}`;
      }
      pen = true;
    });
    if (pen && cur) hrSegs.push({ d: cur, color });
    let area = '';
    let ap = false;
    ys.forEach((v, i) => {
      if (!has(v)) {
        ap = false;
        return;
      }
      area += `${ap ? 'L' : 'M'}${geom.px(xs[i]).toFixed(1)},${geom.py(v).toFixed(1)}`;
      ap = true;
    });
    if (area) {
      areaPath = `${area}L${geom.px(xs[xs.length - 1]).toFixed(1)},${(PAD.t + geom.ih).toFixed(1)}L${geom.px(xs[0]).toFixed(1)},${(PAD.t + geom.ih).toFixed(1)}Z`;
    }
  } else {
    let pen = false;
    ys.forEach((v, i) => {
      if (!has(v)) {
        pen = false;
        return;
      }
      linePath += `${pen ? 'L' : 'M'}${geom.px(xs[i]).toFixed(1)},${geom.py(v).toFixed(1)}`;
      pen = true;
    });
    if (linePath) {
      areaPath = `${linePath}L${geom.px(xs[xs.length - 1]).toFixed(1)},${(PAD.t + geom.ih).toFixed(1)}L${geom.px(xs[0]).toFixed(1)},${(PAD.t + geom.ih).toFixed(1)}Z`;
    }
  }

  const hv = hover != null ? ys[hover] : null;
  // Gain/loss chips on the climb card are not altitude samples; skip a
  // guide line that would sit off the waveform domain.
  const avgY =
    has(avgVal) && avgVal >= geom.lo && avgVal <= geom.hi
      ? geom.py(avgVal)
      : null;

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-3 shadow-[var(--shadow-card)]">
      <div className="mb-1 flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-semibold" style={{ color: def.color }}>
            {def.title}
          </p>
          <div className="mt-0.5 flex flex-wrap items-baseline gap-x-4">
            {has(def.avg) || has(avgVal) ? (
              <p className="metric text-[20px] leading-none font-semibold tracking-tight">
                {def.format((def.avg ?? avgVal) as number)}
                <span className="ml-1 text-[11px] font-normal text-[var(--color-muted)]">
                  {def.unit}
                </span>
                <span className="ml-1.5 text-[10px] font-normal text-[var(--color-muted)]">
                  {def.avgLabel ?? 'Avg'}
                </span>
              </p>
            ) : null}
            {has(def.max) ? (
              <p className="metric text-[13px] text-[var(--color-muted)]">
                {def.format(def.max)}
                <span className="ml-1 text-[10px]">
                  {def.unit} · {def.maxLabel ?? 'Max'}
                </span>
              </p>
            ) : null}
            {has(def.extra) ? (
              <p className="metric text-[13px] text-[var(--color-muted)]">
                {def.format(def.extra)}
                <span className="ml-1 text-[10px]">
                  {def.unit} · {def.extraLabel ?? ''}
                </span>
              </p>
            ) : null}
          </div>
        </div>
        {hover != null ? (
          <p className="metric shrink-0 text-right text-[12px] text-[var(--color-muted)]">
            <span className="font-semibold text-[var(--color-text)]">
              {has(hv) ? def.format(hv) : '--'}
            </span>{' '}
            {def.unit}
            <span className="mt-0.5 block text-[10px]">
              {formatAxis(xs[hover], mode)}
              {mode === 'distance' ? ' km' : ''}
            </span>
          </p>
        ) : null}
      </div>
      <div
        className="relative touch-none select-none"
        onPointerMove={handleMove}
        onPointerDown={handleMove}
        onPointerLeave={() => onHover(null)}
      >
        <svg
          viewBox={`0 0 ${CHART_W} ${CHART_H}`}
          preserveAspectRatio="none"
          className="h-[100px] w-full overflow-visible sm:h-[120px]"
        >
          {geom.ticks.map((tick) => (
            <g key={`y-${tick.label}`}>
              <line
                x1={PAD.l}
                x2={CHART_W - PAD.r}
                y1={tick.y}
                y2={tick.y}
                stroke="var(--color-border)"
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
              <text
                x={PAD.l - 4}
                y={tick.y + 3}
                textAnchor="end"
                fill="var(--color-muted)"
                fontSize="9"
              >
                {tick.label}
              </text>
            </g>
          ))}
          {geom.xTicks.map((tick) => (
            <text
              key={`x-${tick.label}`}
              x={tick.x}
              y={CHART_H - 1}
              textAnchor="middle"
              fill="var(--color-muted)"
              fontSize="9"
            >
              {tick.label}
            </text>
          ))}
          {areaPath ? (
            <path d={areaPath} fill={def.color} opacity={0.18} />
          ) : null}
          {avgY != null ? (
            <line
              x1={PAD.l}
              x2={CHART_W - PAD.r}
              y1={avgY}
              y2={avgY}
              stroke="var(--color-text)"
              strokeOpacity={0.55}
              strokeWidth={1.25}
              strokeDasharray="4 3"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          {def.kind === 'hr-area'
            ? hrSegs.map((s) => (
                <path
                  key={`${s.color}-${s.d.slice(0, 24)}`}
                  d={s.d}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={2}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              ))
            : null}
          {def.kind === 'area' && linePath ? (
            <path
              d={linePath}
              fill="none"
              stroke={def.color}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          {def.kind === 'scatter'
            ? dots.map((d) => (
                <circle
                  key={`${d.x}-${d.y}`}
                  cx={d.x}
                  cy={d.y}
                  r={2.1}
                  fill={d.color}
                  opacity={0.85}
                />
              ))
            : null}
          {hover != null ? (
            <line
              x1={geom.px(xs[hover])}
              x2={geom.px(xs[hover])}
              y1={PAD.t}
              y2={PAD.t + geom.ih}
              stroke="var(--color-text)"
              strokeOpacity={0.3}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>
      </div>
      {footer ? (
        <div className="mt-3 border-t border-[var(--color-border)]/70 pt-3">
          {footer}
        </div>
      ) : null}
    </div>
  );
}

function ChartStack({ data, tr }: { data: RunSplits; tr: Tr }) {
  const base = data.chart;
  const [hover, setHover] = useState<number | null>(null);
  const [axis, setAxis] = useState<'distance' | 'time'>('distance');
  const chart = useMemo(() => (base ? enrichChart(base) : null), [base]);
  if (!chart || chart.d.length < 2) return null;
  const s = data.summary;
  const xs = chartAxis(chart, axis);
  const defs: TrendDef[] = [
    {
      key: 'pace',
      title: tr('配速', 'Pace'),
      unit: '/km',
      color: C.pace,
      kind: 'area',
      invert: true,
      format: (v) => formatPaceSeconds(v),
      avg: s.pace,
      max: s.best_pace,
      avgLabel: tr('平均', 'Avg'),
      maxLabel: tr('最快', 'Best'),
      series: chart.pace ?? [],
    },
    {
      key: 'hr',
      title: tr('心率', 'Heart rate'),
      unit: 'bpm',
      color: C.hr,
      kind: 'hr-area',
      format: (v) => v.toFixed(0),
      avg: s.hr_avg,
      max: s.hr_max,
      avgLabel: tr('平均', 'Avg'),
      maxLabel: tr('最大', 'Max'),
      series: chart.hr ?? [],
    },
    {
      key: 'alt',
      title: tr('爬升', 'Ascent'),
      unit: 'm',
      color: '#22c55e',
      kind: 'area',
      format: (v) => v.toFixed(0),
      avg: s.elev_gain,
      max: s.elev_loss,
      extra: seriesMax(chart.alt),
      avgLabel: tr('爬升', 'Gain'),
      maxLabel: tr('下降', 'Loss'),
      extraLabel: tr('最高海拔', 'Max elev.'),
      series: chart.alt ?? [],
    },
    {
      key: 'power',
      title: tr('功率', 'Power'),
      unit: 'W',
      color: C.power,
      kind: 'area',
      format: (v) => v.toFixed(0),
      avg: s.power_avg,
      max: s.power_max,
      avgLabel: tr('平均', 'Avg'),
      maxLabel: tr('最大', 'Max'),
      series: chart.power ?? [],
    },
    {
      key: 'cad',
      title: tr('步频', 'Cadence'),
      unit: 'spm',
      color: C.cad,
      kind: 'scatter',
      format: (v) => v.toFixed(0),
      avg: s.cadence_avg,
      max: cadenceChipMax(s.cadence_max, chart.cad),
      avgLabel: tr('平均', 'Avg'),
      maxLabel: tr('最大', 'Max'),
      series: chart.cad ?? [],
    },
    {
      key: 'stride',
      title: tr('步幅', 'Stride length'),
      unit: 'm',
      color: C.stride,
      kind: 'scatter',
      format: (v) => v.toFixed(2),
      avg: s.stride_length,
      avgLabel: tr('平均', 'Avg'),
      series: chart.stride ?? [],
    },
    {
      key: 'vo',
      title: tr('垂直振幅', 'Vertical oscillation'),
      unit: 'cm',
      color: C.vo,
      kind: 'scatter',
      format: (v) => v.toFixed(1),
      avg: s.vertical_oscillation,
      avgLabel: tr('平均', 'Avg'),
      series: chart.vo ?? [],
    },
    {
      key: 'vr',
      title: tr('垂直步幅比', 'Vertical ratio'),
      unit: '%',
      color: C.vr,
      kind: 'scatter',
      format: (v) => v.toFixed(1),
      avg: s.vertical_ratio,
      avgLabel: tr('平均', 'Avg'),
      series: chart.vr ?? [],
    },
    {
      key: 'gct',
      title: tr('触地时间', 'Ground contact time'),
      unit: 'ms',
      color: C.gct,
      kind: 'scatter',
      format: (v) => v.toFixed(0),
      avg: s.ground_contact_time,
      avgLabel: tr('平均', 'Avg'),
      series: chart.gct ?? [],
    },
  ];
  const shown = defs.filter((d) => d.series.some((v) => has(v)));
  const paceZones =
    data.zones?.pace ??
    paceZonesFromChart(chart.pace, chart.t, thresholdPaceFromVo2max(s.vo2max));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[13px] font-semibold">{tr('图表', 'Charts')}</p>
        <div className="flex rounded-full bg-[var(--color-sunken)] p-0.5 text-[11px]">
          {(
            [
              ['distance', tr('距离', 'Distance')],
              ['time', tr('时间', 'Time')],
            ] as const
          ).map(([m, label]) => (
            <button
              key={m}
              type="button"
              aria-pressed={axis === m}
              onClick={() => setAxis(m)}
              className={`cursor-pointer rounded-full px-3 py-0.5 transition-colors ${
                axis === m
                  ? 'bg-[var(--color-card)] font-medium text-[var(--color-text)] shadow-sm'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {shown.map((d) => (
        <MetricCard
          key={d.key}
          def={d}
          xs={xs}
          mode={axis}
          hover={hover}
          onHover={setHover}
          zoneBounds={
            d.kind === 'hr-area' ? data.zones?.hr?.high_boundary : null
          }
          footer={
            d.key === 'pace' && paceZones ? (
              <ZoneTable
                title={tr('配速区间', 'Pace zones')}
                zone={paceZones}
                colors={ZONE_COLORS}
                unit="/km"
                tr={tr}
                labels={paceZoneLabels(paceZones)}
              />
            ) : d.key === 'hr' && data.zones?.hr ? (
              <ZoneTable
                title={tr('心率区间', 'HR zones')}
                zone={data.zones.hr}
                colors={ZONE_COLORS}
                unit="bpm"
                tr={tr}
              />
            ) : d.key === 'power' && data.zones?.power ? (
              <ZoneTable
                title={tr('功率区间', 'Power zones')}
                zone={data.zones.power}
                colors={ZONE_COLORS}
                unit="W"
                tr={tr}
              />
            ) : null
          }
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- splits (Garmin-like)
function Delta({ cur, prev, invert }: { cur: N; prev: N; invert?: boolean }) {
  if (!has(cur) || !has(prev) || prev === 0) return null;
  const better = invert ? cur < prev : cur > prev;
  const worse = invert ? cur > prev : cur < prev;
  if (!better && !worse) return null;
  return (
    <span
      className={`ml-0.5 text-[9px] ${better ? 'text-emerald-500' : 'text-rose-500'}`}
      aria-hidden
    >
      {better ? '▲' : '▼'}
    </span>
  );
}

function SplitsBlock({ data, tr }: { data: RunSplits; tr: Tr }) {
  const hasLaps = data.laps.length > 1;
  const [mode, setMode] = useState<'km' | 'laps'>(
    data.splits.length ? 'km' : 'laps'
  );
  const rows = mode === 'km' ? data.splits : data.laps;
  if (!rows.length) return null;

  const paces = rows
    .filter((r) => !r.partial && has(r.pace) && (r.distance ?? 0) >= 200)
    .map((r) => r.pace as number);
  const fast = paces.length ? Math.min(...paces) : 0;
  const slow = paces.length ? Math.max(...paces) : 0;

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[13px] font-semibold">
          {mode === 'km' ? tr('分段', 'Splits') : tr('设备圈', 'Laps')}
        </p>
        {hasLaps && data.splits.length ? (
          <div className="flex rounded-full bg-[var(--color-sunken)] p-0.5 text-[11px]">
            {(['km', 'laps'] as const).map((m) => (
              <button
                key={m}
                type="button"
                aria-pressed={mode === m}
                onClick={() => setMode(m)}
                className={`cursor-pointer rounded-full px-2.5 py-0.5 transition-colors ${
                  mode === m
                    ? 'bg-[var(--color-card)] font-medium text-[var(--color-text)] shadow-sm'
                    : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
                }`}
              >
                {m === 'km'
                  ? tr('每公里', 'Per km')
                  : `${tr('圈', 'Laps')} ${data.laps.length}`}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {/* Garmin-style horizontal pace bars */}
      <div className="mb-3 space-y-1">
        {rows
          .filter((r) => (r.distance ?? 0) >= 50)
          .map((r) => {
            const p = r.pace ?? 0;
            const tiny = (r.distance ?? 0) < 200;
            const ratio =
              slow > fast && has(r.pace)
                ? Math.max(0, Math.min(1, 1 - (p - fast) / (slow - fast)))
                : 0.5;
            const isFast = has(r.pace) && p === fast && !r.partial && !tiny;
            return (
              <div
                key={`bar-${mode}-${r.index}`}
                className={`flex items-center gap-2 text-[11px] ${tiny ? 'opacity-50' : ''}`}
              >
                <span className="metric w-4 shrink-0 text-[var(--color-muted)]">
                  {r.index}
                </span>
                <div className="h-3.5 flex-1 overflow-hidden rounded-sm bg-[var(--color-sunken)]/80">
                  <div
                    className="h-full rounded-sm"
                    style={{
                      width: `${25 + ratio * 75}%`,
                      backgroundColor: C.pace,
                      opacity: 0.35 + ratio * 0.55,
                    }}
                  />
                </div>
                <span
                  className={`metric w-12 shrink-0 text-right ${isFast ? 'font-semibold text-[var(--color-run)]' : ''}`}
                >
                  {formatPaceSeconds(r.pace)}
                </span>
              </div>
            );
          })}
      </div>

      <div className="-mx-0.5 overflow-x-auto">
        <table className="w-full min-w-[400px] text-[12px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-muted)]">
              <th className="py-2 pr-2 font-medium">#</th>
              <th className="py-2 pr-2 font-medium whitespace-nowrap">
                {tr('距离', 'Dist')}
              </th>
              <th className="py-2 pr-2 font-medium whitespace-nowrap">
                {tr('时间', 'Time')}
              </th>
              <th className="py-2 pr-2 font-medium whitespace-nowrap">
                {tr('配速', 'Pace')}
              </th>
              <th className="py-2 pr-2 font-medium whitespace-nowrap">
                {tr('心率', 'HR')}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => {
              const prev: SplitRow | undefined =
                idx > 0 ? rows[idx - 1] : undefined;
              const tiny = (r.distance ?? 0) < 200;
              const isFast =
                has(r.pace) && r.pace === fast && !r.partial && !tiny;
              return (
                <tr
                  key={`${mode}-${r.index}`}
                  className={`border-b border-[var(--color-border)]/50 ${tiny ? 'opacity-50' : ''}`}
                >
                  <td className="metric py-2 pr-2 text-[var(--color-muted)]">
                    {r.index}
                  </td>
                  <td className="metric py-2 pr-2 whitespace-nowrap">
                    {((r.distance ?? 0) / 1000).toFixed(2)}
                  </td>
                  <td className="metric py-2 pr-2 whitespace-nowrap">
                    {formatClock(r.time)}
                  </td>
                  <td
                    className={`metric py-2 pr-2 whitespace-nowrap ${isFast ? 'font-semibold text-[var(--color-run)]' : ''}`}
                  >
                    {formatPaceSeconds(r.pace)}
                    <Delta cur={r.pace} prev={prev?.pace} invert />
                  </td>
                  <td className="metric py-2 pr-2 whitespace-nowrap">
                    {fmt(r.hr_avg)}
                    <Delta cur={r.hr_avg} prev={prev?.hr_avg} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- stack
function AnalysisBody({ data }: { data: RunSplits }) {
  const tr = useTr();
  const s = data.summary;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3 border-b border-[var(--color-border)] pb-3">
        <div>
          <p className="text-[11px] text-[var(--color-muted)]">
            {tr('距离', 'Distance')}
          </p>
          <p className="metric text-xl font-semibold">
            {has(s.distance) ? (s.distance / 1000).toFixed(2) : '--'}
            <span className="ml-1 text-xs font-normal text-[var(--color-muted)]">
              km
            </span>
          </p>
        </div>
        <div>
          <p className="text-[11px] text-[var(--color-muted)]">
            {tr('用时', 'Time')}
          </p>
          <p className="metric text-xl font-semibold">{formatClock(s.time)}</p>
        </div>
        <div>
          <p className="text-[11px] text-[var(--color-muted)]">
            {tr('平均配速', 'Avg pace')}
          </p>
          <p className="metric text-xl font-semibold">
            {formatPaceSeconds(s.pace)}
          </p>
        </div>
      </div>

      <MetricGrid data={data} tr={tr} />

      {(has(s.aerobic_te) || has(s.anaerobic_te)) && (
        <div className="border-t border-[var(--color-border)] pt-4">
          <TeScale aerobic={s.aerobic_te} anaerobic={s.anaerobic_te} tr={tr} />
        </div>
      )}

      <div className="border-t border-[var(--color-border)] pt-4">
        <SplitsBlock data={data} tr={tr} />
      </div>

      {data.chart ? (
        <div className="border-t border-[var(--color-border)] pt-4">
          <ChartStack data={data} tr={tr} />
        </div>
      ) : null}
    </div>
  );
}

function CloseButton({
  onClose,
  label,
}: {
  onClose: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label={label}
      className="cursor-pointer text-[var(--color-muted)] transition-colors hover:text-[var(--color-text)]"
    >
      <svg
        className="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  );
}

function Pulse({ className }: { className: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-[var(--color-sunken)] ${className}`}
    />
  );
}

function AnalysisSkeleton({
  className,
  onClose,
}: {
  className?: string;
  onClose?: () => void;
}) {
  const tr = useTr();
  return (
    <div className={`card p-4 ${className ?? ''}`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <Pulse className="h-4 w-24" />
          <Pulse className="h-3 w-36" />
        </div>
        {onClose ? (
          <CloseButton onClose={onClose} label={tr('关闭', 'Close')} />
        ) : null}
      </div>
      <div className="grid grid-cols-3 gap-3 border-b border-[var(--color-border)] pb-3">
        <div className="space-y-2">
          <Pulse className="h-3 w-10" />
          <Pulse className="h-6 w-16" />
        </div>
        <div className="space-y-2">
          <Pulse className="h-3 w-10" />
          <Pulse className="h-6 w-14" />
        </div>
        <div className="space-y-2">
          <Pulse className="h-3 w-14" />
          <Pulse className="h-6 w-16" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-x-4">
        {Array.from({ length: 6 }, (_, i) => (
          <div
            key={i}
            className="space-y-2 border-b border-[var(--color-border)]/70 py-2.5 pr-3"
          >
            <Pulse className="h-3 w-14" />
            <Pulse className="h-5 w-20" />
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-3">
        <Pulse className="h-3 w-16" />
        <Pulse className="h-2 w-full rounded-full" />
        <Pulse className="h-2 w-full rounded-full" />
      </div>
    </div>
  );
}

function Header({
  data,
  onClose,
  tr,
}: {
  data: RunSplits;
  onClose?: () => void;
  tr: Tr;
}) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h2 className="text-base font-bold">
          {tr('运动分析', 'Run analysis')}
        </h2>
        <p className="truncate text-[11px] text-[var(--color-muted)]">
          {[
            data.device?.toUpperCase(),
            data.sub_sport && data.sub_sport !== 'generic'
              ? data.sub_sport
              : null,
            tr('数据来自 FIT', 'From FIT file'),
          ]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </div>
      {onClose ? (
        <CloseButton onClose={onClose} label={tr('关闭', 'Close')} />
      ) : null}
    </div>
  );
}

function Loaded({
  promise,
  className,
  onClose,
}: {
  promise: Promise<RunSplits | null>;
  className?: string;
  onClose?: () => void;
}) {
  const data = use(promise);
  const tr = useTr();
  if (!data) return null;
  return (
    <div className={`card p-4 ${className ?? ''}`}>
      <Header data={data} onClose={onClose} tr={tr} />
      <AnalysisBody data={data} />
    </div>
  );
}

export function RunAnalysis({
  activity,
  className,
  onClose,
}: {
  activity: Activity;
  className?: string;
  onClose?: () => void;
}) {
  const promise = loadSplits(activity.run_id);
  return (
    <Suspense
      fallback={<AnalysisSkeleton className={className} onClose={onClose} />}
    >
      <Loaded
        key={activity.run_id}
        promise={promise}
        className={className}
        onClose={onClose}
      />
    </Suspense>
  );
}

function LauncherButton({
  activity,
  index,
  onOpen,
}: {
  activity: Activity;
  index: Promise<Set<number>>;
  onOpen: () => void;
}) {
  const ids = use(index);
  const tr = useTr();
  if (!ids.has(activity.run_id)) return null;
  return (
    <button
      type="button"
      onClick={onOpen}
      style={{ bottom: 'calc(0.75rem + env(safe-area-inset-bottom, 0px))' }}
      className="fixed right-4 z-50 flex cursor-pointer items-center gap-2 rounded-full bg-[var(--color-run)] px-4 py-2 text-sm font-medium text-white shadow-lg transition-transform hover:scale-[1.03] sm:right-auto sm:left-1/2 sm:-translate-x-1/2"
    >
      <svg
        className="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 3v18h18M7 15l4-4 3 3 5-6"
        />
      </svg>
      {tr('分段分析', 'Splits')} · {(activity.distance / 1000).toFixed(1)} km
    </button>
  );
}

function Sheet({
  activity,
  onClose,
}: {
  activity: Activity;
  onClose: () => void;
}) {
  const [phase, setPhase] = useState<'enter' | 'open' | 'leave'>('enter');
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPhase('leave');
    };
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKey);
    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => {
        setPhase((p) => (p === 'enter' ? 'open' : p));
      });
    });
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, []);

  useEffect(() => {
    if (phase !== 'leave') return;
    const t = window.setTimeout(() => onCloseRef.current(), SHEET_MS);
    return () => window.clearTimeout(t);
  }, [phase]);

  const visible = phase === 'open';
  const requestClose = () => setPhase('leave');

  return (
    <div
      className={`fixed inset-0 z-[60] flex items-end justify-center bg-black/40 backdrop-blur-[2px] transition-opacity ease-out md:items-center md:p-6 ${
        visible ? 'opacity-100' : 'opacity-0'
      }`}
      style={{ transitionDuration: `${SHEET_MS}ms` }}
      onClick={requestClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        className={`flex max-h-[90vh] w-full origin-bottom flex-col overflow-hidden rounded-t-2xl bg-[var(--color-card)] transition-[opacity,transform] ease-out md:max-w-2xl md:origin-center md:rounded-2xl ${
          visible
            ? 'translate-y-0 scale-100 opacity-100'
            : 'translate-y-6 scale-[0.98] opacity-0 md:translate-y-2'
        }`}
        style={{ transitionDuration: `${SHEET_MS}ms` }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <RunAnalysis
            activity={activity}
            onClose={requestClose}
            className="[--card-radius:0]"
          />
        </div>
      </div>
    </div>
  );
}

export function RunAnalysisLauncher({
  activity,
}: {
  activity: Activity | null;
}) {
  const [openId, setOpenId] = useState<number | null>(null);
  if (!activity) return null;
  const open = openId === activity.run_id;
  return (
    <Suspense fallback={null}>
      {open ? (
        <Sheet activity={activity} onClose={() => setOpenId(null)} />
      ) : (
        <LauncherButton
          activity={activity}
          index={loadSplitsIndex()}
          onOpen={() => setOpenId(activity.run_id)}
        />
      )}
    </Suspense>
  );
}
