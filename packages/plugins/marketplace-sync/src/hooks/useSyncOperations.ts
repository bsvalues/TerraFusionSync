import { useState, useEffect } from 'react';
import { 
  SyncOperation, 
  FilterOptions, 
  DataTypeInfo,
  SystemInfo,
  SyncHistoryEntry,
  getSyncOperations,
  getSyncOperation,
  createSyncOperation,
  updateSyncOperation,
  deleteSyncOperation,
  runSyncOperation,
  retrySyncOperation,
  getAvailableSystems,
  getAvailableDataTypes,
  getSyncHistory
} from '../../../shared/api';

interface UseSyncOperationsOptions {
  page?: number;
  limit?: number;
  filters?: FilterOptions;
  autoFetch?: boolean;
}

interface UseSyncOperationsReturn {
  // Data
  syncOperations: SyncOperation[];
  totalOperations: number; 
  selectedOperation: SyncOperation | null;
  systems: SystemInfo[];
  dataTypes: DataTypeInfo[];
  syncHistory: SyncHistoryEntry[];
  
  // Status
  loading: boolean;
  error: Error | null;
  
  // Pagination
  page: number;
  limit: number;
  totalPages: number;
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
  
  // Filtering
  filters: FilterOptions;
  setFilters: (filters: FilterOptions) => void;
  
  // Actions
  fetchOperations: () => Promise<void>;
  fetchOperation: (id: string) => Promise<void>;
  createOperation: (operation: Omit<SyncOperation, 'id' | 'createdAt' | 'updatedAt' | 'status'>) => Promise<SyncOperation>;
  updateOperation: (id: string, updates: Partial<SyncOperation>) => Promise<SyncOperation>;
  deleteOperation: (id: string) => Promise<void>;
  runOperation: (id: string) => Promise<SyncOperation>;
  retryOperation: (id: string) => Promise<SyncOperation>;
  fetchSystems: () => Promise<void>;
  fetchDataTypes: () => Promise<void>;
  fetchSyncHistory: (operationId: string) => Promise<void>;
}

/**
 * Hook for managing sync operations
 */
export function useSyncOperations(options: UseSyncOperationsOptions = {}): UseSyncOperationsReturn {
  // Default options
  const {
    page: initialPage = 1,
    limit: initialLimit = 10,
    filters: initialFilters = {},
    autoFetch = true
  } = options;
  
  // State
  const [syncOperations, setSyncOperations] = useState<SyncOperation[]>([]);
  const [selectedOperation, setSelectedOperation] = useState<SyncOperation | null>(null);
  const [systems, setSystems] = useState<SystemInfo[]>([]);
  const [dataTypes, setDataTypes] = useState<DataTypeInfo[]>([]);
  const [syncHistory, setSyncHistory] = useState<SyncHistoryEntry[]>([]);
  const [totalOperations, setTotalOperations] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);
  const [filters, setFilters] = useState<FilterOptions>(initialFilters);
  
  // Derived values
  const totalPages = Math.max(1, Math.ceil(totalOperations / limit));
  
  /**
   * Fetch sync operations with current pagination and filters
   */
  const fetchOperations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getSyncOperations(page, limit, filters);
      setSyncOperations(result.data);
      setTotalOperations(result.meta.pagination?.total || 0);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching sync operations:', err);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Fetch a specific sync operation by ID
   */
  const fetchOperation = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getSyncOperation(id);
      setSelectedOperation(result.data);
    } catch (err) {
      setError(err as Error);
      console.error(`Error fetching sync operation ${id}:`, err);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Create a new sync operation
   */
  const createOperation = async (operation: Omit<SyncOperation, 'id' | 'createdAt' | 'updatedAt' | 'status'>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await createSyncOperation(operation);
      
      // Refresh the list if we're on the first page
      if (page === 1) {
        fetchOperations();
      }
      
      return result.data;
    } catch (err) {
      setError(err as Error);
      console.error('Error creating sync operation:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Update an existing sync operation
   */
  const updateOperation = async (id: string, updates: Partial<SyncOperation>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await updateSyncOperation(id, updates);
      
      // Update in the local state if it exists
      setSyncOperations(prev => 
        prev.map(op => op.id === id ? result.data : op)
      );
      
      // Update selected operation if it's the same one
      if (selectedOperation?.id === id) {
        setSelectedOperation(result.data);
      }
      
      return result.data;
    } catch (err) {
      setError(err as Error);
      console.error(`Error updating sync operation ${id}:`, err);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Delete a sync operation
   */
  const deleteOperation = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await deleteSyncOperation(id);
      
      // Remove from local state
      setSyncOperations(prev => prev.filter(op => op.id !== id));
      
      // Clear selected operation if it's the same one
      if (selectedOperation?.id === id) {
        setSelectedOperation(null);
      }
    } catch (err) {
      setError(err as Error);
      console.error(`Error deleting sync operation ${id}:`, err);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Run a sync operation
   */
  const runOperation = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await runSyncOperation(id);
      
      // Update in the local state if it exists
      setSyncOperations(prev => 
        prev.map(op => op.id === id ? result.data : op)
      );
      
      // Update selected operation if it's the same one
      if (selectedOperation?.id === id) {
        setSelectedOperation(result.data);
      }
      
      return result.data;
    } catch (err) {
      setError(err as Error);
      console.error(`Error running sync operation ${id}:`, err);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Retry a failed sync operation
   */
  const retryOperation = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await retrySyncOperation(id);
      
      // Update in the local state if it exists
      setSyncOperations(prev => 
        prev.map(op => op.id === id ? result.data : op)
      );
      
      // Update selected operation if it's the same one
      if (selectedOperation?.id === id) {
        setSelectedOperation(result.data);
      }
      
      return result.data;
    } catch (err) {
      setError(err as Error);
      console.error(`Error retrying sync operation ${id}:`, err);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Fetch available systems
   */
  const fetchSystems = async () => {
    setLoading(true);
    
    try {
      const result = await getAvailableSystems();
      setSystems(result.data);
    } catch (err) {
      console.error('Error fetching available systems:', err);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Fetch available data types
   */
  const fetchDataTypes = async () => {
    setLoading(true);
    
    try {
      const result = await getAvailableDataTypes();
      setDataTypes(result.data);
    } catch (err) {
      console.error('Error fetching available data types:', err);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Fetch sync history for a specific operation
   */
  const fetchSyncHistory = async (operationId: string) => {
    setLoading(true);
    
    try {
      const result = await getSyncHistory(operationId);
      setSyncHistory(result.data);
    } catch (err) {
      console.error(`Error fetching history for operation ${operationId}:`, err);
    } finally {
      setLoading(false);
    }
  };
  
  // Auto-fetch on mount and when pagination/filters change
  useEffect(() => {
    if (autoFetch) {
      fetchOperations();
    }
  }, [page, limit, JSON.stringify(filters)]);
  
  return {
    // Data
    syncOperations,
    totalOperations,
    selectedOperation,
    systems,
    dataTypes,
    syncHistory,
    
    // Status
    loading,
    error,
    
    // Pagination
    page,
    limit,
    totalPages,
    setPage,
    setLimit,
    
    // Filtering
    filters,
    setFilters,
    
    // Actions
    fetchOperations,
    fetchOperation,
    createOperation,
    updateOperation,
    deleteOperation,
    runOperation,
    retryOperation,
    fetchSystems,
    fetchDataTypes,
    fetchSyncHistory
  };
}