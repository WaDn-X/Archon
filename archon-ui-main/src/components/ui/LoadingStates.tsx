import React from 'react';
import { LoadingSkeleton } from './LoadingSkeleton';
import { Card } from './Card';

interface LoadingStateProps {
  type: 'page' | 'section' | 'card' | 'list' | 'form';
  message?: string;
  showProgress?: boolean;
  progress?: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  type,
  message = 'Loading...',
  showProgress = false,
  progress = 0
}) => {
  const renderLoadingContent = () => {
    switch (type) {
      case 'page':
        return (
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
            <div className="max-w-4xl mx-auto space-y-6">
              <LoadingSkeleton variant="text" className="w-1/3 h-8" />
              <Card>
                <div className="p-6 space-y-4">
                  <LoadingSkeleton variant="text" className="w-1/2" />
                  <LoadingSkeleton variant="text" lines={3} />
                  <LoadingSkeleton variant="button" />
                </div>
              </Card>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <LoadingSkeleton variant="card" />
                </Card>
                <Card>
                  <LoadingSkeleton variant="card" />
                </Card>
              </div>
            </div>
          </div>
        );

      case 'section':
        return (
          <div className="space-y-4 p-6">
            <LoadingSkeleton variant="text" className="w-1/4 h-6" />
            <LoadingSkeleton variant="text" lines={2} />
            <LoadingSkeleton variant="button" className="w-32" />
          </div>
        );

      case 'card':
        return (
          <Card>
            <div className="p-6 space-y-4">
              <LoadingSkeleton variant="text" className="w-1/3" />
              <LoadingSkeleton variant="text" lines={2} />
              <LoadingSkeleton variant="avatar" />
            </div>
          </Card>
        );

      case 'list':
        return (
          <div className="space-y-3">
            {Array.from({ length: 5 }, (_, i) => (
              <LoadingSkeleton key={i} variant="card" className="h-16" />
            ))}
          </div>
        );

      case 'form':
        return (
          <div className="space-y-4 max-w-md">
            <LoadingSkeleton variant="input" />
            <LoadingSkeleton variant="input" />
            <LoadingSkeleton variant="button" />
          </div>
        );

      default:
        return <LoadingSkeleton variant="text" />;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      {renderLoadingContent()}
      {message && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
          {showProgress && (
            <div className="mt-2 w-64 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Specialized loading states for common use cases
export const PageLoadingState: React.FC<{ message?: string }> = ({ message }) => (
  <LoadingState type="page" message={message} />
);

export const SectionLoadingState: React.FC<{ message?: string }> = ({ message }) => (
  <LoadingState type="section" message={message} />
);

export const CardLoadingState: React.FC<{ message?: string }> = ({ message }) => (
  <LoadingState type="card" message={message} />
);

export const ListLoadingState: React.FC<{ message?: string }> = ({ message }) => (
  <LoadingState type="list" message={message} />
);

export const FormLoadingState: React.FC<{ message?: string }> = ({ message }) => (
  <LoadingState type="form" message={message} />
);

export const ProgressLoadingState: React.FC<{ progress: number; message?: string }> = ({ progress, message }) => (
  <LoadingState type="section" message={message} showProgress progress={progress} />
);
