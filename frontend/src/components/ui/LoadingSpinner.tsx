import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  progress?: number;
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

const LoadingSpinner: React.FC<LoadingSpinnerProps> = React.memo(({
  size = 'md',
  message,
  progress,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`} role="status" aria-live="polite">
      <div className="relative">
        <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      </div>
      {message && (
        <p className="text-sm text-gray-600 text-center max-w-xs">{message}</p>
      )}
      {typeof progress === 'number' && (
        <div className="w-48 bg-gray-200 rounded-full h-1.5">
          <div 
            className="bg-blue-600 h-1.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      )}
      <span className="sr-only">載入中...</span>
    </div>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';

export default LoadingSpinner;