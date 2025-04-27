import { v4 as uuidv4 } from 'uuid';

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

export interface FilterOptions {
  page: number;
  limit: number;
  status?: string;
  source?: string;
  target?: string;
  dataType?: string;
  fromDate?: string;
  toDate?: string;
}

// Systems and data types
const availableSystems: SystemInfo[] = [
  {
    id: 'erp',
    name: 'ERP System',
    type: 'enterprise',
    connectionDetails: {
      url: 'https://api.erp-example.com',
      authType: 'OAuth2',
    },
  },
  {
    id: 'crm',
    name: 'CRM Platform',
    type: 'enterprise',
    connectionDetails: {
      url: 'https://api.crm-example.com',
      authType: 'Basic',
    },
  },
  {
    id: 'ecommerce',
    name: 'E-commerce Platform',
    type: 'ecommerce',
    connectionDetails: {
      url: 'https://api.ecommerce-example.com',
      authType: 'API Key',
    },
  },
  {
    id: 'warehouse',
    name: 'Warehouse Management',
    type: 'logistics',
    connectionDetails: {
      url: 'https://api.warehouse-example.com',
      authType: 'API Key',
    },
  },
  {
    id: 'marketplace',
    name: 'Online Marketplace',
    type: 'ecommerce',
    connectionDetails: {
      url: 'https://api.marketplace-example.com',
      authType: 'OAuth2',
    },
  },
  {
    id: 'accounting',
    name: 'Accounting System',
    type: 'finance',
    connectionDetails: {
      url: 'https://api.accounting-example.com',
      authType: 'Basic',
    },
  },
];

const dataTypes: DataTypeInfo[] = [
  {
    id: 'products',
    name: 'Products',
    fields: ['sku', 'name', 'description', 'price', 'inventory', 'category'],
  },
  {
    id: 'customers',
    name: 'Customers',
    fields: ['id', 'name', 'email', 'phone', 'address', 'segment'],
  },
  {
    id: 'orders',
    name: 'Orders',
    fields: ['id', 'customer_id', 'date', 'total', 'status', 'items'],
  },
  {
    id: 'inventory',
    name: 'Inventory',
    fields: ['sku', 'quantity', 'location', 'status', 'last_updated'],
  },
  {
    id: 'pricing',
    name: 'Pricing',
    fields: ['sku', 'base_price', 'discount', 'special_price', 'effective_date'],
  },
];

// In-memory data storage (in a real app, this would be a database)
let syncOperations: SyncOperation[] = [];
let syncHistory: SyncHistoryEntry[] = [];

// SyncService implementation
export class SyncService {
  /**
   * Get all sync operations with optional filtering
   */
  static async list(filters: FilterOptions): Promise<SyncOperation[]> {
    let result = [...syncOperations];
    
    // Apply filters
    if (filters.status) {
      result = result.filter(op => op.status === filters.status);
    }
    
    if (filters.source) {
      result = result.filter(op => op.source === filters.source);
    }
    
    if (filters.target) {
      result = result.filter(op => op.target === filters.target);
    }
    
    if (filters.dataType) {
      result = result.filter(op => op.dataType === filters.dataType);
    }
    
    if (filters.fromDate) {
      const fromDate = new Date(filters.fromDate);
      result = result.filter(op => new Date(op.createdAt) >= fromDate);
    }
    
    if (filters.toDate) {
      const toDate = new Date(filters.toDate);
      result = result.filter(op => new Date(op.createdAt) <= toDate);
    }
    
    // Sort by creation date descending
    result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    
    // Apply pagination
    const startIndex = (filters.page - 1) * filters.limit;
    return result.slice(startIndex, startIndex + filters.limit);
  }
  
