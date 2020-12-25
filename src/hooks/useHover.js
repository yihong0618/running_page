import { useState } from 'react';

const useHover = () => {
  const [hovered, setHovered] = useState();
  const [timer, setTimer] = useState();

  const eventHandlers = {
    onMouseOver() {
      setTimer(setTimeout(() => setHovered(true), 700));
    },
    onMouseOut() {
      clearTimeout(timer);
      setHovered(false);
    },
  };

  return [hovered, eventHandlers];
};

export default useHover;
