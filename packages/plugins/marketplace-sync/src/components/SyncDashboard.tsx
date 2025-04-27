import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@terrafusion/ui';

interface SyncOperation {
  id: string;
  name: string;
  type: string;
  status: string;
  source: string;
  target: string;
  created: string;
  progress: number;
}

export const SyncDashboard: React.FC = () => {
  const [operations, setOperations] = useState<SyncOperation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // In a real implementation, this would fetch data from the API
    const fetchOperations = async () => {
      try {
        // Mocked data - would be replaced with actual API call
        setTimeout(() => {
          setOperations([
            {
              id: '1',
              name: 'Weekly Customer Data Sync',
              type: 'Full Sync',
              status: 'Completed',
              source: 'CRM System',
              target: 'Data Warehouse',
              created: '2025-04-20T10:30:00',
              progress: 100
            },
            {
              id: '2',
              name: 'Inventory Update',
              type: 'Incremental Sync',
              status: 'In Progress',
              source: 'Warehouse System',
              target: 'E-commerce Platform',
              created: '2025-04-26T15:45:00',
              progress: 68
            },
            {
              id: '3',
              name: 'Financial Records Sync',
              type: 'Full Sync',
              status: 'Scheduled',
              source: 'Accounting Software',
              target: 'Reporting System',
              created: '2025-04-27T08:00:00',
              progress: 0
            }
          ]);
          setIsLoading(false);
        }, 500);
      } catch (error) {
        console.error('Error fetching sync operations:', error);
        setIsLoading(false);
      }
    };

    fetchOperations();
  }, []);

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      'Completed': 'bg-green-100 text-green-800',
      'In Progress': 'bg-blue-100 text-blue-800',
      'Failed': 'bg-red-100 text-red-800',
      'Scheduled': 'bg-purple-100 text-purple-800',
      'Paused': 'bg-yellow-100 text-yellow-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusMap[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Sync Operations</h1>
        <Button 
          onClick={() => navigate('/marketplace/sync/new')}
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          }
        >
          New Sync
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source → Target
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {operations.map((operation) => (
                <tr key={operation.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link to={`/marketplace/sync/${operation.id}`} className="text-blue-600 hover:text-blue-900 font-medium">
                      {operation.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {operation.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(operation.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {operation.source} → {operation.target}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(operation.created).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full" 
                        style={{ width: `${operation.progress}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500">{operation.progress}%</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link to={`/marketplace/sync/${operation.id}`} className="text-blue-600 hover:text-blue-900 mr-3">
                      View
                    </Link>
                    {operation.status === 'Paused' && (
                      <button className="text-green-600 hover:text-green-900 mr-3">
                        Resume
                      </button>
                    )}
                    {operation.status === 'In Progress' && (
                      <button className="text-yellow-600 hover:text-yellow-900 mr-3">
                        Pause
                      </button>
                    )}
                    {operation.status !== 'Completed' && operation.status !== 'Failed' && (
                      <button className="text-red-600 hover:text-red-900">
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};