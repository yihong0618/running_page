import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import type { RouteMapProps } from './RouteMapCanvas';
import { useLocale } from '../hooks/useLocale';

const MapCanvas = lazy(() =>
  import('./RouteMapCanvas').then((module) => ({
    default: module.RouteMapCanvas,
  }))
);

/** Load WebGL and decode routes only as the map approaches the viewport. */
export function RouteMap(props: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const { locale } = useLocale();
  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '200px' }
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const placeholder = (
    <div
      className="flex h-[442px] items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-muted)]"
      role="status"
    >
      {locale === 'zh' ? '正在加载地图…' : 'Loading map…'}
    </div>
  );
  return (
    <div ref={containerRef}>
      <Suspense fallback={placeholder}>
        {visible || props.selectedActivity ? (
          <MapCanvas {...props} />
        ) : (
          placeholder
        )}
      </Suspense>
    </div>
  );
}
