import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import type { ErrorBoundaryState } from '../../types';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      return <DefaultErrorFallback error={this.state.error!} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4" role="alert">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
        <div className="flex justify-center mb-4">
          <AlertTriangle className="w-16 h-16 text-red-500" />
        </div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">出現錯誤</h1>
        <p className="text-gray-600 mb-4">
          很抱歉，應用程式遇到了未預期的錯誤。請嘗試重新載入頁面。
        </p>
        {process.env.NODE_ENV === 'development' && (
          <details className="text-left mb-4 p-3 bg-gray-100 rounded text-sm">
            <summary className="cursor-pointer font-medium">錯誤詳情</summary>
            <pre className="mt-2 whitespace-pre-wrap">{error.message}</pre>
          </details>
        )}
        <button
          onClick={resetError}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          aria-label="重新載入應用程式"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          重新載入
        </button>
      </div>
    </div>
  );
};

export default ErrorBoundary;