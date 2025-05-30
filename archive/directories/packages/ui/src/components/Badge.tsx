import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  color?: 'blue' | 'gray' | 'green' | 'red' | 'yellow' | 'indigo' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  rounded?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  color = 'blue',
  size = 'md',
  rounded = false,
  className = '',
}) => {
  // Color mappings
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    indigo: 'bg-indigo-100 text-indigo-800',
    purple: 'bg-purple-100 text-purple-800',
  }[color];

  // Size mappings
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  }[size];

  // Rounding
  const roundingClasses = rounded ? 'rounded-full' : 'rounded';

  return (
    <span
      className={`inline-flex items-center font-medium ${colorClasses} ${sizeClasses} ${roundingClasses} ${className}`}
    >
      {children}
    </span>
  );
};

export default Badge;