  /**
   * Count total number of sync operations matching filters
   */
  static async count(filters: FilterOptions): Promise<number> {
    let result = [...syncOperations];
    
    if (filters.status) {
      result = result.filter(op => op.status === filters.status);
    }
    
    if (filters.source) {
      result = result.filter(op => op.source === filters.source);
    }
    
    if (filters.target) {
      result = result.filter(op => op.target === filters.target);
    }
    
    if (filters.dataType) {
      result = result.filter(op => op.dataType === filters.dataType);
    }
    
    if (filters.fromDate) {
      const fromDate = new Date(filters.fromDate);
      result = result.filter(op => new Date(op.createdAt) >= fromDate);
    }
    
    if (filters.toDate) {
      const toDate = new Date(filters.toDate);
      result = result.filter(op => new Date(op.createdAt) <= toDate);
    }
    
    return result.length;
  }
  
  /**
   * Get a specific sync operation by ID
   */
  static async get(id: string): Promise<SyncOperation | null> {
    const operation = syncOperations.find(op => op.id === id);
    return operation || null;
  }
  
  /**
   * Create a new sync operation
   */
  static async create(data: any): Promise<SyncOperation> {
    const id = uuidv4();
    const now = new Date().toISOString();
    
    // Determine initial status based on schedule
    let status: SyncStatus = 'pending';
    const scheduledTime = `${data.schedule.startDate}T${data.schedule.startTime}:00.000Z`;
    const scheduledDate = new Date(scheduledTime);
    
    if (scheduledDate > new Date()) {
      status = 'scheduled';
    }
    
    const newOperation: SyncOperation = {
      id,
      name: data.name,
      status,
      source: data.source,
      target: data.target,
      dataType: data.dataType,
      fields: data.fields,
      fieldMapping: data.fieldMapping,
      filters: data.filters,
      progress: 0,
      recordsTotal: 0,
      recordsProcessed: 0,
      recordsFailed: 0,
      startTime: scheduledTime,
      isRecurring: data.schedule.isRecurring,
      frequency: data.schedule.frequency,
      createdAt: now,
      updatedAt: now
    };
    
    syncOperations.push(newOperation);
    
    // Create initial history entry
    const historyEntry: SyncHistoryEntry = {
      id: uuidv4(),
      syncId: id,
      timestamp: now,
      event: 'sync_created',
      status: 'info',
      details: 'Sync operation created'
    };
    
    syncHistory.push(historyEntry);
    
    // Simulate starting a scheduled sync process
    if (status === 'pending') {
      setTimeout(() => {
        this.simulateSync(id);
      }, 1000);
    }
    
    return newOperation;
  }
  
  /**
   * Update a sync operation
   */
  static async update(id: string, data: any): Promise<SyncOperation> {
    const index = syncOperations.findIndex(op => op.id === id);
    if (index === -1) {
      throw new Error('Sync operation not found');
    }
    
    const operation = syncOperations[index];
    const now = new Date().toISOString();
    
    const updatedOperation = {
      ...operation,
      ...data,
      updatedAt: now
    };
    
    syncOperations[index] = updatedOperation;
    
    // Create history entry for the update
    const historyEntry: SyncHistoryEntry = {
      id: uuidv4(),
      syncId: id,
      timestamp: now,
      event: 'sync_updated',
      status: 'info',
      details: 'Sync operation updated'
    };
    
    syncHistory.push(historyEntry);
    
    return updatedOperation;
  }
  
  /**
   * Retry a failed sync operation
   */
  static async retry(id: string): Promise<SyncOperation> {
    const index = syncOperations.findIndex(op => op.id === id);
    if (index === -1) {
      throw new Error('Sync operation not found');
    }
    
    const operation = syncOperations[index];
    if (operation.status !== 'failed') {
      throw new Error('Only failed operations can be retried');
    }
    
    const now = new Date().toISOString();
    
    const updatedOperation = {
      ...operation,
      status: 'pending' as SyncStatus,
      progress: 0,
      recordsProcessed: 0,
      recordsFailed: 0,
      startTime: now,
      endTime: undefined,
      lastRunStatus: undefined,
      updatedAt: now
    };
    
    syncOperations[index] = updatedOperation;
    
    // Create history entry for retry
    const historyEntry: SyncHistoryEntry = {
      id: uuidv4(),
      syncId: id,
      timestamp: now,
      event: 'sync_retried',
      status: 'info',
      details: 'Sync operation retried'
    };
    
    syncHistory.push(historyEntry);
    
    // Simulate the retried sync process
    setTimeout(() => {
      this.simulateSync(id);
    }, 1000);
    
    return updatedOperation;
  }
  
