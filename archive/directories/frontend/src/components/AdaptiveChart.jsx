import React, { useRef, useEffect, useState, useMemo } from 'react';
import Chart from 'chart.js/auto';
import { getChartColorsFromTrend, getTrendGradient } from '../utils/AdaptiveColors';

/**
 * AdaptiveChart - A Chart.js wrapper component that adjusts colors based on data trends
 * 
 * @param {Object} props - Component props
 * @param {string} props.type - Chart type (line, bar, etc)
 * @param {Array} props.labels - Chart labels
 * @param {Array} props.datasets - Dataset objects with data and optional custom configuration
 * @param {Object} props.options - Chart.js options
 * @param {boolean} props.adaptiveColors - Whether to enable adaptive colors (default: true)
 * @param {Object} props.trendConfig - Configuration for trend-based coloring
 * @param {boolean} props.trendConfig.positiveIsGood - Whether positive trends are good (default: true)
 * @param {number} props.trendConfig.threshold - Threshold for significant change (default: 5)
 */
const AdaptiveChart = ({ 
  type = 'line', 
  labels = [], 
  datasets = [], 
  options = {}, 
  adaptiveColors = true,
  trendConfig = { positiveIsGood: true, threshold: 5 },
  height = 300,
  width = '100%',
  className = '',
  ...props 
}) => {
  const chartRef = useRef(null);
  const canvasRef = useRef(null);
  const [chartInstance, setChartInstance] = useState(null);
  
  // Process datasets with trend-based colors if enabled
  const processedDatasets = useMemo(() => {
    if (!adaptiveColors) return datasets;
    
    return datasets.map(dataset => {
      // Skip if dataset has explicit colors set
      if (dataset.borderColor || dataset.backgroundColor) {
        return dataset;
      }
      
      // Apply adaptive colors based on data trends
      const { borderColor, backgroundColor } = getChartColorsFromTrend(
        dataset.data,
        trendConfig.positiveIsGood,
        trendConfig.threshold
      );
      
      return {
        ...dataset,
        borderColor,
        backgroundColor
      };
    });
  }, [datasets, adaptiveColors, trendConfig]);
  
  // Calculate trend arrows for labels based on data patterns
  const trendArrows = useMemo(() => {
    if (!adaptiveColors || datasets.length === 0 || type !== 'line') return [];
    
    const dataset = datasets[0];
    if (!dataset || !dataset.data || dataset.data.length < 2) return [];
    
    return dataset.data.map((value, index) => {
      if (index === 0) return '';
      const prevValue = dataset.data[index - 1];
      if (value > prevValue) return '↑';
      if (value < prevValue) return '↓';
      return '→';
    });
  }, [datasets, adaptiveColors, type]);
  
  // Create and update chart when data changes
  useEffect(() => {
    if (!canvasRef.current) return;
    
    // Clean up previous chart instance
    if (chartInstance) {
      chartInstance.destroy();
    }
    
    const ctx = canvasRef.current.getContext('2d');
    
    // Create gradient for adaptive background if it's a line chart
    let processedDatasets = [...processedDatasets];
    if (adaptiveColors && type === 'line' && processedDatasets.length > 0) {
      processedDatasets = processedDatasets.map(dataset => {
        if (!dataset.fill) return dataset;
        
        // Calculate overall trend for gradient direction
        const data = dataset.data || [];
        if (data.length < 2) return dataset;
        
        let totalChange = 0;
        for (let i = 1; i < data.length; i++) {
          totalChange += data[i] - data[i-1];
        }
        const avgChange = totalChange / (data.length - 1);
        const percentChange = data[0] !== 0 ? (avgChange / data[0] * 100) : 0;
        
        // Create gradient based on trend
        const gradient = getTrendGradient(
          ctx, 
          percentChange, 
          trendConfig.positiveIsGood, 
          trendConfig.threshold
        );
        
        return {
          ...dataset,
          backgroundColor: gradient
        };
      });
    }
    
    // Merge options with defaults and add responsive tooltip
    const mergedOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            // Add trend indicator to tooltip
            label: function(context) {
              const label = context.dataset.label || '';
              const value = context.parsed.y;
              const index = context.dataIndex;
              const arrow = index > 0 ? trendArrows[index] || '' : '';
              return `${label}: ${value} ${arrow}`;
            }
          }
        },
        ...options.plugins
      },
      ...options
    };
    
    // Create new chart
    const newChartInstance = new Chart(ctx, {
      type,
      data: {
        labels,
        datasets: processedDatasets
      },
      options: mergedOptions
    });
    
    setChartInstance(newChartInstance);
    chartRef.current = newChartInstance;
    
    // Clean up on component unmount
    return () => {
      if (newChartInstance) {
        newChartInstance.destroy();
      }
    };
  }, [labels, processedDatasets, options, type, adaptiveColors, trendConfig, trendArrows]);
  
  return (
    <div 
      className={`adaptive-chart-container ${className}`} 
      style={{ width, height }}
      {...props}
    >
      <canvas ref={canvasRef} />
    </div>
  );
};

export default AdaptiveChart;