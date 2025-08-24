import { useState, useRef } from 'react';

type HoverHook = [boolean, { onMouseOver: () => void; onMouseOut: () => void }];

const useHover = (): HoverHook => {
  const [hovered, setHovered] = useState(false);
  const timerRef = useRef<number | undefined>(undefined);

  const eventHandlers = {
    onMouseOver() {
      // Clear the previous timer if it exists to handle rapid mouse movements
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = window.setTimeout(() => setHovered(true), 1000);
    },
    onMouseOut() {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      setHovered(false);
    },
  };

  return [hovered, eventHandlers];
};

export default useHover;
