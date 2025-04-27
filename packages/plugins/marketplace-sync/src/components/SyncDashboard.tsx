import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button, ProgressBar } from '@terrafusion/ui';

interface SyncOperation {
  id: string;
  name: string;
  description: string;
  type: string;
  status: string;
  source: string;
  target: string;
  created: string;
  lastUpdated: string;
  progress: number;
  records: {
    total: number;
    processed: number;
    successful: number;
    failed: number;
  };
}

export const SyncDashboard: React.FC = () => {
  const [syncOperations, setSyncOperations] = useState<SyncOperation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSyncOperations = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/marketplace-sync/operations');
        if (!response.ok) {
          throw new Error(`Failed to fetch sync operations: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        setSyncOperations(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching sync operations:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSyncOperations();
  }, []);

  // Function to format date strings
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  // Map status to appropriate styles
  const getStatusStyles = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in progress':
        return 'bg-blue-100 text-blue-800';
      case 'scheduled':
        return 'bg-purple-100 text-purple-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Sync Dashboard</h1>
        <Link to="/marketplace/sync/new">
          <Button variant="primary" leftIcon={
            <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          }>
            New Sync Operation
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
          <p className="font-medium">Error loading sync operations</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      ) : (
        <div className="grid gap-6">
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h2 className="text-lg font-medium">Sync Operations</h2>
              <div className="flex space-x-2">
                <button className="text-sm px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-700">Filter</button>
                <button className="text-sm px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-700">Export</button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source → Target
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {syncOperations.map((operation) => (
                    <tr key={operation.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          <Link to={`/marketplace/sync/${operation.id}`} className="hover:text-blue-600">
                            {operation.name}
                          </Link>
                        </div>
                        <div className="text-sm text-gray-500">{operation.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusStyles(operation.status)}`}>
                          {operation.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {operation.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {operation.source} → {operation.target}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="w-32">
                          <ProgressBar
                            value={operation.progress}
                            max={100}
                            size="sm"
                            colorScheme={operation.status === 'Completed' ? 'green' : operation.status === 'Failed' ? 'red' : 'blue'}
                          />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {operation.records.processed}/{operation.records.total} records
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(operation.lastUpdated)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex space-x-3">
                          <Link 
                            to={`/marketplace/sync/${operation.id}`}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View
                          </Link>
                          {operation.status === 'In Progress' && (
                            <button className="text-red-600 hover:text-red-900">
                              Pause
                            </button>
                          )}
                          {operation.status === 'Paused' && (
                            <button className="text-green-600 hover:text-green-900">
                              Resume
                            </button>
                          )}
                          {(operation.status === 'Completed' || operation.status === 'Failed') && (
                            <button className="text-purple-600 hover:text-purple-900">
                              Re-run
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {syncOperations.length === 0 && (
              <div className="text-center py-10">
                <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No sync operations found</h3>
                <p className="mt-1 text-sm text-gray-500">Create a new sync operation to get started.</p>
                <div className="mt-6">
                  <Link
                    to="/marketplace/sync/new"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    New Sync Operation
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};