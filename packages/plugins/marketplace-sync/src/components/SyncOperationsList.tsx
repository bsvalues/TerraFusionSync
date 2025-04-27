import React, { useState, useEffect } from 'react';
import { 
  SyncOperationCard, 
  ErrorState, 
  LoadingState, 
  Button,
  useToastFunctions
} from '@terrafusion/ui';

import { useSyncOperations } from '../hooks/useSyncOperations';

/**
 * SyncOperationsList Component
 * 
 * Displays a list of sync operations with loading, error, and empty states
 */
export const SyncOperationsList: React.FC = () => {
  const { operations, isLoading, error, fetchOperations, startOperation, cancelOperation } = useSyncOperations();
  const [processingId, setProcessingId] = useState<string | null>(null);
  const toast = useToastFunctions();
  
  useEffect(() => {
    fetchOperations();
  }, [fetchOperations]);
  
  // Handle view details
  const handleViewDetails = (id: string) => {
    // Navigate to detail page (implementation would vary based on router)
    window.location.href = `/sync-operations/${id}`;
  };
  
  // Handle start/retry operation
  const handleStartOperation = async (id: string) => {
    setProcessingId(id);
    try {
      await startOperation(id);
      toast.success('Operation started successfully');
    } catch (err) {
      toast.error('Failed to start operation');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };
  
  // Handle cancel operation
  const handleCancelOperation = async (id: string) => {
    setProcessingId(id);
    try {
      await cancelOperation(id);
      toast.info('Operation cancelled');
    } catch (err) {
      toast.error('Failed to cancel operation');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };
  
  // Render loading state
  if (isLoading && !operations.length) {
    return (
      <div className="py-10">
        <LoadingState text="Loading sync operations..." />
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="py-5">
        <ErrorState
          title="Unable to load sync operations"
          description="There was a problem loading the sync operations. Please try again later."
          error={error}
          retryAction={{
            label: 'Try Again',
            onClick: fetchOperations,
          }}
        />
      </div>
    );
  }
  
  // Render empty state
  if (!operations.length) {
    return (
      <div className="py-10 text-center">
        <div className="mb-4">
          <svg 
            className="mx-auto h-12 w-12 text-gray-400" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={1.5} 
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" 
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">No sync operations yet</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by creating your first sync operation.</p>
        <div className="mt-6">
          <Button 
            variant="primary"
            onClick={() => window.location.href = '/sync-operations/new'}
          >
            Create Sync Operation
          </Button>
        </div>
      </div>
    );
  }
  
  // Render list of operations
  return (
    <div className="space-y-4">
      {operations.map((operation) => (
        <SyncOperationCard
          key={operation.id}
          id={operation.id}
          name={operation.name}
          description={operation.description}
          source={operation.source}
          target={operation.target}
          dataType={operation.dataType}
          status={operation.status}
          lastRunAt={operation.lastRunAt}
          nextRunAt={operation.nextRunAt}
          totalRecords={operation.totalRecords}
          processedRecords={operation.processedRecords}
          failedRecords={operation.failedRecords}
          errorMessage={operation.errorMessage}
          onViewDetails={handleViewDetails}
          onRun={handleStartOperation}
          onCancel={handleCancelOperation}
          isLoading={processingId === operation.id}
        />
      ))}
    </div>
  );
};

export default SyncOperationsList;