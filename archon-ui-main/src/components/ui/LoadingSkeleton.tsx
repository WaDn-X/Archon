import React from 'react';
import { cn } from '../../utils/cn';

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'card' | 'text' | 'avatar' | 'button' | 'input';
  lines?: number;
  animated?: boolean;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className,
  variant = 'text',
  lines = 1,
  animated = true
}) => {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';

  if (animated) {
    baseClasses + ' animate-pulse';
  }

  const getVariantClasses = () => {
    switch (variant) {
      case 'card':
        return 'h-32 w-full rounded-lg';
      case 'avatar':
        return 'h-10 w-10 rounded-full';
      case 'button':
        return 'h-10 w-24 rounded-md';
      case 'input':
        return 'h-10 w-full rounded-md';
      case 'text':
      default:
        if (lines === 1) {
          return 'h-4 w-3/4 rounded';
        }
        return 'h-4 w-full rounded';
    }
  };

  if (lines > 1) {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className={cn(
              baseClasses,
              getVariantClasses(),
              i === lines - 1 ? 'w-2/3' : 'w-full' // Last line shorter
            )}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn(baseClasses, getVariantClasses(), className)} />
  );
};

// Pre-built skeleton components for common use cases
export const CardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-3', className)}>
    <LoadingSkeleton variant="text" className="w-3/4" />
    <LoadingSkeleton variant="text" lines={2} />
    <div className="flex justify-between items-center">
      <LoadingSkeleton variant="button" className="w-16" />
      <LoadingSkeleton variant="avatar" />
    </div>
  </div>
);

export const KnowledgeItemSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-3', className)}>
    <div className="flex items-start space-x-3">
      <LoadingSkeleton variant="avatar" className="flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <LoadingSkeleton variant="text" className="w-1/3" />
        <LoadingSkeleton variant="text" lines={2} />
        <LoadingSkeleton variant="text" className="w-1/2" />
      </div>
    </div>
  </div>
);

export const ProjectCardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-4', className)}>
    <LoadingSkeleton variant="text" className="w-1/2" />
    <LoadingSkeleton variant="text" lines={2} />
    <div className="flex justify-between items-center">
      <LoadingSkeleton variant="button" className="w-20" />
      <div className="flex space-x-2">
        <LoadingSkeleton variant="avatar" className="w-6 h-6" />
        <LoadingSkeleton variant="avatar" className="w-6 h-6" />
      </div>
    </div>
  </div>
);

export const TaskListSkeleton: React.FC<{ className?: string; items?: number }> = ({
  className,
  items = 5
}) => (
  <div className={cn('space-y-2', className)}>
    {Array.from({ length: items }, (_, i) => (
      <div key={i} className="flex items-center space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
        <LoadingSkeleton variant="avatar" className="w-8 h-8" />
        <div className="flex-1 space-y-1">
          <LoadingSkeleton variant="text" className="w-1/3" />
          <LoadingSkeleton variant="text" className="w-1/2" />
        </div>
        <LoadingSkeleton variant="button" className="w-16" />
      </div>
    ))}
  </div>
);
