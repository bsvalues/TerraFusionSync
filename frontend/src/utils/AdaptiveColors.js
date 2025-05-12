/**
 * AdaptiveColors.js
 * 
 * Utility for generating dynamic color schemes based on data trends.
 * These colors can be used for charts, tables, and other visualizations
 * to provide intuitive visual feedback about the direction and magnitude of data changes.
 */

// Base color palette (Bootstrap-compatible)
const BASE_COLORS = {
  // Core colors
  primary: '#0d6efd',
  success: '#198754',
  danger: '#dc3545',
  warning: '#ffc107',
  info: '#0dcaf0',
  
  // Neutral colors
  neutral: '#6c757d',
  light: '#f8f9fa',
  dark: '#212529',
  
  // Extended palette
  primaryLight: '#cfe2ff',
  successLight: '#d1e7dd',
  dangerLight: '#f8d7da',
  warningLight: '#fff3cd',
  infoLight: '#cff4fc',
};

/**
 * Generate a color based on trend direction and magnitude
 * 
 * @param {number} trendValue - The trend value (positive = upward trend, negative = downward trend)
 * @param {boolean} positiveIsGood - Whether a positive trend is considered good (default: true)
 * @param {number} threshold - Threshold for significant change (default: 5)
 * @returns {Object} Object containing color, backgroundColor, and bootstrap class name
 */
export const getTrendColor = (trendValue, positiveIsGood = true, threshold = 5) => {
  // Default (neutral) color for no change
  if (trendValue === 0) {
    return {
      color: BASE_COLORS.neutral,
      backgroundColor: `${BASE_COLORS.neutral}20`, // 20 = 12.5% opacity in hex
      className: 'text-secondary',
      borderColor: BASE_COLORS.neutral,
    };
  }
  
  // Determine if the trend is positive or negative in the context
  const isPositive = (trendValue > 0);
  const isGoodTrend = (isPositive && positiveIsGood) || (!isPositive && !positiveIsGood);
  
  // Calculate magnitude (0-1 scale based on threshold)
  const magnitude = Math.min(Math.abs(trendValue) / threshold, 1);
  
  // Determine base color scheme based on trend direction and whether it's considered good
  let baseColor, baseClassName;
  if (isGoodTrend) {
    if (magnitude >= 0.8) {
      baseColor = BASE_COLORS.success;
      baseClassName = 'text-success';
    } else {
      baseColor = BASE_COLORS.info;
      baseClassName = 'text-info';
    }
  } else {
    if (magnitude >= 0.8) {
      baseColor = BASE_COLORS.danger;
      baseClassName = 'text-danger';
    } else {
      baseColor = BASE_COLORS.warning;
      baseClassName = 'text-warning';
    }
  }
  
  return {
    color: baseColor,
    backgroundColor: `${baseColor}20`, // 20 = 12.5% opacity in hex
    className: baseClassName,
    borderColor: baseColor,
  };
};

/**
 * Generate a gradient for Chart.js based on trend
 * 
 * @param {object} ctx - Canvas context for Chart.js
 * @param {number} trendValue - The trend value (positive = upward trend, negative = downward trend)
 * @param {boolean} positiveIsGood - Whether a positive trend is considered good (default: true) 
 * @param {number} threshold - Threshold for significant change (default: 5)
 * @returns {CanvasGradient} Gradient for Chart.js
 */
export const getTrendGradient = (ctx, trendValue, positiveIsGood = true, threshold = 5) => {
  const colors = getTrendColor(trendValue, positiveIsGood, threshold);
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  
  // Create gradient with base color
  gradient.addColorStop(0, `${colors.color}80`); // 80 = 50% opacity in hex
  gradient.addColorStop(1, `${colors.color}10`); // 10 = 6.25% opacity in hex
  
  return gradient;
};

/**
 * Generate chart colors based on data series trends
 * 
 * @param {Array<number>} dataPoints - Array of data points
 * @param {boolean} positiveIsGood - Whether a positive trend is considered good
 * @param {number} threshold - Threshold for significant change
 * @returns {Object} Colors for Chart.js
 */
export const getChartColorsFromTrend = (dataPoints, positiveIsGood = true, threshold = 5) => {
  // Calculate trend from the data series
  if (!dataPoints || dataPoints.length < 2) {
    return {
      borderColor: BASE_COLORS.primary,
      backgroundColor: `${BASE_COLORS.primary}20`,
    };
  }
  
  // Calculate the average change across the series
  let totalChange = 0;
  for (let i = 1; i < dataPoints.length; i++) {
    totalChange += dataPoints[i] - dataPoints[i-1];
  }
  
  const avgChange = totalChange / (dataPoints.length - 1);
  const percentChange = avgChange / dataPoints[0] * 100;
  
  // Get colors based on the calculated trend
  const colors = getTrendColor(percentChange, positiveIsGood, threshold);
  
  return {
    borderColor: colors.color,
    backgroundColor: colors.backgroundColor,
  };
};

/**
 * Dynamic color scale for choropleth maps or heat maps
 * 
 * @param {number} value - The value to get a color for
 * @param {number} min - Minimum value in the data set
 * @param {number} max - Maximum value in the data set
 * @param {boolean} positiveIsGood - Whether higher values are considered good
 * @returns {string} CSS color value
 */
export const getScaleColor = (value, min, max, positiveIsGood = true) => {
  // Normalize value to 0-1 range
  const normalizedValue = (value - min) / (max - min);
  
  // Color scales
  const positiveScale = [
    BASE_COLORS.dangerLight,
    BASE_COLORS.warningLight,
    BASE_COLORS.successLight,
  ];
  
  const negativeScale = [
    BASE_COLORS.successLight,
    BASE_COLORS.warningLight,
    BASE_COLORS.dangerLight,
  ];
  
  const scale = positiveIsGood ? positiveScale : negativeScale;
  
  // Calculate color based on position in scale
  if (normalizedValue <= 0.33) {
    return scale[0];
  } else if (normalizedValue <= 0.66) {
    return scale[1];
  } else {
    return scale[2];
  }
};

// Default export
export default {
  BASE_COLORS,
  getTrendColor,
  getTrendGradient,
  getChartColorsFromTrend,
  getScaleColor,
};