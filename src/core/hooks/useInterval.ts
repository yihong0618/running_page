import { useEffect, useRef } from 'react';

export function useInterval(
  callback: () => void,
  delay: number | null | undefined
) {
  const savedCallbackRef = useRef(callback);

  useEffect(() => {
    savedCallbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay == null) return;
    const id = setInterval(() => savedCallbackRef.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
