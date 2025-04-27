import React from 'react';

export interface ProgressBarProps {
  progress: number; // 0-100
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'indigo' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  className?: string;
  label?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  color = 'blue',
  size = 'md',
  showPercentage = false,
  className = '',
  label,
}) => {
  // Ensure progress is between 0 and 100
  const normalizedProgress = Math.min(100, Math.max(0, progress));
  
  // Color classes
  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-500',
    indigo: 'bg-indigo-600',
    purple: 'bg-purple-600',
  }[color];
  
  // Size classes
  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }[size];
  
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showPercentage && (
            <span className="text-sm font-medium text-gray-700">{normalizedProgress}%</span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${sizeClasses}`}>
        <div
          className={`${colorClasses} ${sizeClasses} rounded-full`}
          style={{ width: `${normalizedProgress}%` }}
        />
      </div>
      {!label && showPercentage && (
        <div className="mt-1 text-right">
          <span className="text-sm font-medium text-gray-700">{normalizedProgress}%</span>
        </div>
      )}
    </div>
  );
};

export default ProgressBar;