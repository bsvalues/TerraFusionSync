import React from 'react';
import ReactDOM from 'react-dom/client';
import MarketAnalysisDashboard from './components/MarketAnalysisDashboard';

// Mount the Market Analysis Dashboard
const dashboardRoot = document.getElementById('market-analysis-dashboard-root');
if (dashboardRoot) {
  // Get county ID from data attribute if available
  const countyId = dashboardRoot.getAttribute('data-county-id') || 'DEFAULT_COUNTY';
  
  ReactDOM.createRoot(dashboardRoot).render(
    <React.StrictMode>
      <MarketAnalysisDashboard countyId={countyId} />
    </React.StrictMode>
  );
}

// Export components for use in other parts of the application
export { default as AdaptiveChart } from './components/AdaptiveChart';
export * from './components/TrendAwareElements';
export * from './hooks/useAdaptiveColor';
export { default as MarketAnalysisDashboard } from './components/MarketAnalysisDashboard';