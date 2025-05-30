import React from 'react';
import { Link } from 'react-router-dom';
import { getMenuItems } from '@/utils/pluginRegistry';

export const Dashboard: React.FC = () => {
  const menuItems = getMenuItems();
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">TerraFusion Dashboard</h1>
      
      <div className="mb-8">
        <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm leading-5 text-blue-700">
                Welcome to TerraFusion SyncService. Navigate through the platform using the sidebar or the quick access cards below.
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium">System Overview</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-500 mr-4">
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">All Systems</p>
                <p className="text-lg font-semibold">Operational</p>
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-500 mr-4">
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Sync Operations</p>
                <p className="text-lg font-semibold">2</p>
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-500 mr-4">
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">Scheduled Operations</p>
                <p className="text-lg font-semibold">1</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium">Quick Access</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {menuItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="bg-white border border-gray-200 hover:border-blue-500 hover:shadow-md rounded-lg p-6 transition duration-200"
              >
                <div className="flex items-center mb-4">
                  <div className="p-2 rounded-full bg-blue-100 text-blue-500 mr-3">
                    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      {item.menuIcon === 'sync-alt' && (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      )}
                      {/* Add more icon paths here based on menuIcon */}
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium">{item.name}</h3>
                </div>
                <p className="text-gray-500">
                  {item.name === 'Sync Dashboard' 
                    ? 'View and manage data synchronization operations across your systems.'
                    : 'Access and configure this feature of the TerraFusion platform.'}
                </p>
              </Link>
            ))}
            
            {/* If there are no menu items, show a placeholder card */}
            {menuItems.length === 0 && (
              <div className="col-span-2 bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900">No plugins installed</h3>
                <p className="text-gray-500 mt-2">
                  There are no available plugins with menu items. Install plugins to add functionality to your TerraFusion platform.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;