  /**
   * Cancel an active sync operation
   */
  static async cancel(id: string): Promise<SyncOperation> {
    const index = syncOperations.findIndex(op => op.id === id);
    if (index === -1) {
      throw new Error('Sync operation not found');
    }
    
    const operation = syncOperations[index];
    if (operation.status !== 'active' && operation.status !== 'scheduled') {
      throw new Error('Only active or scheduled operations can be cancelled');
    }
    
    const now = new Date().toISOString();
    
    const updatedOperation = {
      ...operation,
      status: 'pending' as SyncStatus,
      updatedAt: now
    };
    
    syncOperations[index] = updatedOperation;
    
    // Create history entry for cancellation
    const historyEntry: SyncHistoryEntry = {
      id: uuidv4(),
      syncId: id,
      timestamp: now,
      event: 'sync_cancelled',
      status: 'warning',
      details: 'Sync operation cancelled by user'
    };
    
    syncHistory.push(historyEntry);
    
    return updatedOperation;
  }
  
  /**
   * Get history for a sync operation
   */
  static async getHistory(id: string): Promise<SyncHistoryEntry[]> {
    return syncHistory
      .filter(entry => entry.syncId === id)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }
  
  /**
   * Get available systems
   */
  static async getSystems(): Promise<SystemInfo[]> {
    return availableSystems;
  }
  
  /**
   * Get available data types
   */
  static async getDataTypes(): Promise<DataTypeInfo[]> {
    return dataTypes;
  }
  
  /**
   * Get metrics for sync operations
   */
  static async getMetrics(): Promise<MetricsData> {
    const totalOperations = syncOperations.length;
    const activeOperations = syncOperations.filter(op => op.status === 'active').length;
    const completedOperations = syncOperations.filter(op => op.status === 'completed').length;
    const failedOperations = syncOperations.filter(op => op.status === 'failed').length;
    
    // Calculate average duration for completed operations
    const completedOps = syncOperations.filter(op => op.status === 'completed' && op.endTime);
    let averageDuration = 0;
    
    if (completedOps.length > 0) {
      const totalDuration = completedOps.reduce((sum, op) => {
        const start = new Date(op.startTime).getTime();
        const end = new Date(op.endTime!).getTime();
        return sum + (end - start);
      }, 0);
      
      averageDuration = totalDuration / completedOps.length / 1000; // in seconds
    }
    
    // Calculate total records processed
    const totalRecordsProcessed = syncOperations.reduce((sum, op) => sum + op.recordsProcessed, 0);
    
    // Calculate success rate
    const totalRecords = syncOperations.reduce((sum, op) => sum + op.recordsProcessed + op.recordsFailed, 0);
    const successRate = totalRecords > 0 ? (totalRecordsProcessed / totalRecords) * 100 : 100;
    
    // Operations by system
    const operationsBySystem: Record<string, number> = {};
    syncOperations.forEach(op => {
      operationsBySystem[op.source] = (operationsBySystem[op.source] || 0) + 1;
      operationsBySystem[op.target] = (operationsBySystem[op.target] || 0) + 1;
    });
    
    // Operations by data type
    const operationsByDataType: Record<string, number> = {};
    syncOperations.forEach(op => {
      operationsByDataType[op.dataType] = (operationsByDataType[op.dataType] || 0) + 1;
    });
    
    return {
      totalOperations,
      activeOperations,
      completedOperations,
      failedOperations,
      averageDuration,
      totalRecordsProcessed,
      successRate,
      operationsBySystem,
      operationsByDataType
    };
  }
  
