import React from 'react';
import { cn } from '../../utils/cn';

export interface ErrorStateProps {
  /**
   * The main error message to display
   */
  title: string;
  
  /**
   * More detailed explanation of the error
   */
  description?: string;
  
  /**
   * Error code or ID
   */
  errorCode?: string;
  
  /**
   * Specific error details (typically from a catch block)
   */
  error?: Error | unknown;
  
  /**
   * Whether to show technical details (like stack trace) if available
   * @default false
   */
  showTechnicalDetails?: boolean;
  
  /**
   * Whether to show recovery suggestions
   * @default true
   */
  showRecoverySuggestions?: boolean;
  
  /**
   * Custom recovery suggestions
   */
  recoverySuggestions?: string[];
  
  /**
   * User action to retry/reload
   */
  retryAction?: {
    label: string;
    onClick: () => void;
  };
  
  /**
   * Secondary action (such as reporting the error)
   */
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  
  /**
   * Icon to display
   */
  icon?: React.ReactNode;
  
  /**
   * Additional class names
   */
  className?: string;
  
  /**
   * CSS classes for the container
   */
  containerClassName?: string;
  
  /**
   * CSS classes for the title
   */
  titleClassName?: string;
  
  /**
   * CSS classes for the description
   */
  descriptionClassName?: string;
  
  /**
   * Layout size variant
   * @default 'default'
   */
  size?: 'compact' | 'default' | 'large';
}

/**
 * ErrorState Component
 * 
 * Displays a user-friendly error state with recovery options
 */
export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  description,
  errorCode,
  error,
  showTechnicalDetails = false,
  showRecoverySuggestions = true,
  recoverySuggestions,
  retryAction,
  secondaryAction,
  icon,
  className,
  containerClassName,
  titleClassName,
  descriptionClassName,
  size = 'default',
}) => {
  // Default error icon
  const defaultIcon = (
    <div className="w-12 h-12 rounded-full bg-error-100 flex items-center justify-center text-error-600">
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
          clipRule="evenodd"
        />
      </svg>
    </div>
  );
  
  // Generate default recovery suggestions based on error
  const getDefaultRecoverySuggestions = (): string[] => {
    const defaultSuggestions = [
      'Try refreshing the page',
      'Check your network connection',
      'Try again in a few minutes',
    ];
    
    // Add error-specific suggestions
    if (error instanceof Error) {
      if (error.message.includes('network') || error.message.includes('fetch') || error.message.includes('connection')) {
        defaultSuggestions.push('Verify your internet connection is stable');
      }
      if (error.message.includes('timeout') || error.message.includes('timed out')) {
        defaultSuggestions.push('The request may have timed out, try again with a stronger connection');
      }
      if (error.message.includes('permission') || error.message.includes('access') || error.message.includes('403')) {
        defaultSuggestions.push('You may not have permission to access this resource');
      }
    }
    
    return defaultSuggestions;
  };
  
  // Size-based styles
  const sizeStyles = {
    compact: {
      container: 'p-4',
      icon: 'w-8 h-8',
      title: 'text-base',
      description: 'text-sm',
    },
    default: {
      container: 'p-6',
      icon: 'w-12 h-12',
      title: 'text-xl',
      description: 'text-base',
    },
    large: {
      container: 'p-8',
      icon: 'w-16 h-16',
      title: 'text-2xl',
      description: 'text-lg',
    },
  };
  
  // Suggestions to display
  const suggestionsToShow = recoverySuggestions || getDefaultRecoverySuggestions();
  
  // Format technical details
  const formatError = (err: unknown): string => {
    if (err instanceof Error) {
      return `${err.name}: ${err.message}${err.stack ? `\n${err.stack}` : ''}`;
    }
    return String(err);
  };
  
  return (
    <div 
      className={cn(
        'w-full bg-white rounded-lg border border-gray-200 shadow-sm',
        sizeStyles[size].container,
        containerClassName
      )}
    >
      <div className={cn('flex flex-col items-center text-center', className)}>
        {/* Icon */}
        <div className={cn('mb-4', sizeStyles[size].icon)}>
          {icon || defaultIcon}
        </div>
        
        {/* Error code */}
        {errorCode && (
          <div className="text-sm font-mono text-gray-500 mb-2">
            Error code: {errorCode}
          </div>
        )}
        
        {/* Title */}
        <h3 
          className={cn(
            'font-semibold text-gray-900 mb-2',
            sizeStyles[size].title,
            titleClassName
          )}
        >
          {title}
        </h3>
        
        {/* Description */}
        {description && (
          <p 
            className={cn(
              'text-gray-500 mb-4',
              sizeStyles[size].description,
              descriptionClassName
            )}
          >
            {description}
          </p>
        )}
        
        {/* Technical Details */}
        {showTechnicalDetails && error && (
          <div className="w-full mt-2 mb-4">
            <details className="text-left">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                Technical Details
              </summary>
              <pre className="mt-2 p-3 bg-gray-50 rounded text-xs text-gray-800 overflow-auto max-h-32">
                {formatError(error)}
              </pre>
            </details>
          </div>
        )}
        
        {/* Recovery Suggestions */}
        {showRecoverySuggestions && suggestionsToShow.length > 0 && (
          <div className="w-full mt-2 mb-4">
            <details>
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                Troubleshooting Suggestions
              </summary>
              <ul className="mt-2 text-left text-sm text-gray-600 space-y-1 pl-5 list-disc">
                {suggestionsToShow.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </details>
          </div>
        )}
        
        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 mt-2">
          {retryAction && (
            <button
              type="button"
              onClick={retryAction.onClick}
              className="inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-error-600 hover:bg-error-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error-500"
            >
              {retryAction.label}
            </button>
          )}
          
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorState;