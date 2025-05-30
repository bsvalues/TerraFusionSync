import React from 'react';
import { cn } from '../../utils/cn';

export type StatusType = 
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'scheduled'
  | 'active'
  | 'inactive'
  | 'warning'
  | 'success'
  | 'error'
  | 'info';

export interface StatusBadgeProps {
  /**
   * Status value to display
   */
  status: StatusType;
  
  /**
   * Show the status icon
   * @default true
   */
  showIcon?: boolean;
  
  /**
   * Additional class names
   */
  className?: string;
  
  /**
   * Override the default status label with custom text
   */
  label?: string;
  
  /**
   * Size of the badge
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
  
  /**
   * Render the badge with a pill shape
   * @default true
   */
  pill?: boolean;
  
  /**
   * Whether to outline the badge instead of filling it
   * @default false
   */
  outline?: boolean;
  
  /**
   * Dot indicator beside the label
   * @default true
   */
  showDot?: boolean;
}

/**
 * StatusBadge Component
 * 
 * A badge component for displaying operation and item statuses
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  showIcon = true,
  className,
  label,
  size = 'md',
  pill = true,
  outline = false,
  showDot = true,
}) => {
  // Define colors and icons for each status
  const statusConfig = {
    pending: {
      label: 'Pending',
      baseColor: 'bg-yellow-100 text-yellow-800',
      outlineColor: 'bg-white border border-yellow-400 text-yellow-700',
      dotColor: 'bg-yellow-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
        </svg>
      ),
    },
    running: {
      label: 'Running',
      baseColor: 'bg-blue-100 text-blue-800',
      outlineColor: 'bg-white border border-blue-400 text-blue-700',
      dotColor: 'bg-blue-400',
      icon: (
        <svg className="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
    },
    completed: {
      label: 'Completed',
      baseColor: 'bg-green-100 text-green-800',
      outlineColor: 'bg-white border border-green-400 text-green-700',
      dotColor: 'bg-green-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
    },
    failed: {
      label: 'Failed',
      baseColor: 'bg-red-100 text-red-800',
      outlineColor: 'bg-white border border-red-400 text-red-700',
      dotColor: 'bg-red-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
    },
    cancelled: {
      label: 'Cancelled',
      baseColor: 'bg-gray-100 text-gray-800',
      outlineColor: 'bg-white border border-gray-400 text-gray-700',
      dotColor: 'bg-gray-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
    },
    scheduled: {
      label: 'Scheduled',
      baseColor: 'bg-purple-100 text-purple-800',
      outlineColor: 'bg-white border border-purple-400 text-purple-700',
      dotColor: 'bg-purple-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      ),
    },
    active: {
      label: 'Active',
      baseColor: 'bg-green-100 text-green-800',
      outlineColor: 'bg-white border border-green-400 text-green-700',
      dotColor: 'bg-green-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
    },
    inactive: {
      label: 'Inactive',
      baseColor: 'bg-gray-100 text-gray-800',
      outlineColor: 'bg-white border border-gray-400 text-gray-700',
      dotColor: 'bg-gray-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      ),
    },
    warning: {
      label: 'Warning',
      baseColor: 'bg-yellow-100 text-yellow-800',
      outlineColor: 'bg-white border border-yellow-400 text-yellow-700',
      dotColor: 'bg-yellow-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      ),
    },
    success: {
      label: 'Success',
      baseColor: 'bg-green-100 text-green-800',
      outlineColor: 'bg-white border border-green-400 text-green-700',
      dotColor: 'bg-green-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
    },
    error: {
      label: 'Error',
      baseColor: 'bg-red-100 text-red-800',
      outlineColor: 'bg-white border border-red-400 text-red-700',
      dotColor: 'bg-red-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
    },
    info: {
      label: 'Info',
      baseColor: 'bg-blue-100 text-blue-800',
      outlineColor: 'bg-white border border-blue-400 text-blue-700',
      dotColor: 'bg-blue-400',
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      ),
    },
  };
  
  // Get the correct config based on the status
  const config = statusConfig[status];
  
  // Size configurations
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1',
  };
  
  // Border radius based on pill prop
  const borderRadius = pill ? 'rounded-full' : 'rounded';
  
  // Color based on outline prop
  const colorClasses = outline ? config.outlineColor : config.baseColor;
  
  return (
    <span
      className={cn(
        'inline-flex items-center',
        sizeClasses[size],
        borderRadius,
        colorClasses,
        className
      )}
    >
      {showDot && (
        <span
          className={cn(
            'w-1.5 h-1.5 mr-1.5 rounded-full',
            config.dotColor
          )}
        />
      )}
      
      {showIcon && (
        <span className="mr-1">{config.icon}</span>
      )}
      
      {label || config.label}
    </span>
  );
};

export default StatusBadge;