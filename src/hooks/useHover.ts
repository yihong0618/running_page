import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type HoverHook = [boolean, { onMouseOver: () => void; onMouseOut: () => void }];

const useHover = (): HoverHook => {
  const [hovered, setHovered] = useState(false);
  const timerRef = useRef<number | undefined>(undefined);

  const clearHoverTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = undefined;
    }
  }, []);

  useEffect(() => clearHoverTimer, [clearHoverTimer]);

  const eventHandlers = useMemo(
    () => ({
      onMouseOver() {
        // Clear the previous timer if it exists to handle rapid mouse movements
        clearHoverTimer();
        timerRef.current = window.setTimeout(() => setHovered(true), 1000);
      },
      onMouseOut() {
        clearHoverTimer();
        setHovered(false);
      },
    }),
    [clearHoverTimer]
  );

  return [hovered, eventHandlers];
};

export default useHover;
