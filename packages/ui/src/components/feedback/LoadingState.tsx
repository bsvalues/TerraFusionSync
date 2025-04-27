import React from 'react';
import { cn } from '../../utils/cn';

export type LoadingVariant = 'spinner' | 'dots' | 'pulse' | 'skeleton';
export type LoadingSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface LoadingStateProps {
  /**
   * Loading indicator variant
   * @default 'spinner'
   */
  variant?: LoadingVariant;
  
  /**
   * Size of the loading indicator
   * @default 'md'
   */
  size?: LoadingSize;
  
  /**
   * Text to display while loading
   */
  text?: string;
  
  /**
   * Whether to center the loading indicator
   * @default true
   */
  centered?: boolean;
  
  /**
   * Whether to make the loading indicator full screen with overlay
   * @default false
   */
  fullScreen?: boolean;
  
  /**
   * Additional information or context about the loading process
   */
  description?: string;
  
  /**
   * Color of the loading indicator
   * @default 'primary'
   */
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'gray';
  
  /**
   * Additional class name for the component
   */
  className?: string;
  
  /**
   * Additional class name for the loading indicator
   */
  indicatorClassName?: string;
  
  /**
   * Additional class name for the text
   */
  textClassName?: string;
}

/**
 * LoadingState Component
 * 
 * Displays a loading indicator with various styles
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  variant = 'spinner',
  size = 'md',
  text,
  centered = true,
  fullScreen = false,
  description,
  color = 'primary',
  className,
  indicatorClassName,
  textClassName,
}) => {
  // Size styles for spinner
  const spinnerSizes = {
    xs: 'w-4 h-4',
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
    xl: 'w-12 h-12',
  };
  
  // Size styles for dots
  const dotSizes = {
    xs: 'w-1 h-1',
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
    xl: 'w-3 h-3',
  };
  
  // Size styles for text
  const textSizes = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };
  
  // Size styles for pulse
  const pulseSizes = {
    xs: 'w-12 h-12',
    sm: 'w-16 h-16',
    md: 'w-20 h-20',
    lg: 'w-24 h-24',
    xl: 'w-32 h-32',
  };
  
  // Size styles for skeleton
  const skeletonSizes = {
    xs: 'h-2',
    sm: 'h-3',
    md: 'h-4',
    lg: 'h-5',
    xl: 'h-6',
  };
  
  // Color styles
  const colorStyles = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600',
    success: 'text-success-600',
    warning: 'text-warning-600',
    error: 'text-error-600',
    gray: 'text-gray-600',
  };
  
  // Container styles
  const containerStyles = cn(
    centered && 'flex flex-col items-center justify-center',
    fullScreen && 'fixed inset-0 z-50 bg-white/80 backdrop-blur-sm',
    className
  );
  
  // Spinner loading indicator
  const SpinnerIndicator = () => (
    <svg
      className={cn(
        'animate-spin',
        spinnerSizes[size],
        colorStyles[color],
        indicatorClassName
      )}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
  
  // Dots loading indicator
  const DotsIndicator = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn(
            'rounded-full',
            dotSizes[size],
            colorStyles[color],
            'animate-[bounceDelayed_1.4s_ease-in-out_infinite]',
            `animation-delay-${i * 2}00`,
            indicatorClassName
          )}
          style={{
            animationDelay: `${i * 0.2}s`,
          }}
        ></div>
      ))}
    </div>
  );
  
  // Pulse loading indicator
  const PulseIndicator = () => (
    <div
      className={cn(
        'rounded-full',
        pulseSizes[size],
        'border-2',
        `border-${color}-500`,
        'animate-ping opacity-75',
        indicatorClassName
      )}
    ></div>
  );
  
  // Skeleton loading indicator
  const SkeletonIndicator = () => (
    <div
      className={cn(
        'animate-pulse rounded',
        skeletonSizes[size],
        'bg-gray-200',
        'w-full max-w-sm',
        indicatorClassName
      )}
    ></div>
  );
  
  // Render appropriate loading indicator
  const renderLoadingIndicator = () => {
    switch (variant) {
      case 'spinner':
        return <SpinnerIndicator />;
      case 'dots':
        return <DotsIndicator />;
      case 'pulse':
        return <PulseIndicator />;
      case 'skeleton':
        return <SkeletonIndicator />;
      default:
        return <SpinnerIndicator />;
    }
  };
  
  return (
    <div className={containerStyles}>
      {renderLoadingIndicator()}
      
      {text && (
        <div
          className={cn(
            'mt-4',
            textSizes[size],
            'text-gray-700',
            textClassName
          )}
        >
          {text}
        </div>
      )}
      
      {description && (
        <div className={cn('mt-2 text-sm text-gray-500 max-w-xs text-center')}>
          {description}
        </div>
      )}
    </div>
  );
};

/**
 * SkeletonLoader Component
 * 
 * A specialized component for skeleton loading states
 */
export const SkeletonLoader: React.FC<{
  /**
   * Number of skeleton lines to display
   * @default 3
   */
  lines?: number;
  
  /**
   * Width of each line (as CSS value)
   */
  width?: string;
  
  /**
   * Height of each line
   * @default 'md'
   */
  height?: LoadingSize;
  
  /**
   * Whether to vary the width of lines randomly
   * @default true
   */
  randomWidth?: boolean;
  
  /**
   * Spacing between lines
   * @default 'md'
   */
  spacing?: 'xs' | 'sm' | 'md' | 'lg';
  
  /**
   * Additional class name
   */
  className?: string;
}> = ({ 
  lines = 3,
  width = '100%',
  height = 'md',
  randomWidth = true,
  spacing = 'md',
  className
}) => {
  const heightSizes = {
    xs: 'h-2',
    sm: 'h-3',
    md: 'h-4',
    lg: 'h-5',
    xl: 'h-6',
  };
  
  const spacingSizes = {
    xs: 'space-y-1',
    sm: 'space-y-2',
    md: 'space-y-3',
    lg: 'space-y-4',
  };
  
  // Generate random width if enabled
  const getRandomWidth = (index: number): string => {
    if (!randomWidth) return width;
    
    // Last line is usually shorter
    if (index === lines - 1) {
      return `${Math.floor(Math.random() * 40) + 30}%`;
    }
    
    // Other lines vary less
    return `${Math.floor(Math.random() * 20) + 80}%`;
  };
  
  return (
    <div className={cn('animate-pulse', spacingSizes[spacing], className)}>
      {Array(lines)
        .fill(0)
        .map((_, i) => (
          <div
            key={i}
            className={cn('bg-gray-200 rounded', heightSizes[height])}
            style={{ width: getRandomWidth(i) }}
          />
        ))}
    </div>
  );
};

export default LoadingState;