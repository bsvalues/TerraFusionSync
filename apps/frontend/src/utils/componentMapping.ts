import React from 'react';
import { PluginRoute } from './pluginRegistry';

// Import components from plugins
import {
  SyncDashboard,
  NewSyncWizard,
  SyncDetails
} from '@terrafusion/marketplace-sync';

// Map of component names to their actual React components
const componentMap: Record<string, React.ComponentType<any>> = {
  // Market place sync components
  SyncDashboard,
  NewSyncWizard,
  SyncDetails,
  
  // Additional plugin components would be added here
};

// Get the component for a given route
export const getComponentForRoute = (route: PluginRoute): React.ComponentType<any> => {
  const Component = componentMap[route.component];
  
  if (!Component) {
    console.error(`Component ${route.component} not found in component map`);
    // Return a fallback component
    return () => (
      <div className="p-6 bg-red-50 text-red-700 rounded-md">
        <h2 className="text-lg font-semibold">Component Error</h2>
        <p>The component "{route.component}" could not be found.</p>
      </div>
    );
  }
  
  return Component;
};