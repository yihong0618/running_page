import {
  lazy,
  type LazyExoticComponent,
  type ComponentType,
  Suspense,
} from 'react';
import { LocaleProvider } from './hooks/useLocale';
import { THEME_PRESET } from './config';
import { ErrorBoundary } from './components/ErrorBoundary';

// 主题注册表 — 新增主题时在此处注册，并在 src/themes/ 下创建对应文件夹
const themes: Record<string, LazyExoticComponent<ComponentType>> = {
  dashboard: lazy(() => import('./themes/dashboard')),
  classic: lazy(() => import('./themes/classic')),
  // 在此处添加自定义主题，例如：
  // 'my-theme': lazy(() => import('./themes/my-theme')),
};

const ThemeComponent = themes[THEME_PRESET] ?? themes['dashboard'];

export default function App() {
  return (
    <LocaleProvider>
      <ErrorBoundary>
        <Suspense
          fallback={
            <div
              className="flex min-h-screen items-center justify-center"
              style={{ backgroundColor: 'var(--color-bg, #0d1117)' }}
            >
              <div
                style={{
                  color: 'var(--color-muted, #8b949e)',
                  fontSize: '0.875rem',
                }}
              >
                Loading...
              </div>
            </div>
          }
        >
          <ThemeComponent />
        </Suspense>
      </ErrorBoundary>
    </LocaleProvider>
  );
}
