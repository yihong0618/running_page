import { useEffect, useRef, useState, type RefObject } from 'react';

const MOBILE_MQ = '(max-width: 1023px)';

export type MapDockFrame = {
  left: number;
  width: number;
  height: number;
};

/**
 * Mobile: when the map slot leaves the viewport, collapse the in-flow height
 * (no blank hole) and offer a FAB to re-show the map as a fixed panel.
 * Desktop (lg+): inactive ? caller keeps normal layout.
 *
 * Pass a slot RefObject from the caller (do not return it) so render logic is
 * not flagged by react-hooks/refs.
 */
export function useMobileMapDock(
  enabled: boolean,
  slotRef: RefObject<HTMLDivElement | null>
) {
  const [isMobile, setIsMobile] = useState(false);
  const [outOfView, setOutOfView] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [frame, setFrame] = useState<MapDockFrame | null>(null);
  const lastHeightRef = useRef(280);

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_MQ);
    const sync = () => setIsMobile(mq.matches);
    sync();
    mq.addEventListener('change', sync);
    return () => mq.removeEventListener('change', sync);
  }, []);

  const active = enabled && isMobile;

  useEffect(() => {
    if (!active) {
      setOutOfView(false);
      setExpanded(false);
      return;
    }
    const slot = slotRef.current;
    if (!slot) return;

    const readFrame = () => {
      const rect = slot.getBoundingClientRect();
      if (rect.width > 1) {
        const height = rect.height > 1 ? rect.height : lastHeightRef.current;
        if (rect.height > 1) lastHeightRef.current = rect.height;
        setFrame({
          left: rect.left,
          width: rect.width,
          height,
        });
      }
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) readFrame();
        setOutOfView(!entry.isIntersecting);
        if (entry.isIntersecting) setExpanded(false);
      },
      // Match sticky top-16 offset so under-header counts as leaving.
      { rootMargin: '-64px 0px 0px 0px', threshold: 0 }
    );
    observer.observe(slot);
    readFrame();
    return () => observer.disconnect();
  }, [active, slotRef]);

  useEffect(() => {
    if (!active || !outOfView) return;
    const onResize = () => {
      const slot = slotRef.current;
      if (!slot) return;
      const rect = slot.getBoundingClientRect();
      if (rect.width > 1) {
        setFrame({
          left: rect.left,
          width: rect.width,
          height: lastHeightRef.current,
        });
      }
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [active, outOfView, slotRef]);

  // Collapse in-flow height whenever out of view (even while FAB-expanded)
  // so the fixed panel does not leave a blank reserved hole.
  const collapsed = active && outOfView;
  const pinned = active && outOfView && expanded && frame != null;
  const showFab = active && outOfView;

  return {
    collapsed,
    pinned,
    frame,
    expanded,
    showFab,
    expand: () => setExpanded(true),
    collapse: () => setExpanded(false),
    toggle: () => setExpanded((v) => !v),
  };
}
