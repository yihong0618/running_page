import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import ReactGA from 'react-ga4';

const usePageTracking = () => {
  const location = useLocation();
  useEffect(() => {
    console.log(location.pathname + location.search);
    console.log(window.location.href + window.location.search);
    ReactGA.send({
      hitType: 'pageview',
      page: location.pathname + location.search,
    });
  }, [location]);
};

export default usePageTracking;
