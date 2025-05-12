const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Ensure the frontend_dist directory exists
const distDir = path.join(__dirname, '..', 'static', 'frontend_dist');
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Create a simple bundle from our React components
const bundle = `
// Simple bundled version of the Market Analysis Dashboard React components
(function() {
  const root = document.getElementById('market-analysis-dashboard-root');
  if (!root) return;

  // Get county ID from data attribute
  const countyId = root.getAttribute('data-county-id') || 'DEFAULT_COUNTY';
  
  // Demo data for the dashboard (would normally come from API)
  const demoData = {
    summary: {
      averagePrice: 450000,
      medianPrice: 425000,
      salesVolume: 1250,
      averageDaysOnMarket: 45,
      pricePerSqFt: 350
    },
    previousPeriod: {
      averagePrice: 440000,
      medianPrice: 415000,
      salesVolume: 1200,
      averageDaysOnMarket: 50,
      pricePerSqFt: 340
    },
    trendData: {
      prices: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        averagePrices: [440000, 442000, 445000, 450000, 455000, 460000],
        medianPrices: [415000, 418000, 420000, 422000, 425000, 430000]
      },
      salesVolume: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [1200, 1180, 1220, 1240, 1250, 1280]
      },
      daysOnMarket: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [50, 48, 46, 45, 43, 42]
      },
      pricePerSqFt: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [340, 342, 345, 348, 350, 355]
      }
    }
  };

  // Colors for our dashboard based on Bootstrap theme
  const colors = {
    primary: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#0dcaf0',
    neutral: '#6c757d'
  };

  // Calculate trend percentage between two values
  const calculateTrend = (current, previous) => {
    if (!previous) return 0;
    return ((current - previous) / Math.abs(previous)) * 100;
  };

  // Get appropriate color based on trend direction and magnitude
  const getTrendColor = (trendValue, positiveIsGood = true) => {
    if (trendValue === 0) return colors.neutral;
    
    const isPositive = trendValue > 0;
    const isGood = (isPositive && positiveIsGood) || (!isPositive && !positiveIsGood);
    
    if (isGood) {
      return Math.abs(trendValue) > 5 ? colors.success : colors.info;
    } else {
      return Math.abs(trendValue) > 5 ? colors.danger : colors.warning;
    }
  };

  // Format currency values
  const formatCurrency = (value) => {
    return '$' + value.toLocaleString();
  };

  // Create a simple dashboard with KPIs and charts
  const Dashboard = () => {
    const dashboardStyle = {
      padding: '20px',
      maxWidth: '1200px',
      margin: '0 auto'
    };

    const kpiCardStyle = {
      padding: '15px',
      marginBottom: '20px',
      borderRadius: '8px',
      boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
      transition: 'all 0.3s ease'
    };

    const renderKPICards = () => {
      const kpiData = [
        {
          title: 'Average Price',
          value: demoData.summary.averagePrice,
          previous: demoData.previousPeriod.averagePrice,
          format: formatCurrency,
          positiveIsGood: true,
          icon: 'house-fill'
        },
        {
          title: 'Median Price',
          value: demoData.summary.medianPrice,
          previous: demoData.previousPeriod.medianPrice,
          format: formatCurrency,
          positiveIsGood: true,
          icon: 'tag-fill'
        },
        {
          title: 'Sales Volume',
          value: demoData.summary.salesVolume,
          previous: demoData.previousPeriod.salesVolume,
          format: (v) => v.toLocaleString(),
          positiveIsGood: true,
          icon: 'graph-up'
        },
        {
          title: 'Days on Market',
          value: demoData.summary.averageDaysOnMarket,
          previous: demoData.previousPeriod.averageDaysOnMarket,
          format: (v) => v + ' days',
          positiveIsGood: false, // Lower is better for days on market
          icon: 'clock-fill'
        }
      ];

      return React.createElement('div', { className: 'row' },
        kpiData.map((kpi, index) => {
          const trend = calculateTrend(kpi.value, kpi.previous);
          const trendColor = getTrendColor(trend, kpi.positiveIsGood);
          const trendArrow = trend > 0 ? '↑' : trend < 0 ? '↓' : '';
          
          return React.createElement('div', { 
            className: 'col-md-3 mb-4',
            key: index
          },
            React.createElement('div', { 
              className: 'card h-100',
              style: { ...kpiCardStyle, borderLeft: \`4px solid \${trendColor}\` }
            }, 
              React.createElement('div', { className: 'card-body' },
                React.createElement('h5', { className: 'card-title' },
                  React.createElement('i', { className: \`bi bi-\${kpi.icon} me-2\` }),
                  kpi.title
                ),
                React.createElement('div', { className: 'd-flex justify-content-between' },
                  React.createElement('h3', { 
                    className: 'card-text mb-0',
                    style: { color: trendColor }
                  }, 
                    kpi.format(kpi.value),
                    React.createElement('span', { 
                      className: 'ms-2 small',
                      style: { fontSize: '0.6em' }
                    }, trendArrow + ' ' + Math.abs(trend).toFixed(1) + '%')
                  )
                ),
                React.createElement('p', { className: 'card-text text-muted small' },
                  'Previous: ' + kpi.format(kpi.previous)
                )
              )
            )
          );
        })
      );
    };

    const renderPriceChart = () => {
      // Find the chart container
      const chartContainer = document.getElementById('price-chart');
      if (!chartContainer) return null;

      // Create canvas for Chart.js
      const canvas = document.createElement('canvas');
      canvas.id = 'price-chart-canvas';
      chartContainer.appendChild(canvas);

      // Calculate trend for color
      const priceData = demoData.trendData.prices.averagePrices;
      const avgChange = (priceData[priceData.length-1] - priceData[0]) / priceData[0] * 100;
      const color = getTrendColor(avgChange, true);

      // Create chart
      new Chart(canvas, {
        type: 'line',
        data: {
          labels: demoData.trendData.prices.labels,
          datasets: [
            {
              label: 'Average Price',
              data: demoData.trendData.prices.averagePrices,
              borderColor: color,
              backgroundColor: color + '20', // 20% opacity
              fill: true,
              tension: 0.4
            },
            {
              label: 'Median Price',
              data: demoData.trendData.prices.medianPrices,
              borderColor: colors.neutral,
              borderDash: [5, 5],
              tension: 0.4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += formatCurrency(context.parsed.y);
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            y: {
              ticks: {
                callback: function(value) {
                  return formatCurrency(value);
                }
              }
            }
          }
        }
      });

      return null;
    };

    const renderDaysOnMarketChart = () => {
      // Find the chart container
      const chartContainer = document.getElementById('days-on-market-chart');
      if (!chartContainer) return null;

      // Create canvas for Chart.js
      const canvas = document.createElement('canvas');
      canvas.id = 'days-on-market-chart-canvas';
      chartContainer.appendChild(canvas);

      // Calculate trend for color (negative is good for days on market)
      const domData = demoData.trendData.daysOnMarket.data;
      const avgChange = (domData[domData.length-1] - domData[0]) / domData[0] * 100;
      const color = getTrendColor(avgChange, false); // Lower days on market is better

      // Create chart
      new Chart(canvas, {
        type: 'line',
        data: {
          labels: demoData.trendData.daysOnMarket.labels,
          datasets: [{
            label: 'Days on Market',
            data: demoData.trendData.daysOnMarket.data,
            borderColor: color,
            backgroundColor: color + '20', // 20% opacity
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });

      return null;
    };

    // Return the dashboard structure
    return React.createElement('div', { style: dashboardStyle },
      renderKPICards(),
      React.createElement('div', { className: 'row mb-4' },
        React.createElement('div', { className: 'col-md-6' },
          React.createElement('div', { className: 'card' },
            React.createElement('div', { className: 'card-header' },
              React.createElement('h5', { className: 'mb-0' }, 'Price Trends')
            ),
            React.createElement('div', { className: 'card-body' },
              React.createElement('div', { 
                id: 'price-chart',
                className: 'chart-container'
              })
            )
          )
        ),
        React.createElement('div', { className: 'col-md-6' },
          React.createElement('div', { className: 'card' },
            React.createElement('div', { className: 'card-header' },
              React.createElement('h5', { className: 'mb-0' }, 'Days on Market')
            ),
            React.createElement('div', { className: 'card-body' },
              React.createElement('div', { 
                id: 'days-on-market-chart',
                className: 'chart-container'
              })
            )
          )
        )
      ),
      React.createElement('div', { className: 'demo-note mt-4 alert alert-info' },
        React.createElement('h5', { className: 'alert-heading' }, 'Adaptive Color Scheme Demo'),
        React.createElement('p', { className: 'mb-0' }, 
          'This dashboard demonstrates the adaptive color scheme feature. Colors dynamically change based on data trend direction and magnitude. In a production implementation, all KPIs and charts would use the TrendAwareElements and AdaptiveChart components.'
        )
      ),
      renderPriceChart(),
      renderDaysOnMarketChart()
    );
  };

  // Render the dashboard into the root element
  ReactDOM.createRoot(root).render(
    React.createElement(Dashboard)
  );
})();
`;

// Write the bundle to file
fs.writeFileSync(path.join(distDir, 'index.js'), bundle);

console.log('Market Analysis Dashboard bundle created successfully!');

// Create a package.json file in the frontend directory if it doesn't exist
const packageJsonPath = path.join(__dirname, 'package.json');
if (!fs.existsSync(packageJsonPath)) {
  const packageJson = {
    "name": "terrafusion-frontend",
    "version": "1.0.0",
    "description": "TerraFusion Platform Frontend",
    "scripts": {
      "build": "node build.js"
    },
    "dependencies": {
      "chart.js": "^4.3.0",
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "framer-motion": "^10.14.0"
    }
  };
  
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  console.log('Frontend package.json created successfully!');
}