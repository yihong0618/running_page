import { Component, type ErrorInfo, type ReactNode } from 'react';
import { resetActivityData } from '../hooks/useActivities';

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  message: string;
}

/**
 * Catches render-time errors thrown by descendants (e.g. the Suspense data
 * source throwing a fetch error instead of a promise) so a failed
 * activities.json load degrades gracefully instead of blanking the page.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: unknown, _info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error);
  }

  private handleRetry = () => {
    resetActivityData();
    this.setState({ hasError: false, message: '' });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex min-h-screen flex-col items-center justify-center gap-3"
          style={{
            backgroundColor: 'var(--color-bg, #0d1117)',
            color: 'var(--color-muted, #8b949e)',
          }}
        >
          <p
            className="text-base font-medium"
            style={{ color: 'var(--color-text, #e6edf3)' }}
          >
            Failed to load activities
          </p>
          <p className="text-xs">{this.state.message}</p>
          <button
            type="button"
            onClick={this.handleRetry}
            className="mt-1 rounded-md px-4 py-1.5 text-sm font-medium text-white"
            style={{ backgroundColor: 'var(--color-accent, #a855f7)' }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
