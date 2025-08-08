import React from 'react';
import { pathForRun, Activity } from '@/utils/utils';
import styles from './style.module.css';

interface RoutePreviewProps {
  activities: Activity[];
  className?: string;
}

const RoutePreview: React.FC<RoutePreviewProps> = ({
  activities,
  className,
}) => {
  // Filter activities that have polyline data
  const activitiesWithRoutes = activities.filter(
    (activity) => activity.summary_polyline
  );

  if (activitiesWithRoutes.length === 0) {
    return (
      <div className={`${styles.routePreview} ${className || ''}`}>
        <div className={styles.noRoute}>暂无路线数据</div>
      </div>
    );
  }

  // Get all route coordinates
  const allCoordinates: Array<{ path: [number, number][]; color: string }> =
    activitiesWithRoutes.map((activity, index) => {
      const path = pathForRun(activity);
      // Use different colors for multiple routes
      const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'];
      const color = colors[index % colors.length];
      return { path, color };
    });

  // Calculate bounding box for all routes
  const allPoints = allCoordinates.flatMap((route) => route.path);
  if (allPoints.length === 0) {
    return (
      <div className={`${styles.routePreview} ${className || ''}`}>
        <div className={styles.noRoute}>路线数据无效</div>
      </div>
    );
  }

  const lats = allPoints.map((point) => point[1]);
  const lngs = allPoints.map((point) => point[0]);

  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  // Add padding to bounds
  const padding = 0.001;
  const bounds = {
    minLat: minLat - padding,
    maxLat: maxLat + padding,
    minLng: minLng - padding,
    maxLng: maxLng + padding,
  };

  const boundsWidth = bounds.maxLng - bounds.minLng;
  const boundsHeight = bounds.maxLat - bounds.minLat;

  // SVG dimensions
  const svgWidth = 250;
  const svgHeight = 150;
  const svgPadding = 10;
  const drawWidth = svgWidth - 2 * svgPadding;
  const drawHeight = svgHeight - 2 * svgPadding;

  // Convert coordinate to SVG coordinate
  const coordToSvg = (lng: number, lat: number): [number, number] => {
    const x = svgPadding + ((lng - bounds.minLng) / boundsWidth) * drawWidth;
    const y = svgPadding + ((bounds.maxLat - lat) / boundsHeight) * drawHeight;
    return [x, y];
  };

  return (
    <div className={`${styles.routePreview} ${className || ''}`}>
      <svg width={svgWidth} height={svgHeight} className={styles.routeSvg}>
        {/* Background */}
        <rect
          width={svgWidth}
          height={svgHeight}
          fill="var(--color-activity-card)"
        />

        {/* Routes */}
        {allCoordinates.map((route, routeIndex) => {
          if (route.path.length < 2) return null;

          const pathString = route.path
            .map((coord, index) => {
              const [x, y] = coordToSvg(coord[0], coord[1]);
              return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
            })
            .join(' ');

          return (
            <g key={routeIndex}>
              {/* Route line */}
              <path
                d={pathString}
                fill="none"
                stroke={route.color}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.8"
              />

              {/* Start point */}
              {route.path.length > 0 && (
                <circle
                  cx={coordToSvg(route.path[0][0], route.path[0][1])[0]}
                  cy={coordToSvg(route.path[0][0], route.path[0][1])[1]}
                  r="3"
                  fill="#2ecc71"
                  stroke="white"
                  strokeWidth="1"
                />
              )}

              {/* End point */}
              {route.path.length > 1 && (
                <circle
                  cx={
                    coordToSvg(
                      route.path[route.path.length - 1][0],
                      route.path[route.path.length - 1][1]
                    )[0]
                  }
                  cy={
                    coordToSvg(
                      route.path[route.path.length - 1][0],
                      route.path[route.path.length - 1][1]
                    )[1]
                  }
                  r="3"
                  fill="#e74c3c"
                  stroke="white"
                  strokeWidth="1"
                />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default RoutePreview;
