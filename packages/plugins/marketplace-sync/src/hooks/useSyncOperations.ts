import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Type definitions
export type SyncStatus = 'active' | 'completed' | 'failed' | 'pending' | 'scheduled';

export interface SyncOperation {
  id: string;
  name: string;
  status: SyncStatus;
  source: string;
  target: string;
  dataType: string;
  fields: string[];
  fieldMapping: Record<string, string>;
  filters?: string;
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
  createdAt: string;
  updatedAt: string;
}

export interface SyncHistoryEntry {
  id: string;
  syncId: string;
  timestamp: string;
  event: string;
  status: string;
  details?: string;
  recordsProcessed?: number;
  recordsTotal?: number;
  duration?: number;
}

export interface SystemInfo {
  id: string;
  name: string;
  type: string;
  connectionDetails: Record<string, any>;
}

export interface DataTypeInfo {
  id: string;
  name: string;
  fields: string[];
}

export interface FilterOptions {
  page?: number;
  limit?: number;
  status?: SyncStatus;
  source?: string;
  target?: string;
  dataType?: string;
  fromDate?: string;
  toDate?: string;
}

export interface PaginationMetadata {
  page: number;
  limit: number;
  totalCount: number;
  totalPages: number;
}

export interface ApiResponse<T> {
  data: T;
  error: {
    code: string;
    message: string;
    details?: any;
  } | null;
  meta: {
    pagination?: PaginationMetadata;
    [key: string]: any;
  };
}

// API endpoints
const API_BASE_URL = '/api/plugins/marketplace-sync/v1';

// Hooks
export function useSyncList(filters: FilterOptions = {}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [operations, setOperations] = useState<SyncOperation[]>([]);
  const [pagination, setPagination] = useState<PaginationMetadata | null>(null);
  
  const fetchOperations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<ApiResponse<SyncOperation[]>>(`${API_BASE_URL}/syncs`, {
        params: filters
      });
      
      setOperations(response.data.data);
      setPagination(response.data.meta.pagination || null);
    } catch (err) {
      console.error('Error fetching sync operations:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch sync operations'));
    } finally {
      setLoading(false);
    }
  }, [filters]);
  
  useEffect(() => {
    fetchOperations();
  }, [fetchOperations]);
  
  return {
    loading,
    error,
    operations,
    pagination,
    refresh: fetchOperations
  };
}

export function useSyncOperation(id: string) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [operation, setOperation] = useState<SyncOperation | null>(null);
  
  const fetchOperation = useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<ApiResponse<SyncOperation>>(`${API_BASE_URL}/syncs/${id}`);
      setOperation(response.data.data);
    } catch (err) {
      console.error(`Error fetching sync operation ${id}:`, err);
      setError(err instanceof Error ? err : new Error('Failed to fetch sync operation'));
    } finally {
      setLoading(false);
    }
  }, [id]);
  
  useEffect(() => {
    fetchOperation();
  }, [fetchOperation]);
  
  // Periodically refresh active operations
  useEffect(() => {
    if (!operation || operation.status !== 'active') return;
    
    const intervalId = setInterval(() => {
      fetchOperation();
    }, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(intervalId);
  }, [operation, fetchOperation]);
  
  return {
    loading,
    error,
    operation,
    refresh: fetchOperation
  };
}

export function useSyncHistory(id: string) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [history, setHistory] = useState<SyncHistoryEntry[]>([]);
  
  const fetchHistory = useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<ApiResponse<SyncHistoryEntry[]>>(`${API_BASE_URL}/syncs/${id}/history`);
      setHistory(response.data.data);
    } catch (err) {
      console.error(`Error fetching sync history for ${id}:`, err);
      setError(err instanceof Error ? err : new Error('Failed to fetch sync history'));
    } finally {
      setLoading(false);
    }
  }, [id]);
  
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);
  
  return {
    loading,
    error,
    history,
    refresh: fetchHistory
  };
}

export function useCreateSync() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SyncOperation | null>(null);
  
  const createSync = async (data: any) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      
      const response = await axios.post<ApiResponse<SyncOperation>>(`${API_BASE_URL}/syncs`, data);
      setResult(response.data.data);
      return response.data.data;
    } catch (err) {
      console.error('Error creating sync operation:', err);
      const error = err instanceof Error ? err : new Error('Failed to create sync operation');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  return {
    loading,
    error,
    result,
    createSync
  };
}

export function useUpdateSync() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SyncOperation | null>(null);
  
  const updateSync = async (id: string, data: any) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      
      const response = await axios.patch<ApiResponse<SyncOperation>>(`${API_BASE_URL}/syncs/${id}`, data);
      setResult(response.data.data);
      return response.data.data;
    } catch (err) {
      console.error(`Error updating sync operation ${id}:`, err);
      const error = err instanceof Error ? err : new Error('Failed to update sync operation');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  return {
    loading,
    error,
    result,
    updateSync
  };
}

export function useRetrySync() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SyncOperation | null>(null);
  
  const retrySync = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      
      const response = await axios.post<ApiResponse<SyncOperation>>(`${API_BASE_URL}/syncs/${id}/actions/retry`);
      setResult(response.data.data);
      return response.data.data;
    } catch (err) {
      console.error(`Error retrying sync operation ${id}:`, err);
      const error = err instanceof Error ? err : new Error('Failed to retry sync operation');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  return {
    loading,
    error,
    result,
    retrySync
  };
}

export function useCancelSync() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SyncOperation | null>(null);
  
  const cancelSync = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      
      const response = await axios.post<ApiResponse<SyncOperation>>(`${API_BASE_URL}/syncs/${id}/actions/cancel`);
      setResult(response.data.data);
      return response.data.data;
    } catch (err) {
      console.error(`Error cancelling sync operation ${id}:`, err);
      const error = err instanceof Error ? err : new Error('Failed to cancel sync operation');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  return {
    loading,
    error,
    result,
    cancelSync
  };
}

export function useSystems() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [systems, setSystems] = useState<SystemInfo[]>([]);
  
  const fetchSystems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<ApiResponse<SystemInfo[]>>(`${API_BASE_URL}/systems`);
      setSystems(response.data.data);
    } catch (err) {
      console.error('Error fetching systems:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch systems'));
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchSystems();
  }, [fetchSystems]);
  
  return {
    loading,
    error,
    systems,
    refresh: fetchSystems
  };
}

export function useDataTypes() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [dataTypes, setDataTypes] = useState<DataTypeInfo[]>([]);
  
  const fetchDataTypes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<ApiResponse<DataTypeInfo[]>>(`${API_BASE_URL}/datatypes`);
      setDataTypes(response.data.data);
    } catch (err) {
      console.error('Error fetching data types:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch data types'));
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchDataTypes();
  }, [fetchDataTypes]);
  
  return {
    loading,
    error,
    dataTypes,
    refresh: fetchDataTypes
  };
}