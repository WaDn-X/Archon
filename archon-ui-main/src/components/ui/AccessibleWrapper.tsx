import React, { useRef, useEffect } from 'react';
import { useAccessibility } from '../../hooks/useAccessibility';
import { cn } from '../../utils/cn';

interface AccessibleWrapperProps {
  children: React.ReactNode;
  label?: string;
  description?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  role?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  focusable?: boolean;
  skipLinkTarget?: string;
  announceOnMount?: string;
  announceOnUpdate?: string;
  className?: string;
  onFocus?: (event: React.FocusEvent) => void;
  onBlur?: (event: React.BlurEvent) => void;
}

export const AccessibleWrapper: React.FC<AccessibleWrapperProps> = ({
  children,
  label,
  description,
  error,
  required,
  disabled,
  role,
  ariaLabel,
  ariaDescribedBy,
  focusable = true,
  skipLinkTarget,
  announceOnMount,
  announceOnUpdate,
  className,
  onFocus,
  onBlur,
  ...props
}) => {
  const { announceToScreenReader, useUniqueId, useSkipLink } = useAccessibility();
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Generate unique IDs
  const labelId = useUniqueId('label');
  const descriptionId = useUniqueId('description');
  const errorId = useUniqueId('error');

  // Combine aria-describedby IDs
  const describedByIds = [
    description ? descriptionId : '',
    error ? errorId : '',
    ariaDescribedBy || ''
  ].filter(Boolean).join(' ');

  // Handle skip link
  const handleSkipLink = skipLinkTarget ? useSkipLink(skipLinkTarget) : undefined;

  // Announce content changes
  useEffect(() => {
    if (announceOnMount) {
      announceToScreenReader(announceOnMount);
    }
  }, [announceOnMount, announceToScreenReader]);

  useEffect(() => {
    if (announceOnUpdate) {
      announceToScreenReader(announceOnUpdate);
    }
  }, [announceOnUpdate, announceToScreenReader]);

  const handleFocus = (event: React.FocusEvent) => {
    onFocus?.(event);
  };

  const handleBlur = (event: React.BlurEvent) => {
    onBlur?.(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (skipLinkTarget && event.key === 'Enter') {
      handleSkipLink?.(event);
    }
  };

  return (
    <div
      ref={wrapperRef}
      className={cn('accessible-wrapper', className)}
      role={role}
      aria-label={ariaLabel}
      aria-describedby={describedByIds || undefined}
      aria-disabled={disabled}
      tabIndex={focusable && !disabled ? 0 : -1}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
      {...props}
    >
      {/* Skip Link */}
      {skipLinkTarget && (
        <a
          href={`#${skipLinkTarget}`}
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50"
          onClick={handleSkipLink}
        >
          Skip to {skipLinkTarget}
        </a>
      )}

      {/* Label */}
      {label && (
        <label
          id={labelId}
          className="block text-sm font-medium text-foreground mb-2"
        >
          {label}
          {required && (
            <span className="text-destructive ml-1" aria-label="required">
              *
            </span>
          )}
        </label>
      )}

      {/* Main Content */}
      <div
        className="accessible-content"
        aria-labelledby={label ? labelId : undefined}
        aria-describedby={describedByIds || undefined}
      >
        {children}
      </div>

      {/* Description */}
      {description && (
        <div
          id={descriptionId}
          className="mt-2 text-sm text-muted-foreground"
        >
          {description}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div
          id={errorId}
          className="mt-2 text-sm text-destructive"
          role="alert"
          aria-live="polite"
        >
          {error}
        </div>
      )}
    </div>
  );
};

// Screen Reader Only Text Component
export const ScreenReaderOnly: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => (
  <span className={cn('sr-only', className)}>
    {children}
  </span>
);

// Focus Trap Component
interface FocusTrapProps {
  children: React.ReactNode;
  className?: string;
  autoFocus?: boolean;
  restoreFocus?: boolean;
  onEscape?: () => void;
}

export const FocusTrap: React.FC<FocusTrapProps> = ({
  children,
  className,
  autoFocus = true,
  restoreFocus = true,
  onEscape,
}) => {
  const { useFocusTrap, useUniqueId } = useAccessibility();
  const containerRef = useRef<HTMLDivElement>(null);
  const initialFocusRef = useRef<HTMLDivElement>(null);

  const trapId = useUniqueId('focus-trap');

  useFocusTrap(containerRef, {
    initialFocusRef: autoFocus ? initialFocusRef : undefined,
    restoreFocus,
  });

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape' && onEscape) {
      onEscape();
    }
  };

  return (
    <div
      ref={containerRef}
      id={trapId}
      className={cn('focus-trap', className)}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      {autoFocus && (
        <div ref={initialFocusRef} tabIndex={-1} aria-hidden="true" />
      )}
      {children}
    </div>
  );
};

// High Contrast Mode Detector
export const useHighContrast = () => {
  const [isHighContrast, setIsHighContrast] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setIsHighContrast(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setIsHighContrast(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return isHighContrast;
};

// Reduced Motion Detector
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};
