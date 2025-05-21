import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Button, Card, Badge, ProgressBar, Notification, Spinner } from '@terrafusion/ui';
import { useSyncOperations } from '../hooks/useSyncOperations';
import { useWebSocketConnection } from '../hooks/useWebSocketConnection';

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
  const location = useLocation();
  const [filterStatus, setFilterStatus] = useState<SyncStatus | 'all'>('all');
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  
  // Check for created=true in URL query params (for showing success notification)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('created') === 'true') {
      setShowSuccessNotification(true);
      // Remove the query param after showing notification
      navigate(location.pathname, { replace: true });
      
      // Auto-hide notification after 5 seconds
      const timer = setTimeout(() => {
        setShowSuccessNotification(false);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [location, navigate]);

  // Use custom hook for API operations
  const { 
    operations, 
    isLoading: loading, 
    error, 
    fetchOperations, 
    retryOperation,
    cancelOperation 
  } = useSyncOperations();
  
  // Use WebSocket connection for real-time updates
  const { isConnected: wsConnected } = useWebSocketConnection({
    onMessage: (data) => {
      // Refresh operations list when we receive an update
      fetchOperations();
    }
  });

  // Filter operations based on selected status
  const filteredOperations = filterStatus === 'all'
    ? operations
    : operations.filter(op => op.status === filterStatus);

  // Setup auto-refresh for active operations
  useEffect(() => {
    const hasActiveOperations = operations.some(op => op.status === 'active' || op.status === 'pending');
    
    let intervalId: NodeJS.Timeout | null = null;
    
    // If we have active operations and no WebSocket connection, poll instead
    if (hasActiveOperations && !wsConnected) {
      intervalId = setInterval(() => {
        fetchOperations();
      }, 10000); // Poll every 10 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [operations, wsConnected, fetchOperations]);

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
    navigate('/sync/new');
  };
  
  // Handle retry operation
  const handleRetryOperation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await retryOperation(id);
    } catch (error) {
      console.error('Error retrying operation:', error);
    }
  };
  
  // Handle cancel operation
  const handleCancelOperation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to cancel this operation?')) {
      try {
        await cancelOperation(id);
      } catch (error) {
        console.error('Error canceling operation:', error);
      }
    }
  };

  return (
    <div className="p-6">
      {showSuccessNotification && (
        <Notification
          type="success"
          title="Sync Operation Created"
          message="Your new sync operation has been created successfully."
          onClose={() => setShowSuccessNotification(false)}
          className="mb-6"
        />
      )}
      
      {error && (
        <Notification
          type="error"
          title="Error Loading Sync Operations"
          message={error.message || 'An error occurred while loading sync operations.'}
          onClose={() => {}} // Keep error visible until refresh
          action={{
            label: 'Retry',
            onClick: fetchOperations
          }}
          className="mb-6"
        />
      )}
      
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Sync Operations</h1>
          <p className="text-gray-600">
            View and manage your data sync operations
            {wsConnected && (
              <span className="ml-2 text-green-600 text-xs">
                <span className="inline-block h-2 w-2 rounded-full bg-green-600 mr-1"></span>
                Real-time updates active
              </span>
            )}
          </p>
        </div>
        <div className="flex space-x-2 items-center">
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={fetchOperations}
            disabled={loading}
            className="mr-2"
          >
            {loading ? <Spinner size="sm" className="mr-2" /> : null}
            Refresh
          </Button>
          <Button onClick={handleNewSync}>New Sync Operation</Button>
        </div>
      </div>

      {/* Status filter */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
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

      {loading && operations.length === 0 ? (
        <div className="text-center py-12">
          <Spinner size="lg" className="mb-4" />
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
                        onClick={(e) => handleRetryOperation(operation.id, e)}
                      >
                        Retry
                      </Button>
                    )}
                    {operation.status === 'active' && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => handleCancelOperation(operation.id, e)}
                      >
                        Cancel
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