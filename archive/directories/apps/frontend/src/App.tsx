import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Dashboard } from './pages/Dashboard';
import NotFound from './pages/NotFound';
import { getAllPluginRoutes } from '@/utils/pluginRegistry';
import { getComponentForRoute } from '@/utils/componentMapping';

const App: React.FC = () => {
  // Get all plugin routes for our router
  const pluginRoutes = getAllPluginRoutes();

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        
        {/* Dynamically generated routes from plugins */}
        {pluginRoutes.map((route) => (
          <Route 
            key={route.path}
            path={route.path}
            element={React.createElement(getComponentForRoute(route))}
          />
        ))}
        
        {/* Fallback routes */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default App;