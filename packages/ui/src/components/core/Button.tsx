import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export type ButtonVariant = 
  | 'primary' 
  | 'secondary' 
  | 'outline' 
  | 'ghost' 
  | 'link'
  | 'success'
  | 'warning'
  | 'error';

export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Visual style variant of the button
   * @default 'primary'
   */
  variant?: ButtonVariant;
  
  /**
   * Size of the button
   * @default 'md'
   */
  size?: ButtonSize;
  
  /**
   * Whether the button takes up the full width of its container
   * @default false
   */
  fullWidth?: boolean;
  
  /**
   * Whether the button is currently in loading state
   * @default false
   */
  isLoading?: boolean;
  
  /**
   * Icon to display before button text
   */
  leftIcon?: React.ReactNode;
  
  /**
   * Icon to display after button text
   */
  rightIcon?: React.ReactNode;
  
  /**
   * If true, the button will have rounded-full style
   * @default false
   */
  rounded?: boolean;
  
  /**
   * Custom class names to apply to the button
   */
  className?: string;
  
  /**
   * Display only an icon without text
   * @default false
   */
  iconButton?: boolean;
  
  /**
   * Whether to remove padding from the button
   * @default false
   */
  noPadding?: boolean;
  
  /**
   * Content of the button
   */
  children?: React.ReactNode;
}

/**
 * Button Component
 * 
 * A versatile button component with various visual styles, sizes, and states
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      isLoading = false,
      leftIcon,
      rightIcon,
      rounded = false,
      className,
      iconButton = false,
      noPadding = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    // Base button styles
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    // Variant styles
    const variantStyles = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus:ring-primary-500 disabled:bg-primary-300',
      secondary: 'bg-secondary-600 text-white hover:bg-secondary-700 active:bg-secondary-800 focus:ring-secondary-500 disabled:bg-secondary-300',
      outline: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:bg-gray-100 focus:ring-primary-500 disabled:bg-gray-50 disabled:text-gray-400',
      ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 active:bg-gray-200 focus:ring-gray-500 disabled:text-gray-400',
      link: 'bg-transparent text-primary-600 hover:underline focus:ring-0 disabled:text-gray-400',
      success: 'bg-success-600 text-white hover:bg-success-700 active:bg-success-800 focus:ring-success-500 disabled:bg-success-300',
      warning: 'bg-warning-600 text-white hover:bg-warning-700 active:bg-warning-800 focus:ring-warning-500 disabled:bg-warning-300',
      error: 'bg-error-600 text-white hover:bg-error-700 active:bg-error-800 focus:ring-error-500 disabled:bg-error-300',
    };
    
    // Size styles
    const sizeStyles = {
      xs: iconButton ? 'p-1 text-xs' : noPadding ? 'text-xs' : 'px-2 py-1 text-xs',
      sm: iconButton ? 'p-1.5 text-sm' : noPadding ? 'text-sm' : 'px-3 py-1.5 text-sm',
      md: iconButton ? 'p-2 text-base' : noPadding ? 'text-base' : 'px-4 py-2 text-base',
      lg: iconButton ? 'p-2.5 text-lg' : noPadding ? 'text-lg' : 'px-5 py-2.5 text-lg',
      xl: iconButton ? 'p-3 text-xl' : noPadding ? 'text-xl' : 'px-6 py-3 text-xl',
    };
    
    // Full width style
    const fullWidthStyle = fullWidth ? 'w-full' : '';
    
    // Rounded style
    const roundedStyle = rounded ? 'rounded-full' : 'rounded-md';
    
    // Disabled style
    const isDisabled = disabled || isLoading;
    
    // Loading spinner
    const LoadingSpinner = () => (
      <svg 
        className="animate-spin -ml-1 mr-2 h-4 w-4" 
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
    
    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          fullWidthStyle,
          roundedStyle,
          isDisabled && 'cursor-not-allowed opacity-75',
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {isLoading && <LoadingSpinner />}
        {!isLoading && leftIcon && <span className={children ? 'mr-2' : ''}>{leftIcon}</span>}
        {children}
        {!isLoading && rightIcon && <span className={children ? 'ml-2' : ''}>{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;