  /**
   * Simulate a sync process (for demo purposes)
   */
  private static simulateSync(id: string) {
    const index = syncOperations.findIndex(op => op.id === id);
    if (index === -1) return;
    
    const operation = syncOperations[index];
    const now = new Date().toISOString();
    
    // Set operation to active
    syncOperations[index] = {
      ...operation,
      status: 'active',
      progress: 0,
      updatedAt: now
    };
    
    // Create history entry for sync start
    syncHistory.push({
      id: uuidv4(),
      syncId: id,
      timestamp: now,
      event: 'sync_started',
      status: 'info',
      details: 'Sync operation started'
    });
    
    // Simulate a random number of total records
    const totalRecords = Math.floor(Math.random() * 1000) + 500;
    
    // Update total records
    syncOperations[index] = {
      ...syncOperations[index],
      recordsTotal: totalRecords
    };
    
    // Simulate progress updates
    let currentProgress = 0;
    let processedRecords = 0;
    let failedRecords = 0;
    
    const progressInterval = setInterval(() => {
      // Check if the operation still exists and is active
      const currentIndex = syncOperations.findIndex(op => op.id === id);
      if (currentIndex === -1 || syncOperations[currentIndex].status !== 'active') {
        clearInterval(progressInterval);
        return;
      }
      
      // Random progress increment (5-15%)
      const increment = Math.random() * 10 + 5;
      currentProgress = Math.min(currentProgress + increment, 100);
      
      // Calculate processed records based on progress
      const newProcessedRecords = Math.floor((currentProgress / 100) * totalRecords);
      
      // Simulate some failed records
      const newFailedRecords = Math.floor(Math.random() * 0.05 * (newProcessedRecords - processedRecords));
      
      processedRecords = newProcessedRecords - newFailedRecords;
      failedRecords += newFailedRecords;
      
      // Update operation
      syncOperations[currentIndex] = {
        ...syncOperations[currentIndex],
        progress: Math.round(currentProgress),
        recordsProcessed: processedRecords,
        recordsFailed: failedRecords,
        updatedAt: new Date().toISOString()
      };
      
      // Add progress history entry (but not too frequently)
      if (Math.random() > 0.7) {
        syncHistory.push({
          id: uuidv4(),
          syncId: id,
          timestamp: new Date().toISOString(),
          event: 'processing',
          status: 'info',
          details: `Processed ${Math.round(currentProgress)}% of records`,
          recordsProcessed: processedRecords,
          recordsTotal: totalRecords
        });
      }
      
      // Randomly add error entries
      if (newFailedRecords > 0 && Math.random() > 0.7) {
        syncHistory.push({
          id: uuidv4(),
          syncId: id,
          timestamp: new Date().toISOString(),
          event: 'error',
          status: 'warning',
          details: `Failed to process ${newFailedRecords} records due to validation errors`
        });
      }
      
      // When progress reaches 100%, complete the operation or fail it
      if (currentProgress >= 100) {
        clearInterval(progressInterval);
        
        // 10% chance of failing the operation
        const shouldFail = Math.random() < 0.1;
        
        if (shouldFail) {
          syncOperations[currentIndex] = {
            ...syncOperations[currentIndex],
            status: 'failed',
            endTime: new Date().toISOString(),
            lastRunStatus: 'Error: Connection to target system lost',
            updatedAt: new Date().toISOString()
          };
          
          syncHistory.push({
            id: uuidv4(),
            syncId: id,
            timestamp: new Date().toISOString(),
            event: 'sync_failed',
            status: 'error',
            details: 'Sync operation failed: Connection to target system lost'
          });
        } else {
          syncOperations[currentIndex] = {
            ...syncOperations[currentIndex],
            status: 'completed',
            progress: 100,
            endTime: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          };
          
          syncHistory.push({
            id: uuidv4(),
            syncId: id,
            timestamp: new Date().toISOString(),
            event: 'sync_completed',
            status: 'info',
            details: 'Sync operation completed successfully',
            recordsProcessed: processedRecords,
            recordsTotal: totalRecords
          });
        }
      }
    }, 1000);
  }
}