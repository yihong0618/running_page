import React from 'react';
import usePageTracking from '../hooks/usePageTracking';
import { USE_GOOGLE_ANALYTICS } from './analytics';

const TrackPageRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  usePageTracking();
  return <>{children}</>;
};

export const withOptionalGAPageTracking = (element: React.ReactElement) => {
  if (USE_GOOGLE_ANALYTICS) {
    return <TrackPageRoute>{element}</TrackPageRoute>;
  }
  return element;
};
