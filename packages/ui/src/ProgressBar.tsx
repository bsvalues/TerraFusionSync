import React from 'react';

export interface ProgressBarProps {
  value: number;
  max?: number;
  showValue?: boolean;
  colorScheme?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

const colorSchemes = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  red: 'bg-red-500',
  yellow: 'bg-yellow-500',
  purple: 'bg-purple-500',
};

const sizesStyles = {
  xs: 'h-1',
  sm: 'h-2',
  md: 'h-3',
  lg: 'h-4',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  showValue = false,
  colorScheme = 'blue',
  size = 'md',
  className = '',
  label,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showValue && (
            <span className="text-sm font-medium text-gray-700">{`${value}/${max}`}</span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizesStyles[size]}`}>
        <div
          className={`${colorSchemes[colorScheme]} transition-all duration-300 ease-in-out ${sizesStyles[size]}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        ></div>
      </div>
      {!label && showValue && (
        <div className="mt-1 text-xs text-gray-500 text-right">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};