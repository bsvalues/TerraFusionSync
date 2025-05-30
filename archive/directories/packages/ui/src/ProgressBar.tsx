import React from 'react';

export interface ProgressBarProps {
  value: number;
  max: number;
  size?: 'sm' | 'md' | 'lg';
  colorScheme?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  showValue?: boolean;
  label?: string;
  animated?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max,
  size = 'md',
  colorScheme = 'blue',
  showValue = false,
  label,
  animated = true,
  className = '',
}) => {
  // Calculate percentage
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  // Size styles
  const sizeStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };
  
  // Color styles
  const colorStyles = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-500',
    purple: 'bg-purple-600',
  };
  
  // Animation style
  const animationStyle = animated ? 'transition-all duration-300 ease-in-out' : '';
  
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showValue && (
            <span className="text-sm font-medium text-gray-700">{value}/{max}</span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${sizeStyles[size]}`}>
        <div
          className={`${colorStyles[colorScheme]} rounded-full ${sizeStyles[size]} ${animationStyle}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      {showValue && !label && (
        <div className="mt-1 text-xs text-gray-500 text-right">
          {value}/{max} ({Math.round(percentage)}%)
        </div>
      )}
    </div>
  );
};