export const USE_GOOGLE_ANALYTICS = false;
export const GOOGLE_ANALYTICS_TRACKING_ID = '';

type ReactGAInstance = (typeof import('react-ga4'))['default'];

let googleAnalyticsPromise: Promise<ReactGAInstance> | undefined;

export const initializeGoogleAnalytics = (): Promise<ReactGAInstance> => {
  googleAnalyticsPromise ??= import('react-ga4').then(
    ({ default: ReactGA }) => {
      ReactGA.initialize(GOOGLE_ANALYTICS_TRACKING_ID);
      return ReactGA;
    }
  );
  return googleAnalyticsPromise;
};

export const sendGooglePageView = (page: string) => {
  if (!USE_GOOGLE_ANALYTICS) return;

  void initializeGoogleAnalytics().then((ReactGA) => {
    if (!ReactGA.isInitialized) return;

    ReactGA.send({
      hitType: 'pageview',
      page,
    });
  });
};
