import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card, Badge, ProgressBar } from '@terrafusion/ui';

type SyncStatus = 'active' | 'completed' | 'failed' | 'pending' | 'scheduled';

interface SyncOperation {
  id: string;
  name: string;
  status: SyncStatus;
  source: string;
  target: string;
  progress: number;
  recordsTotal: number;
  recordsProcessed: number;
  startTime: string;
  endTime?: string;
  lastRunStatus?: string;
}

export const SyncDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [operations, setOperations] = useState<SyncOperation[]>([]);
  const [filterStatus, setFilterStatus] = useState<SyncStatus | 'all'>('all');

  // Fetch sync operations data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // In a real implementation, this would fetch from API
        const response = await fetch('/api/sync/operations');
        if (!response.ok) {
          throw new Error('Failed to fetch sync operations');
        }
        const data = await response.json();
        setOperations(data.operations);
      } catch (error) {
        console.error('Error fetching sync operations:', error);
        // Simulate data for development
        setOperations([
          {
            id: '1',
            name: 'Products Synchronization',
            status: 'active',
            source: 'ERP System',
            target: 'E-commerce Platform',
            progress: 65,
            recordsTotal: 1250,
            recordsProcessed: 812,
            startTime: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          },
          {
            id: '2',
            name: 'Customer Data Migration',
            status: 'completed',
            source: 'Legacy CRM',
            target: 'New CRM Platform',
            progress: 100,
            recordsTotal: 500,
            recordsProcessed: 500,
            startTime: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
            endTime: new Date(Date.now() - 105 * 60 * 1000).toISOString(),
          },
          {
            id: '3',
            name: 'Inventory Update',
            status: 'scheduled',
            source: 'Warehouse System',
            target: 'Marketplace',
            progress: 0,
            recordsTotal: 0,
            recordsProcessed: 0,
            startTime: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
          },
          {
            id: '4',
            name: 'Pricing Update',
            status: 'failed',
            source: 'Pricing System',
            target: 'Marketplace',
            progress: 23,
            recordsTotal: 1500,
            recordsProcessed: 345,
            startTime: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
            endTime: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            lastRunStatus: 'API Error: Target system not responding',
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter operations based on selected status
  const filteredOperations = filterStatus === 'all'
    ? operations
    : operations.filter(op => op.status === filterStatus);

  // Render status badge with appropriate color
  const renderStatusBadge = (status: SyncStatus) => {
    const statusConfig = {
      active: { color: 'blue', label: 'Active' },
      completed: { color: 'green', label: 'Completed' },
      failed: { color: 'red', label: 'Failed' },
      pending: { color: 'yellow', label: 'Pending' },
      scheduled: { color: 'purple', label: 'Scheduled' },
    };
    
    const config = statusConfig[status];
    return (
      <Badge
        color={config.color as 'blue' | 'green' | 'red' | 'yellow' | 'purple'}
      >
        {config.label}
      </Badge>
    );
  };

  // Create a new sync operation
  const handleNewSync = () => {
    navigate('/sync-new');
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Sync Operations</h1>
          <p className="text-gray-600">View and manage your data sync operations</p>
        </div>
        <Button onClick={handleNewSync}>New Sync Operation</Button>
      </div>

      {/* Status filter */}
      <div className="mb-6">
        <div className="flex space-x-2">
          <Button
            variant={filterStatus === 'all' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('all')}
          >
            All
          </Button>
          <Button
            variant={filterStatus === 'active' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('active')}
          >
            Active
          </Button>
          <Button
            variant={filterStatus === 'completed' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('completed')}
          >
            Completed
          </Button>
          <Button
            variant={filterStatus === 'failed' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('failed')}
          >
            Failed
          </Button>
          <Button
            variant={filterStatus === 'scheduled' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('scheduled')}
          >
            Scheduled
          </Button>
          <Button
            variant={filterStatus === 'pending' ? 'primary' : 'tertiary'}
            size="sm"
            onClick={() => setFilterStatus('pending')}
          >
            Pending
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <svg
            className="animate-spin h-10 w-10 text-blue-500 mx-auto mb-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <p className="text-gray-500">Loading sync operations...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {filteredOperations.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
              <svg
                className="h-16 w-16 text-gray-400 mx-auto mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1"
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">No sync operations found</h3>
              <p className="mt-2 text-gray-500">
                {filterStatus !== 'all'
                  ? `There are no ${filterStatus} sync operations.`
                  : 'You have not set up any sync operations yet.'}
              </p>
              {filterStatus !== 'all' ? (
                <Button variant="secondary" className="mt-4" onClick={() => setFilterStatus('all')}>
                  View all operations
                </Button>
              ) : (
                <Button className="mt-4" onClick={handleNewSync}>
                  Create a new sync
                </Button>
              )}
            </div>
          ) : (
            filteredOperations.map((operation) => (
              <Card
                key={operation.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate(`/sync-details/${operation.id}`)}
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="mb-4 md:mb-0">
                    <div className="flex items-center">
                      <h3 className="text-lg font-medium mr-3">{operation.name}</h3>
                      {renderStatusBadge(operation.status)}
                    </div>
                    <div className="mt-2 flex flex-col md:flex-row md:items-center text-sm text-gray-600">
                      <span className="md:mr-6">
                        <span className="font-medium">Source:</span> {operation.source}
                      </span>
                      <span>
                        <span className="font-medium">Target:</span> {operation.target}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <Link
                      to={`/sync-details/${operation.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm mr-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      View Details
                    </Link>
                    {operation.status === 'failed' && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={(e) => {
                          e.stopPropagation();
                          // In a real implementation, this would call an API
                          alert(`Retry operation ${operation.id}`);
                        }}
                      >
                        Retry
                      </Button>
                    )}
                  </div>
                </div>
                
                {operation.status === 'active' && (
                  <div className="mt-4">
                    <ProgressBar
                      progress={operation.progress}
                      showPercentage
                      label={`${operation.recordsProcessed} of ${operation.recordsTotal} records processed`}
                    />
                  </div>
                )}
                
                {operation.status === 'failed' && operation.lastRunStatus && (
                  <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
                    <span className="font-medium">Error:</span> {operation.lastRunStatus}
                  </div>
                )}
                
                <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
                  {operation.status === 'scheduled' ? (
                    <div>
                      <span className="font-medium">Scheduled Start:</span>{' '}
                      {new Date(operation.startTime).toLocaleString()}
                    </div>
                  ) : (
                    <div>
                      <span className="font-medium">Started:</span>{' '}
                      {new Date(operation.startTime).toLocaleString()}
                      {operation.endTime && (
                        <>
                          <span className="mx-2">•</span>
                          <span className="font-medium">Ended:</span>{' '}
                          {new Date(operation.endTime).toLocaleString()}
                        </>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default SyncDashboard;