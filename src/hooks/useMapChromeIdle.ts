import { useEffect } from 'react';

/** Hide business map controls after this many ms without interaction. */
export const MAP_CHROME_IDLE_MS = 3000;

/**
 * Toggle `.is-chrome-idle` on a map root after inactivity.
 * Works in fullscreen when the fullscreen element is (or is inside) `root`.
 * CSS must not hide Mapbox logo / AttributionControl (ToS).
 */
export function useMapChromeIdle(
  root: HTMLElement | null,
  enabled = true
): void {
  useEffect(() => {
    if (!root || !enabled) {
      root?.classList.remove('is-chrome-idle');
      return;
    }

    let timer: ReturnType<typeof setTimeout> | null = null;
    let lastMoveAt = 0;

    const scheduleIdle = () => {
      if (timer != null) clearTimeout(timer);
      timer = setTimeout(() => {
        root.classList.add('is-chrome-idle');
      }, MAP_CHROME_IDLE_MS);
    };

    const reveal = () => {
      root.classList.remove('is-chrome-idle');
      scheduleIdle();
    };

    const onMove = () => {
      const now = performance.now();
      if (now - lastMoveAt < 400) return;
      lastMoveAt = now;
      reveal();
    };

    reveal();

    root.addEventListener('pointerdown', reveal);
    root.addEventListener('pointermove', onMove);
    root.addEventListener('wheel', reveal, { passive: true });
    root.addEventListener('keydown', reveal);

    const onFsChange = () => {
      // Entering/leaving fullscreen counts as activity; restart idle clock.
      reveal();
    };
    document.addEventListener('fullscreenchange', onFsChange);
    document.addEventListener(
      'webkitfullscreenchange' as 'fullscreenchange',
      onFsChange
    );

    return () => {
      if (timer != null) clearTimeout(timer);
      root.classList.remove('is-chrome-idle');
      root.removeEventListener('pointerdown', reveal);
      root.removeEventListener('pointermove', onMove);
      root.removeEventListener('wheel', reveal);
      root.removeEventListener('keydown', reveal);
      document.removeEventListener('fullscreenchange', onFsChange);
      document.removeEventListener(
        'webkitfullscreenchange' as 'fullscreenchange',
        onFsChange
      );
    };
  }, [root, enabled]);
}
