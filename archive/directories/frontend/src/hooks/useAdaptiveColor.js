import { useMemo } from 'react';
import { getTrendColor, getChartColorsFromTrend } from '../utils/AdaptiveColors';

/**
 * Custom hook to calculate and return adaptive colors based on data trends
 * 
 * @param {number} trendValue - Percentage change value
 * @param {Object} options - Configuration options
 * @param {boolean} options.positiveIsGood - Whether positive trends are good (default: true)
 * @param {number} options.threshold - Threshold for significant change (default: 5)
 * @returns {Object} Object containing color attributes for styling
 */
export const useTrendColor = (trendValue, options = {}) => {
  const { positiveIsGood = true, threshold = 5 } = options;
  
  return useMemo(() => {
    return getTrendColor(trendValue, positiveIsGood, threshold);
  }, [trendValue, positiveIsGood, threshold]);
};

/**
 * Custom hook to calculate trend from a series of data points
 * and return appropriate colors
 * 
 * @param {Array<number>} dataPoints - Array of numeric data points
 * @param {Object} options - Configuration options
 * @param {boolean} options.positiveIsGood - Whether positive trends are good (default: true)
 * @param {number} options.threshold - Threshold for significant change (default: 5)
 * @returns {Object} Object containing calculated trend and color attributes
 */
export const useDataTrendColors = (dataPoints, options = {}) => {
  const { positiveIsGood = true, threshold = 5 } = options;
  
  return useMemo(() => {
    // Calculate trend percentage if enough data points
    if (!dataPoints || dataPoints.length < 2) {
      return {
        trendPercentage: 0,
        trendDirection: 'neutral',
        colors: {
          borderColor: '#6c757d', // Bootstrap secondary/neutral
          backgroundColor: 'rgba(108, 117, 125, 0.1)',
          className: 'text-secondary'
        }
      };
    }
    
    // Calculate the average change across the series
    let totalChange = 0;
    for (let i = 1; i < dataPoints.length; i++) {
      totalChange += dataPoints[i] - dataPoints[i - 1];
    }
    
    const avgChange = totalChange / (dataPoints.length - 1);
    const percentChange = dataPoints[0] !== 0 ? (avgChange / dataPoints[0] * 100) : 0;
    
    // Determine trend direction
    let trendDirection = 'neutral';
    if (percentChange > 0) {
      trendDirection = positiveIsGood ? 'positive' : 'negative';
    } else if (percentChange < 0) {
      trendDirection = positiveIsGood ? 'negative' : 'positive';
    }
    
    // Get colors based on the calculated trend
    const colors = getChartColorsFromTrend(dataPoints, positiveIsGood, threshold);
    const { className } = getTrendColor(percentChange, positiveIsGood, threshold);
    
    return {
      trendPercentage: percentChange,
      trendDirection,
      colors: {
        ...colors,
        className
      }
    };
  }, [dataPoints, positiveIsGood, threshold]);
};

/**
 * Custom hook to compare current and previous values and return trend colors
 * 
 * @param {number} currentValue - Current value
 * @param {number} previousValue - Previous value for comparison
 * @param {Object} options - Configuration options
 * @param {boolean} options.positiveIsGood - Whether positive trends are good (default: true)
 * @param {number} options.threshold - Threshold for significant change (default: 5)
 * @returns {Object} Object containing calculated trend and color attributes
 */
export const useValueComparisonColors = (currentValue, previousValue, options = {}) => {
  const { positiveIsGood = true, threshold = 5 } = options;
  
  return useMemo(() => {
    // Calculate trend percentage
    if (currentValue === undefined || previousValue === undefined || previousValue === 0) {
      return {
        trendPercentage: 0,
        trendDirection: 'neutral',
        trendArrow: '',
        colors: getTrendColor(0, positiveIsGood, threshold)
      };
    }
    
    const trendPercentage = ((currentValue - previousValue) / Math.abs(previousValue)) * 100;
    
    // Determine trend direction and arrow
    let trendDirection = 'neutral';
    let trendArrow = '';
    
    if (trendPercentage > 0) {
      trendDirection = 'up';
      trendArrow = '↑';
    } else if (trendPercentage < 0) {
      trendDirection = 'down';
      trendArrow = '↓';
    }
    
    // Get colors based on the calculated trend
    const colors = getTrendColor(trendPercentage, positiveIsGood, threshold);
    
    return {
      trendPercentage,
      trendDirection,
      trendArrow,
      colors
    };
  }, [currentValue, previousValue, positiveIsGood, threshold]);
};

// Default export of all hooks
export default {
  useTrendColor,
  useDataTrendColors,
  useValueComparisonColors
};