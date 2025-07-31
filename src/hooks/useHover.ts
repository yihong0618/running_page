import { useState, useRef } from 'react';

type HoverHook = [boolean, { onMouseOver: () => void; onMouseOut: () => void }];

const useHover = (): HoverHook => {
  const [hovered, setHovered] = useState(false);
  const timerRef = useRef<number>();

  const eventHandlers = {
    onMouseOver() {
      // Clear the previous timer if it exists to handle rapid mouse movements
      clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => setHovered(true), 1000);
    },
    onMouseOut() {
      clearTimeout(timerRef.current);
      setHovered(false);
    },
  };

  return [hovered, eventHandlers];
};

export default useHover;
