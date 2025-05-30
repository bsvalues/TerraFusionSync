import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Badge, ProgressBar, TabGroup, Modal } from '@terrafusion/ui';

// Sync operation types
type SyncStatus = 'active' | 'completed' | 'failed' | 'pending' | 'scheduled';

interface SyncOperation {
  id: string;
  name: string;
  status: SyncStatus;
  source: {
    id: string;
    name: string;
    connectionDetails: Record<string, string>;
  };
  target: {
    id: string;
    name: string;
    connectionDetails: Record<string, string>;
  };
  dataType: {
    id: string;
    name: string;
  };
  fields: string[];
  fieldMapping: Record<string, string>;
  filters: string;
  progress: number;
  recordsTotal: number;
  recordsProcessed: number;
  recordsFailed: number;
  startTime: string;
  endTime?: string;
  scheduledTime?: string;
  frequency?: string;
  isRecurring: boolean;
  lastRunStatus?: string;
  history: SyncHistoryEntry[];
}

interface SyncHistoryEntry {
  id: string;
  timestamp: string;
  event: string;
  status: string;
  details?: string;
  recordsProcessed?: number;
  recordsTotal?: number;
  duration?: number;
}

export const SyncDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [operation, setOperation] = useState<SyncOperation | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState('');
  
  // Fetch sync operation data
  useEffect(() => {
    const fetchSyncOperation = async () => {
      try {
        setLoading(true);
        // In a real implementation, this would fetch from API
        const response = await fetch(`/api/sync/operations/${id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch sync operation');
        }
        const data = await response.json();
        setOperation(data);
      } catch (error) {
        console.error('Error fetching sync operation:', error);
        // Simulate data for development
        setOperation({
          id: id || '1',
          name: 'Products Synchronization',
          status: 'active',
          source: {
            id: 'erp',
            name: 'ERP System',
            connectionDetails: {
              url: 'https://api.erp-example.com',
              authType: 'OAuth2',
            },
          },
          target: {
            id: 'ecommerce',
            name: 'E-commerce Platform',
            connectionDetails: {
              url: 'https://api.ecommerce-example.com',
              authType: 'API Key',
            },
          },
          dataType: {
            id: 'products',
            name: 'Products',
          },
          fields: ['sku', 'name', 'description', 'price', 'inventory', 'category'],
          fieldMapping: {
            sku: 'product_id',
            name: 'title',
            description: 'description',
            price: 'price',
            inventory: 'stock_level',
            category: 'category',
          },
          filters: 'category = "electronics" AND inventory > 0',
          progress: 65,
          recordsTotal: 1250,
          recordsProcessed: 812,
          recordsFailed: 15,
          startTime: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          isRecurring: true,
          frequency: 'daily',
          history: [
            {
              id: 'h1',
              timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
              event: 'sync_started',
              status: 'info',
              details: 'Sync operation started',
            },
            {
              id: 'h2',
              timestamp: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
              event: 'processing',
              status: 'info',
              details: 'Processed 10% of records',
              recordsProcessed: 125,
              recordsTotal: 1250,
            },
            {
              id: 'h3',
              timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
              event: 'processing',
              status: 'info',
              details: 'Processed 25% of records',
              recordsProcessed: 312,
              recordsTotal: 1250,
            },
            {
              id: 'h4',
              timestamp: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
              event: 'error',
              status: 'warning',
              details: 'Failed to process 8 records due to validation errors',
            },
            {
              id: 'h5',
              timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
              event: 'processing',
              status: 'info',
              details: 'Processed 50% of records',
              recordsProcessed: 625,
              recordsTotal: 1250,
            },
          ],
        });
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchSyncOperation();
    }
  }, [id]);

  // Handle cancel operation
  const handleCancelOperation = async () => {
    try {
      // In a real implementation, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update operation status locally
      if (operation) {
        setOperation({
          ...operation,
          status: 'pending',
          history: [
            {
              id: `h${operation.history.length + 1}`,
              timestamp: new Date().toISOString(),
              event: 'cancellation_requested',
              status: 'warning',
              details: 'Cancellation requested by user',
            },
            ...operation.history,
          ],
        });
      }
      
      setShowCancelModal(false);
    } catch (error) {
      console.error('Error cancelling operation:', error);
      alert('Failed to cancel operation. Please try again.');
    }
  };

  // Handle edit name
  const handleEditName = async () => {
    if (!editName.trim() || !operation) return;
    
    try {
      // In a real implementation, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update operation name locally
      setOperation({
        ...operation,
        name: editName,
        history: [
          {
            id: `h${operation.history.length + 1}`,
            timestamp: new Date().toISOString(),
            event: 'config_changed',
            status: 'info',
            details: `Operation name changed from "${operation.name}" to "${editName}"`,
          },
          ...operation.history,
        ],
      });
      
      setShowEditModal(false);
    } catch (error) {
      console.error('Error updating operation name:', error);
      alert('Failed to update operation name. Please try again.');
    }
  };

  // Handle retry operation
  const handleRetryOperation = async () => {
    if (!operation) return;
    
    try {
      // In a real implementation, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update operation status locally
      setOperation({
        ...operation,
        status: 'active',
        progress: 0,
        recordsProcessed: 0,
        recordsFailed: 0,
        startTime: new Date().toISOString(),
        endTime: undefined,
        history: [
          {
            id: `h${operation.history.length + 1}`,
            timestamp: new Date().toISOString(),
            event: 'sync_restarted',
            status: 'info',
            details: 'Sync operation restarted',
          },
          ...operation.history,
        ],
      });
    } catch (error) {
      console.error('Error restarting operation:', error);
      alert('Failed to restart operation. Please try again.');
    }
  };

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
        size="md"
      >
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="p-6">
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
          <p className="text-gray-500">Loading sync operation details...</p>
        </div>
      </div>
    );
  }

  if (!operation) {
    return (
      <div className="p-6">
        <div className="text-center py-12 bg-white rounded-lg shadow">
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
          <h3 className="text-lg font-medium text-gray-900">Sync operation not found</h3>
          <p className="mt-2 text-gray-500">
            The sync operation you're looking for does not exist or has been removed.
          </p>
          <Button
            className="mt-4"
            onClick={() => navigate('/sync-dashboard')}
          >
            Back to Sync Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {operation.status === 'active' && (
              <Card>
                <div className="mb-3">
                  <h3 className="text-lg font-medium text-gray-900">Current Progress</h3>
                </div>
                <ProgressBar
                  progress={operation.progress}
                  showPercentage
                  label={`${operation.recordsProcessed} of ${operation.recordsTotal} records processed`}
                  color="blue"
                  size="lg"
                />
                <div className="mt-4 flex flex-wrap gap-4">
                  <div className="bg-blue-50 text-blue-800 p-2 rounded">
                    <span className="font-medium">Records Processed:</span> {operation.recordsProcessed}
                  </div>
                  <div className="bg-red-50 text-red-800 p-2 rounded">
                    <span className="font-medium">Records Failed:</span> {operation.recordsFailed}
                  </div>
                  <div className="bg-gray-50 text-gray-800 p-2 rounded">
                    <span className="font-medium">Records Remaining:</span> {operation.recordsTotal - operation.recordsProcessed}
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex justify-end">
                    <Button
                      variant="danger"
                      onClick={() => setShowCancelModal(true)}
                    >
                      Cancel Operation
                    </Button>
                  </div>
                </div>
              </Card>
            )}
            
            <Card>
              <div className="mb-3 flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Operation Details</h3>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setEditName(operation.name);
                    setShowEditModal(true);
                  }}
                >
                  Edit
                </Button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Name</p>
                    <p className="font-medium">{operation.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <div>{renderStatusBadge(operation.status)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Source</p>
                    <p className="font-medium">{operation.source.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Target</p>
                    <p className="font-medium">{operation.target.name}</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Data Type</p>
                    <p className="font-medium">{operation.dataType.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Schedule</p>
                    <p className="font-medium">
                      {operation.isRecurring
                        ? `Recurring (${operation.frequency})`
                        : 'One-time'}
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Start Time</p>
                    <p className="font-medium">
                      {new Date(operation.startTime).toLocaleString()}
                    </p>
                  </div>
                  {operation.endTime && (
                    <div>
                      <p className="text-sm text-gray-500">End Time</p>
                      <p className="font-medium">
                        {new Date(operation.endTime).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
                {operation.status === 'failed' && (
                  <div className="mt-4 flex justify-end">
                    <Button
                      variant="primary"
                      onClick={handleRetryOperation}
                    >
                      Retry Operation
                    </Button>
                  </div>
                )}
              </div>
            </Card>
            
            <Card>
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-900">Field Mapping</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source Field
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Target Field
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {operation.fields.map((field) => (
                      <tr key={field}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {field}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {operation.fieldMapping[field]}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            
            {operation.filters && (
              <Card>
                <div className="mb-3">
                  <h3 className="text-lg font-medium text-gray-900">Filters</h3>
                </div>
                <div className="bg-gray-50 p-3 rounded font-mono text-sm">
                  {operation.filters}
                </div>
              </Card>
            )}
          </div>
        );
      
      case 'history':
        return (
          <div className="space-y-6">
            <div className="flow-root">
              <ul className="-mb-8">
                {operation.history.map((historyItem, itemIdx) => (
                  <li key={historyItem.id}>
                    <div className="relative pb-8">
                      {itemIdx !== operation.history.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span
                            className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                              historyItem.status === 'warning' || historyItem.status === 'error'
                                ? 'bg-red-500'
                                : 'bg-blue-500'
                            }`}
                          >
                            {historyItem.event === 'error' || historyItem.status === 'warning' || historyItem.status === 'error' ? (
                              <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            ) : historyItem.event === 'sync_started' || historyItem.event === 'sync_restarted' ? (
                              <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                              </svg>
                            ) : historyItem.event === 'sync_completed' ? (
                              <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                              </svg>
                            )}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {historyItem.details}
                              {historyItem.recordsProcessed !== undefined && historyItem.recordsTotal !== undefined && (
                                <span className="font-medium">
                                  {' '}
                                  ({historyItem.recordsProcessed} of {historyItem.recordsTotal} records)
                                </span>
                              )}
                            </p>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            <time dateTime={historyItem.timestamp}>
                              {new Date(historyItem.timestamp).toLocaleString()}
                            </time>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        );
      
      case 'config':
        return (
          <div className="space-y-6">
            <Card>
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-900">Source System Configuration</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Property
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Value
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        System ID
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {operation.source.id}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        System Name
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {operation.source.name}
                      </td>
                    </tr>
                    {Object.entries(operation.source.connectionDetails).map(([key, value]) => (
                      <tr key={key}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {key}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            
            <Card>
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-900">Target System Configuration</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Property
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Value
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        System ID
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {operation.target.id}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        System Name
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {operation.target.name}
                      </td>
                    </tr>
                    {Object.entries(operation.target.connectionDetails).map(([key, value]) => (
                      <tr key={key}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {key}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">{operation.name}</h1>
          <div className="flex items-center mt-1">
            <span className="mr-2">{renderStatusBadge(operation.status)}</span>
            <p className="text-gray-600">
              {operation.dataType.name} from {operation.source.name} to {operation.target.name}
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          onClick={() => navigate('/sync-dashboard')}
        >
          Back to Dashboard
        </Button>
      </div>
      
      {/* Tabs */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <TabGroup
          tabs={[
            { id: 'overview', label: 'Overview', content: null },
            { id: 'history', label: 'History', content: null },
            { id: 'config', label: 'Configuration', content: null },
          ]}
          defaultTab="overview"
          onChange={setActiveTab}
        />
        
        <div className="p-6">
          {renderTabContent()}
        </div>
      </div>
      
      {/* Cancel Operation Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="Cancel Sync Operation"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCancelModal(false)}>
              No, Keep Running
            </Button>
            <Button variant="danger" onClick={handleCancelOperation}>
              Yes, Cancel Operation
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Are you sure you want to cancel this sync operation? This will stop all data transfer immediately.
        </p>
        <p className="mt-2 text-gray-700">
          Any data that has already been synchronized will remain in the target system.
        </p>
      </Modal>
      
      {/* Edit Name Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Sync Operation"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditName} disabled={!editName.trim()}>
              Save Changes
            </Button>
          </>
        }
      >
        <div>
          <label htmlFor="operationName" className="block text-sm font-medium text-gray-700">
            Operation Name
          </label>
          <input
            type="text"
            id="operationName"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="e.g., Product Catalog Sync"
          />
        </div>
      </Modal>
    </div>
  );
};

export default SyncDetails;