import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { sendGooglePageView } from '../utils/analytics';

const usePageTracking = () => {
  const location = useLocation();
  const page = location.pathname + location.search;

  useEffect(() => {
    sendGooglePageView(page);
  }, [page]);
};

export default usePageTracking;
