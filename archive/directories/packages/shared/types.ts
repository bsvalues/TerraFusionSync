// Commonly used types across the application

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

// API response format
export interface ApiResponse<T> {
  data: T;
  error: {
    code: string;
    message: string;
    details?: any;
  } | null;
  meta: {
    [key: string]: any;
  };
}

// Plugin related types
export interface PluginRoute {
  path: string;
  component: string;
  exact: boolean;
  name: string;
  menuItem: boolean;
  menuGroup?: string;
  menuIcon?: string;
}

export interface ApiEndpoint {
  path: string;
  method: string;
  description: string;
}

export interface PluginInfo {
  name: string;
  version: string;
  description: string;
  routes: PluginRoute[];
  apiEndpoints?: ApiEndpoint[];
}

// Form types for sync operations
export interface SyncFormData {
  name: string;
  source: string;
  target: string;
  dataType: string;
  fields: string[];
  fieldMapping: Record<string, string>;
  filters?: string;
  schedule: {
    frequency: 'once' | 'hourly' | 'daily' | 'weekly' | 'monthly';
    startDate: string;
    startTime: string;
    endDate?: string;
    isRecurring: boolean;
  };
}

// Metrics types
export interface MetricsData {
  totalOperations: number;
  activeOperations: number;
  completedOperations: number;
  failedOperations: number;
  averageDuration: number;
  totalRecordsProcessed: number;
  successRate: number;
  operationsBySystem: Record<string, number>;
  operationsByDataType: Record<string, number>;
}