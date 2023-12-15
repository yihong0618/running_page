import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import Index from './pages';
import NotFound from './pages/404';
import ReactGA from 'react-ga4';
import { GOOGLE_ANALYTICS_TRACKING_ID } from './utils/const';
import '@/styles/index.scss';
import usePageTracking from './hooks/usePageTracking';

ReactGA.initialize(GOOGLE_ANALYTICS_TRACKING_ID);

interface TrackPageRouteProps {
  children: React.ReactNode;
}

const TrackPageRoute = ({ children }: TrackPageRouteProps) => {
  usePageTracking();
  return <>{children}</>;
};

const routes = createBrowserRouter(
  [
    {
      path: '/',
      element: (
        <TrackPageRoute>
          <Index />
        </TrackPageRoute>
      ),
    },
    {
      path: '*',
      element: (
        <TrackPageRoute>
          <NotFound />
        </TrackPageRoute>
      ),
    },
  ],
  { basename: import.meta.env.BASE_URL }
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HelmetProvider>
      <RouterProvider router={routes} />
    </HelmetProvider>
  </React.StrictMode>
);
