import {
  lazy,
  Suspense,
  type ComponentType,
  type LazyExoticComponent,
} from 'react';
import { LocaleProvider, useLocale } from './hooks/useLocale';
import { THEME_PRESET } from './config';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ThemeProvider } from './core/theme';

const themes: Record<string, LazyExoticComponent<ComponentType>> = {
  dashboard: lazy(() => import('./themes/dashboard')),
  classic: lazy(() => import('./themes/classic')),
};

const ThemeComponent = themes[THEME_PRESET] ?? themes.dashboard;

function AppLoading() {
  const { t } = useLocale();
  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#8b949e',
        fontSize: '0.875rem',
      }}
    >
      {t('loading')}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LocaleProvider>
        <ErrorBoundary>
          <Suspense fallback={<AppLoading />}>
            <ThemeComponent />
          </Suspense>
        </ErrorBoundary>
      </LocaleProvider>
    </ThemeProvider>
  );
}
