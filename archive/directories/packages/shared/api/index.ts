import { api, ApiResponse } from './client';

// Type definitions
export interface SyncOperation {
  id: string;
  name: string;
  description?: string;
  source: string;
  target: string;
  dataType: string;
  fields: string[];
  fieldMapping: Record<string, string>;
  filters?: Record<string, any>;
  status: SyncStatus;
  schedule?: {
    frequency: 'once' | 'daily' | 'weekly' | 'monthly';
    startDate: string;
    startTime: string;
    isRecurring: boolean;
    daysOfWeek?: number[];
    dayOfMonth?: number;
  };
  lastRunAt?: string;
  nextRunAt?: string;
  createdAt: string;
  updatedAt: string;
  totalRecords?: number;
  processedRecords?: number;
  failedRecords?: number;
  errorMessage?: string;
  createdBy?: string;
}

export type SyncStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'scheduled';

export interface SyncHistoryEntry {
  id: string;
  syncOperationId: string;
  startTime: string;
  endTime?: string;
  status: SyncStatus;
  totalRecords: number;
  processedRecords: number;
  failedRecords: number;
  errorDetails?: Record<string, any>;
}

export interface SystemInfo {
  id: string;
  name: string;
  type: string;
  description: string;
  connectionDetails: {
    url?: string | boolean;
    apiKey?: boolean;
    oauth?: boolean;
    useCredentials?: boolean;
  };
}

export interface DataTypeInfo {
  id: string;
  name: string;
  description: string;
  fields: Array<{
    name: string;
    type: string;
    required: boolean;
    description?: string;
  }>;
  sourceSystemId?: string;
}

export interface FilterOptions {
  status?: SyncStatus;
  source?: string;
  target?: string;
  dataType?: string;
  [key: string]: any;
}

export interface PaginationMetadata {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

// API functions
export async function getSyncOperations(
  page: number = 1,
  limit: number = 20,
  filters: FilterOptions = {}
): Promise<ApiResponse<SyncOperation[]>> {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...Object.entries(filters)
      .filter(([_, value]) => value !== undefined && value !== null)
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value.toString() }), {})
  });
  
  return api.get<SyncOperation[]>(`/plugins/marketplace-sync/v1/syncs?${queryParams.toString()}`);
}

export async function getSyncOperation(id: string): Promise<ApiResponse<SyncOperation>> {
  return api.get<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}`);
}

export async function createSyncOperation(
  data: Omit<SyncOperation, 'id' | 'createdAt' | 'updatedAt' | 'status'>
): Promise<ApiResponse<SyncOperation>> {
  return api.post<SyncOperation>('/plugins/marketplace-sync/v1/syncs', data);
}

export async function updateSyncOperation(
  id: string,
  data: Partial<SyncOperation>
): Promise<ApiResponse<SyncOperation>> {
  return api.patch<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}`, data);
}

export async function deleteSyncOperation(id: string): Promise<ApiResponse<boolean>> {
  return api.delete<boolean>(`/plugins/marketplace-sync/v1/syncs/${id}`);
}

export async function runSyncOperation(id: string): Promise<ApiResponse<SyncOperation>> {
  return api.post<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}/actions/run`);
}

export async function retrySyncOperation(id: string): Promise<ApiResponse<SyncOperation>> {
  return api.post<SyncOperation>(`/plugins/marketplace-sync/v1/syncs/${id}/actions/retry`);
}

export async function getAvailableSystems(): Promise<ApiResponse<SystemInfo[]>> {
  return api.get<SystemInfo[]>('/plugins/marketplace-sync/v1/systems');
}

export async function getAvailableDataTypes(): Promise<ApiResponse<DataTypeInfo[]>> {
  return api.get<DataTypeInfo[]>('/plugins/marketplace-sync/v1/datatypes');
}

export async function getSyncHistory(syncId: string): Promise<ApiResponse<SyncHistoryEntry[]>> {
  return api.get<SyncHistoryEntry[]>(`/plugins/marketplace-sync/v1/syncs/${syncId}/history`);
}

// Re-export client
export { ApiResponse } from './client';