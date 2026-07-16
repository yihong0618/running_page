import { Coordinate } from './utils';

// Haversine distance calculation in meters
export const haversine = (a: Coordinate, b: Coordinate): number => {
  const toRad = (x: number) => (x * Math.PI) / 180;
  const R = 6371000; // meters
  const dLat = toRad(b[1] - a[1]);
  const dLon = toRad(b[0] - a[0]);
  const lat1 = toRad(a[1]);
  const lat2 = toRad(b[1]);
  const sinDLat = Math.sin(dLat / 2);
  const sinDLon = Math.sin(dLon / 2);
  const v =
    sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLon * sinDLon;
  const c = 2 * Math.atan2(Math.sqrt(v), Math.sqrt(1 - v));
  return R * c;
};

// Simplify route points to reduce computation for long routes
export const simplifyRoute = (
  points: Coordinate[],
  minDistance = 5
): Coordinate[] => {
  if (points.length <= 100) {
    return points;
  }

  const simplified = [points[0]];
  let lastIncluded = 0;

  for (let i = 1; i < points.length - 1; i++) {
    const d = haversine(points[lastIncluded], points[i]);
    if (d > minDistance) {
      simplified.push(points[i]);
      lastIncluded = i;
    }
  }

  // Ensure the last point is included
  simplified.push(points[points.length - 1]);
  return simplified;
};

// Calculate segment lengths and cumulative distances
export const calculateSegmentLengths = (
  points: Coordinate[]
): {
  segLens: number[];
  total: number;
  cum: number[];
} => {
  const segLens: number[] = [];
  let total = 0;

  for (let i = 1; i < points.length; i++) {
    const d = haversine(points[i - 1], points[i]);
    segLens.push(d);
    total += d;
  }

  const cum: number[] = [0];
  for (let i = 0; i < segLens.length; i++) {
    cum.push(cum[i] + segLens[i]);
  }

  return { segLens, total, cum };
};

// Binary search to find segment index for target distance
export const findSegmentIdx = (cum: number[], targetDist: number): number => {
  let left = 0;
  let right = cum.length - 2;

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (cum[mid] <= targetDist && targetDist < cum[mid + 1]) {
      return mid;
    } else if (cum[mid] > targetDist) {
      right = mid - 1;
    } else {
      left = mid + 1;
    }
  }

  return Math.max(0, Math.min(cum.length - 2, left));
};

// Calculate visible points for current animation progress
export const calculateVisiblePoints = (
  points: Coordinate[],
  segLens: number[],
  cum: number[],
  targetDist: number
): Coordinate[] => {
  const upTo = findSegmentIdx(cum, targetDist);
  const segStart = points[upTo];
  const segEnd = points[Math.min(upTo + 1, points.length - 1)];
  const segTotal = segLens[upTo] || 1;
  const segT = Math.max(0, Math.min(1, (targetDist - cum[upTo]) / segTotal));

  const visiblePoints: Coordinate[] = [];
  for (let i = 0; i <= upTo; i++) {
    visiblePoints.push(points[i]);
  }

  if (segT > 0 && segT < 1) {
    const lon = segStart[0] + (segEnd[0] - segStart[0]) * segT;
    const lat = segStart[1] + (segEnd[1] - segStart[1]) * segT;
    visiblePoints.push([lon, lat]);
  }

  return visiblePoints;
};

export interface RouteAnimationConfig {
  speedMps?: number;
  minDuration?: number;
  maxDuration?: number;
  targetFps?: number;
  updateThreshold?: number;
  minDistance?: number;
}

export interface RouteAnimationState {
  lastUpTo: number;
  lastT: number;
  frameCount: number;
  lastFrameTime: number;
}

export class RouteAnimator {
  private points: Coordinate[];
  private simplified: Coordinate[];
  private segLens: number[];
  private total: number;
  private cum: number[];
  private duration: number;
  private startTime: number;
  private state: RouteAnimationState;
  private config: Required<RouteAnimationConfig>;
  private animationFrameId: number | null = null;

  constructor(
    points: Coordinate[],
    private onUpdate: (points: Coordinate[]) => void,
    private onComplete: () => void,
    config: RouteAnimationConfig = {}
  ) {
    this.config = {
      speedMps: 4000,
      minDuration: 2500,
      maxDuration: 8000,
      targetFps: 60,
      updateThreshold: 0.01,
      minDistance: 5,
      ...config,
    };

    this.points = points;
    this.simplified = simplifyRoute(points, this.config.minDistance);

    const { segLens, total, cum } = calculateSegmentLengths(this.simplified);
    this.segLens = segLens;
    this.total = total;
    this.cum = cum;

    // Calculate animation duration
    let duration = (this.total / this.config.speedMps) * 1000;
    this.duration = Math.max(
      this.config.minDuration,
      Math.min(this.config.maxDuration, duration)
    );

    this.state = {
      lastUpTo: -1,
      lastT: 0,
      frameCount: 0,
      lastFrameTime: 0,
    };

    this.startTime = performance.now();
  }

  start(): void {
    if (this.total <= 0) {
      this.onUpdate([]);
      this.onComplete();
      return;
    }

    // Start with first point
    this.onUpdate([this.simplified[0]]);
    this.animationFrameId = requestAnimationFrame(this.step.bind(this));
  }

  stop(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  private step(t: number): void {
    const frameInterval = 1000 / this.config.targetFps;

    // Frame rate control
    if (
      t - this.state.lastFrameTime < frameInterval &&
      this.state.frameCount > 0
    ) {
      this.animationFrameId = requestAnimationFrame(this.step.bind(this));
      return;
    }

    this.state.lastFrameTime = t;
    this.state.frameCount++;

    const elapsed = t - this.startTime;
    const p = Math.min(1, elapsed / this.duration);

    // Animation complete
    if (p >= 1) {
      this.onUpdate(this.simplified);
      this.animationFrameId = null;
      this.onComplete();
      return;
    }

    const targetDist = p * this.total;
    const upTo = findSegmentIdx(this.cum, targetDist);

    // Skip update if minimal change
    if (
      upTo === this.state.lastUpTo &&
      Math.abs(p - this.state.lastT) < this.config.updateThreshold &&
      p < 0.98
    ) {
      this.animationFrameId = requestAnimationFrame(this.step.bind(this));
      return;
    }

    this.state.lastUpTo = upTo;
    this.state.lastT = p;

    const visiblePoints = calculateVisiblePoints(
      this.simplified,
      this.segLens,
      this.cum,
      targetDist
    );

    this.onUpdate(visiblePoints);
    this.animationFrameId = requestAnimationFrame(this.step.bind(this));
  }
}
