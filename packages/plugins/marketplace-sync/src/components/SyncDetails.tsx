import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button, ProgressBar, Modal, ModalFooter } from '@terrafusion/ui';

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
  logs: {
    timestamp: string;
    level: string;
    message: string;
  }[];
}

export const SyncDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  // State
  const [syncOperation, setSyncOperation] = useState<SyncOperation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'data'>('overview');
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'cancel' | 'restart' | 'delete' | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);
  
  // Fetch sync operation details
  useEffect(() => {
    const fetchSyncOperation = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/marketplace-sync/operations/${id}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch sync operation: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        setSyncOperation(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching sync operation:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchSyncOperation();
    }
  }, [id]);

  // Function to format date strings
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  };

  // Function to handle confirmation actions
  const handleConfirmAction = async () => {
    if (!confirmAction || !syncOperation) return;
    
    setActionInProgress(true);
    
    try {
      // In a real implementation, these would be actual API calls
      switch (confirmAction) {
        case 'cancel':
          // Simulate API call to cancel the sync operation
          await new Promise(resolve => setTimeout(resolve, 1000));
          // Navigate back to dashboard after cancellation
          navigate('/marketplace/sync');
          break;
        case 'restart':
          // Simulate API call to restart the sync operation
          await new Promise(resolve => setTimeout(resolve, 1000));
          // Refresh the operation details to show the new status
          window.location.reload();
          break;
        case 'delete':
          // Simulate API call to delete the sync operation
          await new Promise(resolve => setTimeout(resolve, 1000));
          // Navigate back to dashboard after deletion
          navigate('/marketplace/sync');
          break;
      }
    } catch (err) {
      console.error('Error performing action:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setActionInProgress(false);
      setIsConfirmModalOpen(false);
      setConfirmAction(null);
    }
  };

  // Function to show the confirmation modal
  const showConfirmModal = (action: 'cancel' | 'restart' | 'delete') => {
    setConfirmAction(action);
    setIsConfirmModalOpen(true);
  };

  // Function to get confirmation modal content based on the action
  const getConfirmModalContent = () => {
    switch (confirmAction) {
      case 'cancel':
        return {
          title: 'Cancel Sync Operation',
          message: 'Are you sure you want to cancel this sync operation? This action cannot be undone.',
          confirmText: 'Yes, Cancel',
        };
      case 'restart':
        return {
          title: 'Restart Sync Operation',
          message: 'Are you sure you want to restart this sync operation? This will reset all progress.',
          confirmText: 'Yes, Restart',
        };
      case 'delete':
        return {
          title: 'Delete Sync Operation',
          message: 'Are you sure you want to delete this sync operation? This action cannot be undone and all data will be lost.',
          confirmText: 'Yes, Delete',
        };
      default:
        return {
          title: 'Confirm Action',
          message: 'Are you sure you want to proceed with this action?',
          confirmText: 'Confirm',
        };
    }
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

  // Map log level to appropriate styles
  const getLogLevelStyles = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'text-red-600';
      case 'warning':
        return 'text-yellow-600';
      case 'info':
        return 'text-blue-600';
      case 'debug':
        return 'text-gray-600';
      default:
        return 'text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700 mb-6">
          <p className="font-medium">Error loading sync operation</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => navigate('/marketplace/sync')}
        >
          Back to Dashboard
        </Button>
      </div>
    );
  }

  if (!syncOperation) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-yellow-700 mb-6">
          <p className="font-medium">Sync operation not found</p>
          <p className="text-sm mt-1">The requested sync operation could not be found.</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => navigate('/marketplace/sync')}
        >
          Back to Dashboard
        </Button>
      </div>
    );
  }

  // Modal content
  const modalContent = getConfirmModalContent();

  return (
    <div className="p-6">
      {/* Header section */}
      <div className="mb-6 flex justify-between items-center">
        <div className="flex items-center">
          <Link to="/marketplace/sync" className="mr-4 text-blue-600 hover:text-blue-800">
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <h1 className="text-2xl font-bold">{syncOperation.name}</h1>
          <span className={`ml-4 px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusStyles(syncOperation.status)}`}>
            {syncOperation.status}
          </span>
        </div>
        <div className="flex space-x-3">
          {syncOperation.status === 'In Progress' && (
            <Button
              variant="warning"
              onClick={() => showConfirmModal('cancel')}
            >
              Cancel
            </Button>
          )}
          {syncOperation.status === 'Completed' || syncOperation.status === 'Failed' ? (
            <Button
              variant="primary"
              onClick={() => showConfirmModal('restart')}
            >
              Restart
            </Button>
          ) : syncOperation.status === 'Paused' ? (
            <Button
              variant="success"
            >
              Resume
            </Button>
          ) : null}
          <Button
            variant="danger"
            onClick={() => showConfirmModal('delete')}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Description */}
      <div className="mb-6 text-gray-600">
        {syncOperation.description}
      </div>

      {/* Progress section */}
      {(syncOperation.status === 'In Progress' || syncOperation.status === 'Paused') && (
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Progress: {syncOperation.progress}%
            </span>
            <span className="text-sm font-medium text-gray-700">
              {syncOperation.records.processed}/{syncOperation.records.total} records
            </span>
          </div>
          <ProgressBar
            value={syncOperation.progress}
            max={100}
            size="md"
            colorScheme={syncOperation.status === 'Paused' ? 'yellow' : 'blue'}
            animated={syncOperation.status === 'In Progress'}
          />
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-gray-500">Total Records</div>
              <div className="text-lg font-semibold">{syncOperation.records.total}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Processed</div>
              <div className="text-lg font-semibold text-green-600">{syncOperation.records.successful}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Failed</div>
              <div className="text-lg font-semibold text-red-600">{syncOperation.records.failed}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'logs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('logs')}
          >
            Logs
          </button>
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'data'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('data')}
          >
            Data Preview
          </button>
        </nav>
      </div>

      {/* Tab content */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        {activeTab === 'overview' && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium mb-4">Sync Details</h3>
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                  <div className="border-t border-gray-200">
                    <dl>
                      <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Name</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{syncOperation.name}</dd>
                      </div>
                      <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Sync Type</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{syncOperation.type}</dd>
                      </div>
                      <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Status</dt>
                        <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusStyles(syncOperation.status)}`}>
                            {syncOperation.status}
                          </span>
                        </dd>
                      </div>
                      <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Source</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{syncOperation.source}</dd>
                      </div>
                      <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Target</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{syncOperation.target}</dd>
                      </div>
                      <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Created</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(syncOperation.created)}</dd>
                      </div>
                      <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(syncOperation.lastUpdated)}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-4">Record Statistics</h3>
                <div className="bg-white shadow rounded-lg p-6">
                  <div className="mb-6">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-500">Total Records</span>
                      <span className="text-sm font-medium text-gray-900">{syncOperation.records.total}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div className="bg-gray-600 h-2.5 rounded-full" style={{ width: '100%' }}></div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-500">Processed</span>
                      <span className="text-sm font-medium text-gray-900">{syncOperation.records.processed} ({Math.round((syncOperation.records.processed / syncOperation.records.total) * 100)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${(syncOperation.records.processed / syncOperation.records.total) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-500">Successful</span>
                      <span className="text-sm font-medium text-gray-900">{syncOperation.records.successful} ({Math.round((syncOperation.records.successful / syncOperation.records.total) * 100)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div className="bg-green-600 h-2.5 rounded-full" style={{ width: `${(syncOperation.records.successful / syncOperation.records.total) * 100}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-500">Failed</span>
                      <span className="text-sm font-medium text-gray-900">{syncOperation.records.failed} ({Math.round((syncOperation.records.failed / syncOperation.records.total) * 100)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div className="bg-red-600 h-2.5 rounded-full" style={{ width: `${(syncOperation.records.failed / syncOperation.records.total) * 100}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Operation Logs</h3>
            <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto font-mono text-sm">
              {syncOperation.logs.map((log, index) => (
                <div key={index} className="mb-2">
                  <span className="text-gray-500">[{formatDate(log.timestamp)}]</span>{' '}
                  <span className={`font-semibold ${getLogLevelStyles(log.level)}`}>{log.level.toUpperCase()}</span>:{' '}
                  <span>{log.message}</span>
                </div>
              ))}
              {syncOperation.logs.length === 0 && (
                <div className="text-gray-500 italic">No logs available</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Data Preview</h3>
            {syncOperation.status === 'Completed' || syncOperation.status === 'In Progress' ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source Value
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Target Value
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {/* Sample data - would be dynamic in a real implementation */}
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">001</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Product Alpha</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Electronics</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Synced
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$499.99</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$499.99</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">002</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Product Beta</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Clothing</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Synced
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$29.99</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$29.99</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">003</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Product Gamma</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Food</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                          Error
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$8.99</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-500">Invalid format</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No data available</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Data preview is only available for operations that have processed data.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title={modalContent.title}
      >
        <p className="text-sm text-gray-500">{modalContent.message}</p>
        <div className="mt-4">
          <ModalFooter 
            onCancel={() => setIsConfirmModalOpen(false)}
            onConfirm={handleConfirmAction}
            cancelText="Cancel"
            confirmText={modalContent.confirmText}
            isLoading={actionInProgress}
          />
        </div>
      </Modal>
    </div>
  );
};