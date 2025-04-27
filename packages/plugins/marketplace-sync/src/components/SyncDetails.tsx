import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
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
  logs: Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
  }>;
}

export const SyncDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [operation, setOperation] = useState<SyncOperation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'settings'>('overview');

  useEffect(() => {
    // In a real implementation, this would fetch data from the API
    const fetchOperationDetails = async () => {
      try {
        // Simulating API call delay
        setTimeout(() => {
          // Mock data based on the ID
          setOperation({
            id: id || '1',
            name: 'Weekly Customer Data Sync',
            description: 'Synchronize customer data from CRM to Data Warehouse for reporting',
            type: 'Full Sync',
            status: 'Completed',
            source: 'CRM System',
            target: 'Data Warehouse',
            created: '2025-04-20T10:30:00',
            lastUpdated: '2025-04-20T11:45:23',
            progress: 100,
            records: {
              total: 5000,
              processed: 5000,
              successful: 4950,
              failed: 50
            },
            logs: [
              {
                timestamp: '2025-04-20T10:30:00',
                level: 'info',
                message: 'Sync operation started'
              },
              {
                timestamp: '2025-04-20T10:35:12',
                level: 'info',
                message: 'Retrieved 5000 records from source'
              },
              {
                timestamp: '2025-04-20T11:15:45',
                level: 'warning',
                message: 'Encountered 50 validation errors during processing'
              },
              {
                timestamp: '2025-04-20T11:45:23',
                level: 'info',
                message: 'Sync operation completed'
              }
            ]
          });
          setIsLoading(false);
        }, 800);
      } catch (error) {
        console.error('Error fetching sync operation details:', error);
        setIsLoading(false);
      }
    };

    fetchOperationDetails();
  }, [id]);

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

  const getLogLevelBadge = (level: 'info' | 'warning' | 'error') => {
    const levelMap: Record<string, string> = {
      'info': 'bg-blue-100 text-blue-800',
      'warning': 'bg-yellow-100 text-yellow-800',
      'error': 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${levelMap[level]}`}>
        {level.toUpperCase()}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    );
  }

  if (!operation) {
    return (
      <div className="p-6">
        <div className="text-center py-10">
          <h2 className="text-xl font-semibold mb-2">Sync Operation Not Found</h2>
          <p className="text-gray-600 mb-4">The sync operation you're looking for doesn't exist or has been deleted.</p>
          <Link to="/marketplace/sync">
            <Button variant="primary">Back to Sync Operations</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center">
            <h1 className="text-2xl font-bold">{operation.name}</h1>
            <div className="ml-3">{getStatusBadge(operation.status)}</div>
          </div>
          <p className="text-gray-600 mt-1">{operation.description}</p>
        </div>
        <div className="flex space-x-3">
          {operation.status === 'Paused' && (
            <Button variant="success">Resume</Button>
          )}
          {operation.status === 'In Progress' && (
            <Button variant="warning">Pause</Button>
          )}
          {operation.status !== 'Completed' && operation.status !== 'Failed' && (
            <Button variant="danger">Cancel</Button>
          )}
          {operation.status === 'Completed' && (
            <Button variant="primary">Clone</Button>
          )}
          <Link to="/marketplace/sync">
            <Button variant="secondary">Back</Button>
          </Link>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex">
            <button
              className={`px-6 py-4 text-sm font-medium text-center border-b-2 ${activeTab === 'overview' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`px-6 py-4 text-sm font-medium text-center border-b-2 ${activeTab === 'logs' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              onClick={() => setActiveTab('logs')}
            >
              Logs
            </button>
            <button
              className={`px-6 py-4 text-sm font-medium text-center border-b-2 ${activeTab === 'settings' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              onClick={() => setActiveTab('settings')}
            >
              Settings
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div>
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-2">Progress</h3>
                <ProgressBar
                  value={operation.progress}
                  max={100}
                  showValue
                  size="md"
                  colorScheme={operation.status === 'Failed' ? 'red' : 'blue'}
                  label="Sync Progress"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Sync Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <dl className="grid grid-cols-1 gap-3">
                      <div className="flex">
                        <dt className="text-sm font-medium text-gray-500 w-1/3">Type:</dt>
                        <dd className="text-sm text-gray-900">{operation.type}</dd>
                      </div>
                      <div className="flex">
                        <dt className="text-sm font-medium text-gray-500 w-1/3">Source:</dt>
                        <dd className="text-sm text-gray-900">{operation.source}</dd>
                      </div>
                      <div className="flex">
                        <dt className="text-sm font-medium text-gray-500 w-1/3">Target:</dt>
                        <dd className="text-sm text-gray-900">{operation.target}</dd>
                      </div>
                      <div className="flex">
                        <dt className="text-sm font-medium text-gray-500 w-1/3">Created:</dt>
                        <dd className="text-sm text-gray-900">{new Date(operation.created).toLocaleString()}</dd>
                      </div>
                      <div className="flex">
                        <dt className="text-sm font-medium text-gray-500 w-1/3">Last Updated:</dt>
                        <dd className="text-sm text-gray-900">{new Date(operation.lastUpdated).toLocaleString()}</dd>
                      </div>
                    </dl>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-4">Record Statistics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-blue-600">{operation.records.total.toLocaleString()}</div>
                      <div className="text-sm text-gray-500">Total Records</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-green-600">{operation.records.successful.toLocaleString()}</div>
                      <div className="text-sm text-gray-500">Successful</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-red-600">{operation.records.failed.toLocaleString()}</div>
                      <div className="text-sm text-gray-500">Failed</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {operation.status === 'Completed' ? '100%' : Math.round((operation.records.processed / operation.records.total) * 100) + '%'}
                      </div>
                      <div className="text-sm text-gray-500">Completion Rate</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div>
              <h3 className="text-lg font-medium mb-4">Operation Logs</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="divide-y divide-gray-200">
                  {operation.logs.map((log, index) => (
                    <div key={index} className="py-3">
                      <div className="flex items-center mb-1">
                        <span className="text-sm text-gray-500 mr-2">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                        {getLogLevelBadge(log.level)}
                      </div>
                      <p className="text-sm">{log.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div>
              <h3 className="text-lg font-medium mb-4">Sync Settings</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-600 mb-4">Configure the settings for this sync operation.</p>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="syncName" className="block text-sm font-medium text-gray-700 mb-1">
                      Sync Operation Name
                    </label>
                    <input
                      type="text"
                      id="syncName"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={operation.name}
                      disabled={operation.status === 'In Progress'}
                    />
                  </div>
                  <div>
                    <label htmlFor="syncDescription" className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      id="syncDescription"
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={operation.description}
                      disabled={operation.status === 'In Progress'}
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button variant="primary" disabled={operation.status === 'In Progress'}>
                      Save Settings
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};