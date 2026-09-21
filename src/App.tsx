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

// 主题注册表 — 新增主题时在此处注册，并在 src/themes/ 下创建对应文件夹
const themes: Record<string, LazyExoticComponent<ComponentType>> = {
  dashboard: lazy(() => import('./themes/dashboard')),
  classic: lazy(() => import('./themes/classic')),
  // 在此处添加自定义主题，例如：
  // 'my-theme': lazy(() => import('./themes/my-theme')),
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
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
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
