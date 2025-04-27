import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Content of the card
   */
  children: React.ReactNode;
  
  /**
   * Whether to remove padding inside the card
   * @default false
   */
  noPadding?: boolean;
  
  /**
   * Add a subtle hover effect to the card
   * @default false
   */
  hoverable?: boolean;
  
  /**
   * Makes the card clickable and adds appropriate hover styles
   * @default false
   */
  clickable?: boolean;
  
  /**
   * Apply a border to the card
   * @default false
   */
  bordered?: boolean;
  
  /**
   * Make the border on a specific edge more prominent
   */
  accentBorder?: 'top' | 'right' | 'bottom' | 'left' | 'none';
  
  /**
   * Adjust the shadow/elevation of the card
   * @default 'md'
   */
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * Card Component
 * 
 * A versatile container component for grouping related content and actions
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      className,
      noPadding = false,
      hoverable = false,
      clickable = false,
      bordered = false,
      accentBorder = 'none',
      shadow = 'md',
      ...props
    }, 
    ref
  ) => {
    // Base styles
    const baseStyles = 'bg-white rounded-lg overflow-hidden';
    
    // Padding styles
    const paddingStyles = noPadding ? '' : 'p-6';
    
    // Border styles
    const borderStyles = bordered ? 'border border-gray-200' : '';
    
    // Accent border styles
    const accentBorderStyles = {
      top: 'border-t-2 border-t-primary-500',
      right: 'border-r-2 border-r-primary-500',
      bottom: 'border-b-2 border-b-primary-500',
      left: 'border-l-2 border-l-primary-500',
      none: ''
    };
    
    // Shadow styles
    const shadowStyles = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow',
      lg: 'shadow-lg',
      xl: 'shadow-xl'
    };
    
    // Interactive styles
    const hoverStyles = hoverable ? 'transition-all duration-200 ease-in-out hover:shadow-lg' : '';
    const clickableStyles = clickable 
      ? 'cursor-pointer transition-all duration-200 ease-in-out hover:shadow-lg active:shadow-md active:translate-y-0.5' 
      : '';
    
    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          paddingStyles,
          borderStyles,
          accentBorder !== 'none' && accentBorderStyles[accentBorder],
          shadowStyles[shadow],
          hoverStyles,
          clickableStyles,
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;