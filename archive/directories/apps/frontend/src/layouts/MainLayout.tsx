import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { getMenuItemsByGroup } from '@/utils/pluginRegistry';

export const MainLayout: React.FC = () => {
  const location = useLocation();
  const menuItemsByGroup = getMenuItemsByGroup();
  
  // Convert menu groups to array for rendering
  const menuGroups = Object.entries(menuItemsByGroup);
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 text-white">
        <div className="p-4 font-bold text-xl">
          <Link to="/" className="flex items-center">
            <svg className="h-8 w-8 mr-2 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            TerraFusion
          </Link>
        </div>
        
        <div className="mt-8">
          <Link 
            to="/"
            className={`flex items-center px-4 py-2 ${location.pathname === '/' ? 'bg-gray-700' : 'hover:bg-gray-700'}`}
          >
            <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard
          </Link>
          
          {/* Menu Groups */}
          {menuGroups.map(([groupName, routes]) => (
            <div key={groupName} className="mt-4">
              <div className="px-4 py-2 text-xs text-gray-400 uppercase tracking-wider">
                {groupName}
              </div>
              
              {routes.map((route) => (
                <Link
                  key={route.path}
                  to={route.path}
                  className={`flex items-center px-4 py-2 ${
                    location.pathname.startsWith(route.path) ? 'bg-gray-700' : 'hover:bg-gray-700'
                  }`}
                >
                  {/* Render menu icon if available */}
                  {route.menuIcon && (
                    <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      {route.menuIcon === 'sync-alt' && (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      )}
                      {/* Add more icon paths here for different icons */}
                    </svg>
                  )}
                  {route.name}
                </Link>
              ))}
            </div>
          ))}
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {/* Top Navigation */}
        <div className="bg-white shadow-sm">
          <div className="flex justify-between items-center px-6 py-4">
            <h1 className="text-xl font-semibold">
              {location.pathname === '/' ? 'Dashboard' : 
                menuItemsByGroup[Object.keys(menuItemsByGroup)[0]]?.find(
                  route => location.pathname.startsWith(route.path)
                )?.name || 'TerraFusion'
              }
            </h1>
            
            <div className="flex items-center">
              <button className="mr-4 text-gray-500 hover:text-gray-700">
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </button>
              
              <div className="relative">
                <button className="flex items-center text-gray-700">
                  <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold">
                    U
                  </div>
                  <span className="ml-2">User</span>
                  <svg className="ml-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Page Content */}
        <main className="p-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;