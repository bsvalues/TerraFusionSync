import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/layouts/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { getPluginRoutes } from '@/utils/pluginRegistry';
import { getComponentByName } from '@/utils/componentMapping';

const App: React.FC = () => {
  const pluginRoutes = getPluginRoutes();

  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        
        {/* Dynamically generated routes from plugins */}
        {pluginRoutes.map((route) => {
          const Component = getComponentByName(route.component);
          if (!Component) {
            console.warn(`Component ${route.component} not found for route ${route.path}`);
            return null;
          }
          
          return (
            <Route 
              key={route.path} 
              path={route.path} 
              element={<Component />} 
            />
          );
        })}
        
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MainLayout>
  );
};

export default App;