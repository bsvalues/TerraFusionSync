import React from 'react';
import { cn } from '../../utils/cn';

export interface ProgressBarProps {
  /**
   * Current value of the progress bar
   */
  value: number;
  
  /**
   * Maximum value of the progress bar
   * @default 100
   */
  max?: number;
  
  /**
   * Color variant of the progress bar
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  
  /**
   * Size of the progress bar
   * @default 'md'
   */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  
  /**
   * Whether to show the progress percentage as a label
   * @default false
   */
  showLabel?: boolean;
  
  /**
   * Format for the label display
   * @default 'percent'
   */
  labelFormat?: 'percent' | 'fraction' | 'value';
  
  /**
   * Whether to animate the progress bar
   * @default false
   */
  animated?: boolean;
  
  /**
   * Whether to show stripes in the progress bar
   * @default false
   */
  striped?: boolean;
  
  /**
   * Whether to show indeterminate state (loading)
   * @default false
   */
  indeterminate?: boolean;
  
  /**
   * Additional class names to apply
   */
  className?: string;
  
  /**
   * Additional class names to apply to the bar element
   */
  barClassName?: string;
  
  /**
   * Additional class names to apply to the label element
   */
  labelClassName?: string;
  
  /**
   * Custom label content
   */
  customLabel?: React.ReactNode;
}

/**
 * ProgressBar Component
 * 
 * Displays progress for a task or operation
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  variant = 'primary',
  size = 'md',
  showLabel = false,
  labelFormat = 'percent',
  animated = false,
  striped = false,
  indeterminate = false,
  className,
  barClassName,
  labelClassName,
  customLabel,
}) => {
  // Calculate percentage
  const percent = Math.min(Math.max(0, value), max) / max * 100;
  
  // Container height based on size
  const containerSizes = {
    xs: 'h-1',
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };
  
  // Progress bar colors
  const variantStyles = {
    primary: 'bg-primary-600',
    secondary: 'bg-secondary-600',
    success: 'bg-success-600',
    warning: 'bg-warning-500',
    error: 'bg-error-600',
  };
  
  // Striped style
  const stripedStyle = striped ? 'bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:1rem_100%]' : '';
  
  // Animation style
  const animationStyle = animated ? 'transition-all duration-300 ease-in-out' : '';
  
  // Indeterminate animation
  const indeterminateStyle = indeterminate ? 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[progressIndeterminate_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/30 before:to-transparent' : '';
  
  // Format the label
  const getLabel = () => {
    if (customLabel) return customLabel;
    
    switch (labelFormat) {
      case 'percent':
        return `${Math.round(percent)}%`;
      case 'fraction':
        return `${value}/${max}`;
      case 'value':
        return value.toString();
      default:
        return `${Math.round(percent)}%`;
    }
  };
  
  return (
    <div className={cn('w-full flex flex-col gap-1', className)}>
      {showLabel && (
        <div className={cn('flex justify-between text-sm text-gray-700', labelClassName)}>
          <span>{getLabel()}</span>
        </div>
      )}
      <div className={cn('w-full bg-gray-200 rounded-full overflow-hidden', containerSizes[size])}>
        <div
          className={cn(
            'h-full rounded-full',
            variantStyles[variant],
            stripedStyle,
            animationStyle,
            indeterminateStyle,
            barClassName
          )}
          style={{ width: indeterminate ? '100%' : `${percent}%` }}
          role="progressbar"
          aria-valuenow={indeterminate ? undefined : value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
};

export default ProgressBar;