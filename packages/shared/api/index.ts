export { default as apiClient, api, type ApiResponse } from './client';

// Sync operation types
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

// Sync API endpoints
export const SyncApi = {
  // Get list of sync operations with filtering
  getSyncs: (filters?: FilterOptions) => {
    return api.get<SyncOperation[]>('/plugins/marketplace-sync/v1/syncs', { params: filters });
  },
  
  // Get a specific sync operation by ID
  getSync: (id: string) => {
    return api.get<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}`);
  },
  
  // Create a new sync operation
  createSync: (data: any) => {
    return api.post<SyncOperation>('/plugins/marketplace-sync/v1/syncs', data);
  },
  
  // Update a sync operation
  updateSync: (id: string, data: any) => {
    return api.patch<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}`, data);
  },
  
  // Retry a failed sync operation
  retrySync: (id: string) => {
    return api.post<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}/actions/retry`);
  },
  
  // Cancel an active sync operation
  cancelSync: (id: string) => {
    return api.post<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}/actions/cancel`);
  },
  
  // Get sync operation history
  getSyncHistory: (id: string) => {
    return api.get<SyncHistoryEntry[]>(`/plugins/marketplace-sync/v1/syncs/${id}/history`);
  },
  
  // Get available systems
  getSystems: () => {
    return api.get<SystemInfo[]>('/plugins/marketplace-sync/v1/systems');
  },
  
  // Get available data types
  getDataTypes: () => {
    return api.get<DataTypeInfo[]>('/plugins/marketplace-sync/v1/datatypes');
  },
  
  // Get sync metrics
  getMetrics: () => {
    return api.get<any>('/plugins/marketplace-sync/v1/metrics');
  }
};