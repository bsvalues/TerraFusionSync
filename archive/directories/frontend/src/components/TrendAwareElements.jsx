import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { getTrendColor } from '../utils/AdaptiveColors';

/**
 * TrendValue - A component to display a value with color indicating trend direction
 * 
 * @param {Object} props - Component props
 * @param {number} props.value - The current value to display
 * @param {number} props.previousValue - The previous value for comparison
 * @param {boolean} props.positiveIsGood - Whether positive trends are good (green) or bad (red)
 * @param {boolean} props.showArrow - Whether to show trend arrow indicator
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.threshold - Threshold for significant change (default: 5%)
 * @param {function} props.formatter - Function to format the displayed value
 */
export const TrendValue = ({
  value,
  previousValue,
  positiveIsGood = true,
  showArrow = true,
  className = '',
  threshold = 5,
  formatter = (val) => val,
  ...props
}) => {
  // Calculate trend percentage if both values provided
  const trendPercentage = useMemo(() => {
    if (value === undefined || previousValue === undefined || previousValue === 0) {
      return 0;
    }
    return ((value - previousValue) / Math.abs(previousValue)) * 100;
  }, [value, previousValue]);
  
  // Get color based on trend
  const { className: trendClass, color } = useMemo(() => {
    return getTrendColor(trendPercentage, positiveIsGood, threshold);
  }, [trendPercentage, positiveIsGood, threshold]);
  
  // Determine arrow direction
  const arrow = useMemo(() => {
    if (!showArrow || trendPercentage === 0) return null;
    return trendPercentage > 0 ? '↑' : '↓';
  }, [showArrow, trendPercentage]);

  // Format the displayed value
  const displayValue = useMemo(() => {
    return formatter(value);
  }, [value, formatter]);

  return (
    <motion.span
      className={`${trendClass} ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {displayValue}
      {arrow && (
        <motion.span
          className="ms-1"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
        >
          {arrow}
        </motion.span>
      )}
    </motion.span>
  );
};

/**
 * TrendBadge - A badge with color based on trend direction
 * 
 * @param {Object} props - Component props
 * @param {number} props.trendValue - The trend value (percentage)
 * @param {boolean} props.positiveIsGood - Whether positive trends are good
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.threshold - Threshold for significant change
 */
export const TrendBadge = ({
  trendValue,
  positiveIsGood = true,
  className = '',
  threshold = 5,
  children,
  ...props
}) => {
  // Get color based on trend
  const { color, backgroundColor } = useMemo(() => {
    return getTrendColor(trendValue, positiveIsGood, threshold);
  }, [trendValue, positiveIsGood, threshold]);
  
  // Determine arrow direction
  const arrow = useMemo(() => {
    if (trendValue === 0) return '';
    return trendValue > 0 ? '↑' : '↓';
  }, [trendValue]);

  return (
    <motion.span
      className={`badge ${className}`}
      style={{ backgroundColor, color }}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
      {arrow && <span className="ms-1">{arrow}</span>}
    </motion.span>
  );
};

/**
 * TrendCard - A card component that adapts border color based on trend
 * 
 * @param {Object} props - Component props
 * @param {number} props.trendValue - The trend value (percentage)
 * @param {boolean} props.positiveIsGood - Whether positive trends are good
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.threshold - Threshold for significant change
 */
export const TrendCard = ({
  trendValue,
  positiveIsGood = true,
  className = '',
  threshold = 5,
  children,
  ...props
}) => {
  // Get colors based on trend
  const { borderColor } = useMemo(() => {
    return getTrendColor(trendValue, positiveIsGood, threshold);
  }, [trendValue, positiveIsGood, threshold]);

  return (
    <motion.div
      className={`card ${className}`}
      style={{ borderColor, borderWidth: '2px' }}
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -10, opacity: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ 
        y: -2, 
        boxShadow: `0 8px 15px rgba(0,0,0,0.1), 0 0 0 2px ${borderColor}40` 
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

/**
 * TrendProgress - A progress bar that changes color based on value trend
 * 
 * @param {Object} props - Component props
 * @param {number} props.value - Current progress value (0-100)
 * @param {number} props.previousValue - Previous progress value for comparison
 * @param {boolean} props.positiveIsGood - Whether positive trends are good
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.threshold - Threshold for significant change
 */
export const TrendProgress = ({
  value,
  previousValue,
  positiveIsGood = true,
  className = '',
  threshold = 5,
  ...props
}) => {
  // Calculate trend percentage
  const trendPercentage = useMemo(() => {
    if (value === undefined || previousValue === undefined || previousValue === 0) {
      return 0;
    }
    return ((value - previousValue) / Math.abs(previousValue)) * 100;
  }, [value, previousValue]);
  
  // Get colors based on trend
  const { color } = useMemo(() => {
    return getTrendColor(trendPercentage, positiveIsGood, threshold);
  }, [trendPercentage, positiveIsGood, threshold]);

  return (
    <div className={`progress ${className}`} {...props}>
      <motion.div
        className="progress-bar"
        style={{ backgroundColor: color }}
        initial={{ width: previousValue ? `${previousValue}%` : '0%' }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin="0"
        aria-valuemax="100"
      />
    </div>
  );
};

/**
 * TrendAlert - Alert component that changes style based on trend
 * 
 * @param {Object} props - Component props
 * @param {number} props.trendValue - The trend value (percentage)
 * @param {boolean} props.positiveIsGood - Whether positive trends are good
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.threshold - Threshold for significant change
 */
export const TrendAlert = ({
  trendValue,
  positiveIsGood = true,
  className = '',
  threshold = 5,
  children,
  ...props
}) => {
  // Get color based on trend
  const { color, backgroundColor } = useMemo(() => {
    return getTrendColor(trendValue, positiveIsGood, threshold);
  }, [trendValue, positiveIsGood, threshold]);

  return (
    <motion.div
      className={`alert ${className}`}
      style={{ backgroundColor, color, borderColor: color }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default {
  TrendValue,
  TrendBadge,
  TrendCard,
  TrendProgress,
  TrendAlert
};