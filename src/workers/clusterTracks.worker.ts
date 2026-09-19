import * as polyline from '@mapbox/polyline';

interface Track {
  summary_polyline: string;
  start_date_local: string;
  distance: number;
}

self.onmessage = ({ data }: MessageEvent<Track[]>) => {
  // Keep original indices so the page can resolve each representative activity.
  const tracks = data
    .map((track, index) => ({ ...track, index }))
    .sort(
      (a, b) =>
        new Date(b.start_date_local).getTime() -
        new Date(a.start_date_local).getTime()
    );
  const decoded = tracks.map((track) => {
    try {
      const coords = polyline.decode(track.summary_polyline);
      if (coords.length < 2) return null;
      return {
        start: coords[0],
        end: coords[coords.length - 1],
        distBucket: Math.round(track.distance / 2000),
      };
    } catch {
      return null;
    }
  });

  const clusters: { index: number; count: number }[] = [];
  const used = new Set<number>();
  for (let i = 0; i < tracks.length; i++) {
    if (used.has(i)) continue;
    const current = decoded[i];
    if (!current) continue;
    let count = 1;
    for (let j = i + 1; j < tracks.length; j++) {
      if (used.has(j)) continue;
      const candidate = decoded[j];
      if (!candidate || current.distBucket !== candidate.distBucket) continue;
      const startClose =
        Math.abs(current.start[0] - candidate.start[0]) < 0.005 &&
        Math.abs(current.start[1] - candidate.start[1]) < 0.005;
      const endClose =
        Math.abs(current.end[0] - candidate.end[0]) < 0.005 &&
        Math.abs(current.end[1] - candidate.end[1]) < 0.005;
      if (startClose && endClose) {
        used.add(j);
        count++;
      }
    }
    used.add(i);
    clusters.push({ index: tracks[i].index, count });
  }
  self.postMessage(clusters);
};
