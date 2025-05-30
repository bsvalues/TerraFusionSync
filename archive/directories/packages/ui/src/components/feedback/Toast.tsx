import React, { useEffect, useState } from 'react';
import { cn } from '../../utils/cn';

export type ToastVariant = 'info' | 'success' | 'warning' | 'error';
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

export interface ToastProps {
  /**
   * Unique identifier for the toast
   */
  id: string;
  
  /**
   * Message content to display
   */
  message: string;
  
  /**
   * Optional title for the toast
   */
  title?: string;
  
  /**
   * Visual variant of the toast
   * @default 'info'
   */
  variant?: ToastVariant;
  
  /**
   * Duration in milliseconds before auto-closing
   * Set to 0 or null to prevent auto-closing
   * @default 5000
   */
  duration?: number | null;
  
  /**
   * Whether the toast can be manually dismissed
   * @default true
   */
  dismissible?: boolean;
  
  /**
   * Function to call when toast is dismissed
   */
  onDismiss?: (id: string) => void;
  
  /**
   * Function to call when toast is clicked
   */
  onClick?: (id: string) => void;
  
  /**
   * Optional action button config
   */
  action?: {
    label: string;
    onClick: (id: string) => void;
  };
  
  /**
   * Additional class name to apply
   */
  className?: string;
}

/**
 * Toast notification component for transient user feedback
 */
export const Toast: React.FC<ToastProps> = ({
  id,
  message,
  title,
  variant = 'info',
  duration = 5000,
  dismissible = true,
  onDismiss,
  onClick,
  action,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  
  // Handle dismissal
  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss(id);
    }
  };
  
  // Handle click on toast body
  const handleClick = () => {
    if (onClick) {
      onClick(id);
    }
  };
  
  // Handle action button click
  const handleActionClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (action?.onClick) {
      action.onClick(id);
    }
  };
  
  // Auto-dismiss timer
  useEffect(() => {
    if (!duration || isPaused) return;
    
    const startTime = Date.now();
    const endTime = startTime + duration;
    let animationFrame: number;
    
    const updateProgress = () => {
      const now = Date.now();
      const remaining = Math.max(0, endTime - now);
      const newProgress = 100 - (remaining / duration) * 100;
      
      setProgress(newProgress);
      
      if (remaining > 0) {
        animationFrame = requestAnimationFrame(updateProgress);
      } else {
        handleDismiss();
      }
    };
    
    animationFrame = requestAnimationFrame(updateProgress);
    
    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [duration, isPaused]);
  
  // Base styles
  const baseStyles = 'relative flex w-full max-w-sm overflow-hidden rounded-lg shadow-lg';
  
  // Variant styles
  const variantStyles = {
    info: 'bg-secondary-50 text-secondary-900 border-l-4 border-secondary-500',
    success: 'bg-success-50 text-success-900 border-l-4 border-success-500',
    warning: 'bg-warning-50 text-warning-900 border-l-4 border-warning-500',
    error: 'bg-error-50 text-error-900 border-l-4 border-error-500',
  };
  
  // Icon based on variant
  const ToastIcon = () => {
    switch (variant) {
      case 'info':
        return (
          <svg className="h-5 w-5 text-secondary-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case 'success':
        return (
          <svg className="h-5 w-5 text-success-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-5 w-5 text-warning-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-5 w-5 text-error-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };
  
  // Animation classes
  const animationClasses = isVisible
    ? 'animate-fade-in'
    : 'animate-fade-out pointer-events-none';
  
  if (!isVisible) return null;
  
  return (
    <div
      className={cn(
        baseStyles,
        variantStyles[variant],
        animationClasses,
        className
      )}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      onClick={handleClick}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Progress bar */}
      {duration && duration > 0 && (
        <div 
          className="absolute bottom-0 left-0 h-1 bg-current opacity-20"
          style={{ width: `${progress}%` }}
        />
      )}
      
      <div className="flex-shrink-0 flex items-center justify-center w-12 pt-3 pl-3">
        <ToastIcon />
      </div>
      
      <div className="p-3 w-full">
        {title && (
          <div className="font-medium">{title}</div>
        )}
        <div className="text-sm">
          {message}
        </div>
        
        {action && (
          <div className="mt-2">
            <button
              type="button"
              className={cn(
                'text-sm font-medium',
                variant === 'info' && 'text-secondary-700 hover:text-secondary-900',
                variant === 'success' && 'text-success-700 hover:text-success-900',
                variant === 'warning' && 'text-warning-700 hover:text-warning-900',
                variant === 'error' && 'text-error-700 hover:text-error-900'
              )}
              onClick={handleActionClick}
            >
              {action.label}
            </button>
          </div>
        )}
      </div>
      
      {dismissible && (
        <button
          type="button"
          className="absolute top-1 right-1 p-1 rounded-full inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500"
          onClick={(e) => {
            e.stopPropagation();
            handleDismiss();
          }}
          aria-label="Close"
        >
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

// Toast container for positioning
export interface ToastContainerProps {
  position?: ToastPosition;
  className?: string;
  children: React.ReactNode;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  position = 'top-right',
  className,
  children,
}) => {
  // Position styles
  const positionStyles = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'top-center': 'top-0 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-0 left-1/2 transform -translate-x-1/2',
  };
  
  return (
    <div
      className={cn(
        'fixed z-50 p-4 flex flex-col gap-3 pointer-events-none max-h-screen overflow-hidden',
        positionStyles[position],
        className
      )}
    >
      {children}
    </div>
  );
};

export default Toast;