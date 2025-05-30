import { useState, useCallback } from 'react';
import { 
  getSyncOperations, 
  startSyncOperation, 
  cancelSyncOperation 
} from '../api/services/sync-service';

// Type definition for a sync operation
export interface SyncOperation {
  id: string;
  name: string;
  description?: string;
  source: string;
  target: string;
  dataType: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'scheduled';
  lastRunAt?: string;
  nextRunAt?: string;
  totalRecords?: number;
  processedRecords?: number;
  failedRecords?: number;
  errorMessage?: string;
}

/**
 * Hook for managing sync operations
 * 
 * Provides functions for fetching, starting, and cancelling sync operations
 */
export const useSyncOperations = () => {
  const [operations, setOperations] = useState<SyncOperation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Fetch all sync operations
  const fetchOperations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getSyncOperations();
      setOperations(response.data || []);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch operations'));
      console.error('Error fetching sync operations:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Start/retry a sync operation
  const startOperation = useCallback(async (id: string) => {
    try {
      const response = await startSyncOperation(id);
      
      // Update the operation status in the local state
      setOperations(prev => 
        prev.map(op => 
          op.id === id 
            ? { ...op, status: 'running' as const } 
            : op
        )
      );
      
      return response;
    } catch (err) {
      console.error('Error starting sync operation:', err);
      throw err;
    }
  }, []);

  // Cancel a sync operation
  const cancelOperation = useCallback(async (id: string) => {
    try {
      const response = await cancelSyncOperation(id);
      
      // Update the operation status in the local state
      setOperations(prev => 
        prev.map(op => 
          op.id === id 
            ? { ...op, status: 'cancelled' as const } 
            : op
        )
      );
      
      return response;
    } catch (err) {
      console.error('Error cancelling sync operation:', err);
      throw err;
    }
  }, []);

  return {
    operations,
    isLoading,
    error,
    fetchOperations,
    startOperation,
    cancelOperation
  };
};

export default useSyncOperations;