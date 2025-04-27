/**
 * Sync Service
 * Handles business logic for sync operations
 */

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
    url?: string;
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

export interface PaginatedResult<T> {
  items: T[];
  total: number;
}

// In-memory storage for development
let syncOperations: SyncOperation[] = [];
let syncHistory: SyncHistoryEntry[] = [];

// Initialize with sample data
initializeSampleData();

/**
 * Get all sync operations with optional filtering and pagination
 */
export async function getSyncOperations(
  page: number = 1,
  limit: number = 20,
  filters: Record<string, any> = {}
): Promise<PaginatedResult<SyncOperation>> {
  let filteredOperations = [...syncOperations];
  
  // Apply filters
  if (filters.status) {
    filteredOperations = filteredOperations.filter(op => op.status === filters.status);
  }
  
  if (filters.source) {
    filteredOperations = filteredOperations.filter(op => op.source === filters.source);
  }
  
  if (filters.target) {
    filteredOperations = filteredOperations.filter(op => op.target === filters.target);
  }
  
  if (filters.dataType) {
    filteredOperations = filteredOperations.filter(op => op.dataType === filters.dataType);
  }
  
  // Sort by updated date (most recent first)
  filteredOperations.sort((a, b) => 
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
  
  // Calculate pagination
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const paginatedOperations = filteredOperations.slice(startIndex, endIndex);
  
  return {
    items: paginatedOperations,
    total: filteredOperations.length
  };
}

/**
 * Get a specific sync operation by ID
 */
export async function getSyncOperation(id: string): Promise<SyncOperation | null> {
  const operation = syncOperations.find(op => op.id === id);
  return operation || null;
}

/**
 * Create a new sync operation
 */
export async function createSyncOperation(operation: SyncOperation): Promise<SyncOperation> {
  // Set default next run time if scheduled
  if (operation.schedule?.isRecurring) {
    operation.nextRunAt = calculateNextRunTime(operation.schedule);
  }
  
  syncOperations.push(operation);
  return operation;
}

/**
 * Update an existing sync operation
 */
export async function updateSyncOperation(
  id: string,
  updates: Partial<SyncOperation>
): Promise<SyncOperation> {
  const index = syncOperations.findIndex(op => op.id === id);
  
  if (index === -1) {
    throw new Error(`Sync operation with ID ${id} not found`);
  }
  
  // Update schedule-related fields
  if (updates.schedule) {
    updates.nextRunAt = calculateNextRunTime(updates.schedule);
  }
  
  // Merge with existing operation
  syncOperations[index] = {
    ...syncOperations[index],
    ...updates,
    updatedAt: new Date().toISOString()
  };
  
  return syncOperations[index];
}

/**
 * Delete a sync operation
 */
export async function deleteSyncOperation(id: string): Promise<void> {
  const index = syncOperations.findIndex(op => op.id === id);
  
  if (index === -1) {
    throw new Error(`Sync operation with ID ${id} not found`);
  }
  
  syncOperations.splice(index, 1);
  
  // Also remove history entries
  syncHistory = syncHistory.filter(h => h.syncOperationId !== id);
}

/**
 * Run a sync operation manually
 */
export async function runSyncOperation(id: string): Promise<SyncOperation> {
  const operation = await getSyncOperation(id);
  
  if (!operation) {
    throw new Error(`Sync operation with ID ${id} not found`);
  }
  
  if (operation.status === 'running') {
    throw new Error('This operation is already running');
  }
  
  // Update operation status to running
  await updateSyncOperation(id, { 
    status: 'running',
    lastRunAt: new Date().toISOString()
  });
  
  // Create history entry
  const historyEntry: SyncHistoryEntry = {
    id: Math.random().toString(36).substring(2, 15),
    syncOperationId: id,
    startTime: new Date().toISOString(),
    status: 'running',
    totalRecords: 0,
    processedRecords: 0,
    failedRecords: 0
  };
  
  syncHistory.push(historyEntry);
  
  // Simulate sync process
  setTimeout(() => {
    simulateSyncCompletion(id, historyEntry.id);
  }, 2000);
  
  return await getSyncOperation(id) as SyncOperation;
}

/**
 * Retry a failed sync operation
 */
export async function retrySyncOperation(id: string): Promise<SyncOperation> {
  const operation = await getSyncOperation(id);
  
  if (!operation) {
    throw new Error(`Sync operation with ID ${id} not found`);
  }
  
  if (operation.status !== 'failed') {
    throw new Error('Only failed operations can be retried');
  }
  
  // Reset error info
  await updateSyncOperation(id, {
    status: 'pending',
    errorMessage: undefined
  });
  
  // Run the operation
  return runSyncOperation(id);
}

/**
 * Get history entries for a sync operation
 */
export async function getSyncHistory(operationId: string): Promise<SyncHistoryEntry[]> {
  return syncHistory
    .filter(h => h.syncOperationId === operationId)
    .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime());
}

/**
 * Get all available systems
 */
export async function getAvailableSystems(): Promise<SystemInfo[]> {
  return [
    {
      id: 'erp',
      name: 'Enterprise Resource Planning',
      type: 'ERP',
      description: 'Core business management system',
      connectionDetails: {
        url: true,
        apiKey: true,
        useCredentials: false
      }
    },
    {
      id: 'crm',
      name: 'Customer Relationship Management',
      type: 'CRM',
      description: 'Customer management system',
      connectionDetails: {
        url: true,
        oauth: true,
        useCredentials: false
      }
    },
    {
      id: 'ecommerce',
      name: 'E-Commerce Platform',
      type: 'E-Commerce',
      description: 'Online store and product management',
      connectionDetails: {
        url: true,
        apiKey: true,
        useCredentials: false
      }
    },
    {
      id: 'warehouse',
      name: 'Warehouse Management System',
      type: 'WMS',
      description: 'Inventory and warehouse management',
      connectionDetails: {
        url: true,
        apiKey: false,
        useCredentials: true
      }
    },
    {
      id: 'marketplace',
      name: 'Marketplace Integration',
      type: 'Marketplace',
      description: 'Third-party marketplace connector',
      connectionDetails: {
        url: false,
        apiKey: true,
        oauth: false
      }
    }
  ];
}

/**
 * Get all available data types
 */
export async function getAvailableDataTypes(): Promise<DataTypeInfo[]> {
  return [
    {
      id: 'products',
      name: 'Products',
      description: 'Product catalog data',
      fields: [
        { name: 'sku', type: 'string', required: true, description: 'Unique product identifier' },
        { name: 'name', type: 'string', required: true, description: 'Product name' },
        { name: 'description', type: 'string', required: false, description: 'Product description' },
        { name: 'price', type: 'number', required: true, description: 'Product price' },
        { name: 'category', type: 'string', required: false, description: 'Product category' },
        { name: 'imageUrl', type: 'string', required: false, description: 'Product image URL' },
        { name: 'inStock', type: 'boolean', required: false, description: 'Product availability' }
      ]
    },
    {
      id: 'orders',
      name: 'Orders',
      description: 'Customer order data',
      fields: [
        { name: 'orderId', type: 'string', required: true, description: 'Unique order identifier' },
        { name: 'customerId', type: 'string', required: true, description: 'Customer identifier' },
        { name: 'orderDate', type: 'date', required: true, description: 'Order date' },
        { name: 'status', type: 'string', required: true, description: 'Order status' },
        { name: 'total', type: 'number', required: true, description: 'Order total' },
        { name: 'items', type: 'array', required: true, description: 'Order line items' },
        { name: 'shippingAddress', type: 'object', required: false, description: 'Shipping address' }
      ]
    },
    {
      id: 'customers',
      name: 'Customers',
      description: 'Customer profile data',
      fields: [
        { name: 'id', type: 'string', required: true, description: 'Unique customer identifier' },
        { name: 'name', type: 'string', required: true, description: 'Customer name' },
        { name: 'email', type: 'string', required: true, description: 'Customer email' },
        { name: 'phone', type: 'string', required: false, description: 'Customer phone' },
        { name: 'addresses', type: 'array', required: false, description: 'Customer addresses' },
        { name: 'createdAt', type: 'date', required: false, description: 'Customer creation date' },
        { name: 'lastOrderDate', type: 'date', required: false, description: 'Last order date' }
      ]
    },
    {
      id: 'inventory',
      name: 'Inventory',
      description: 'Inventory and stock data',
      fields: [
        { name: 'sku', type: 'string', required: true, description: 'Product SKU' },
        { name: 'quantity', type: 'number', required: true, description: 'Available quantity' },
        { name: 'warehouseId', type: 'string', required: false, description: 'Warehouse identifier' },
        { name: 'location', type: 'string', required: false, description: 'Storage location' },
        { name: 'lastUpdated', type: 'date', required: false, description: 'Last update timestamp' },
        { name: 'minStockLevel', type: 'number', required: false, description: 'Minimum stock level' },
        { name: 'onOrder', type: 'number', required: false, description: 'Quantity on order' }
      ]
    }
  ];
}

/**
 * Initialize sample data for development
 */
function initializeSampleData() {
  // Sample sync operations
  syncOperations = [
    {
      id: 'sync-1',
      name: 'Product Catalog Sync',
      description: 'Sync products from ERP to E-Commerce platform',
      source: 'erp',
      target: 'ecommerce',
      dataType: 'products',
      fields: ['sku', 'name', 'description', 'price', 'category', 'imageUrl'],
      fieldMapping: {
        sku: 'product_id',
        name: 'title',
        description: 'description',
        price: 'price',
        category: 'category',
        imageUrl: 'image'
      },
      status: 'completed',
      schedule: {
        frequency: 'daily',
        startDate: '2025-04-01',
        startTime: '01:00',
        isRecurring: true
      },
      lastRunAt: '2025-04-26T01:00:00Z',
      nextRunAt: '2025-04-27T01:00:00Z',
      createdAt: '2025-03-15T14:22:10Z',
      updatedAt: '2025-04-26T01:15:23Z',
      totalRecords: 1250,
      processedRecords: 1250,
      failedRecords: 0
    },
    {
      id: 'sync-2',
      name: 'Customer Data Integration',
      description: 'Sync customer data from CRM to E-Commerce',
      source: 'crm',
      target: 'ecommerce',
      dataType: 'customers',
      fields: ['id', 'name', 'email', 'phone', 'addresses'],
      fieldMapping: {
        id: 'customer_id',
        name: 'full_name',
        email: 'email_address',
        phone: 'phone_number',
        addresses: 'addresses'
      },
      status: 'failed',
      schedule: {
        frequency: 'weekly',
        startDate: '2025-04-05',
        startTime: '02:30',
        isRecurring: true,
        daysOfWeek: [6] // Saturday
      },
      lastRunAt: '2025-04-26T02:30:00Z',
      nextRunAt: '2025-05-03T02:30:00Z',
      createdAt: '2025-03-20T09:45:33Z',
      updatedAt: '2025-04-26T02:42:18Z',
      totalRecords: 3500,
      processedRecords: 2980,
      failedRecords: 520,
      errorMessage: 'Invalid email format for 520 customer records'
    },
    {
      id: 'sync-3',
      name: 'Inventory Update',
      description: 'Sync inventory data from Warehouse to Marketplace',
      source: 'warehouse',
      target: 'marketplace',
      dataType: 'inventory',
      fields: ['sku', 'quantity'],
      fieldMapping: {
        sku: 'product_id',
        quantity: 'stock'
      },
      status: 'scheduled',
      schedule: {
        frequency: 'daily',
        startDate: '2025-04-01',
        startTime: '04:00',
        isRecurring: true
      },
      nextRunAt: '2025-04-27T04:00:00Z',
      createdAt: '2025-04-01T15:30:00Z',
      updatedAt: '2025-04-26T04:15:12Z'
    }
  ];
  
  // Sample sync history
  syncHistory = [
    {
      id: 'history-1',
      syncOperationId: 'sync-1',
      startTime: '2025-04-26T01:00:00Z',
      endTime: '2025-04-26T01:15:23Z',
      status: 'completed',
      totalRecords: 1250,
      processedRecords: 1250,
      failedRecords: 0
    },
    {
      id: 'history-2',
      syncOperationId: 'sync-1',
      startTime: '2025-04-25T01:00:00Z',
      endTime: '2025-04-25T01:14:48Z',
      status: 'completed',
      totalRecords: 1245,
      processedRecords: 1245,
      failedRecords: 0
    },
    {
      id: 'history-3',
      syncOperationId: 'sync-2',
      startTime: '2025-04-26T02:30:00Z',
      endTime: '2025-04-26T02:42:18Z',
      status: 'failed',
      totalRecords: 3500,
      processedRecords: 2980,
      failedRecords: 520,
      errorDetails: {
        message: 'Invalid email format for 520 customer records',
        failedRecords: [
          { id: 'cust-1001', error: 'Invalid email format' },
          { id: 'cust-1002', error: 'Invalid email format' },
          // More records would be here
        ]
      }
    }
  ];
}

/**
 * Simulate completion of a sync operation
 * This would be replaced with actual sync logic in production
 */
async function simulateSyncCompletion(operationId: string, historyId: string) {
  // Get the current operation
  const operation = await getSyncOperation(operationId);
  if (!operation) return;
  
  // Find the history entry
  const historyIndex = syncHistory.findIndex(h => h.id === historyId);
  if (historyIndex === -1) return;
  
  // Randomly decide if operation succeeds or fails (80% success rate)
  const isSuccess = Math.random() > 0.2;
  
  // Update total records
  const totalRecords = Math.floor(Math.random() * 1000) + 100;
  
  if (isSuccess) {
    // Success case
    await updateSyncOperation(operationId, {
      status: 'completed',
      totalRecords,
      processedRecords: totalRecords,
      failedRecords: 0,
      errorMessage: undefined
    });
    
    // Update history
    syncHistory[historyIndex] = {
      ...syncHistory[historyIndex],
      endTime: new Date().toISOString(),
      status: 'completed',
      totalRecords,
      processedRecords: totalRecords,
      failedRecords: 0
    };
  } else {
    // Failure case
    const failedRecords = Math.floor(totalRecords * Math.random() * 0.5);
    const processedRecords = totalRecords - failedRecords;
    const errorMessage = 'Sync operation partially failed';
    
    await updateSyncOperation(operationId, {
      status: 'failed',
      totalRecords,
      processedRecords,
      failedRecords,
      errorMessage
    });
    
    // Update history
    syncHistory[historyIndex] = {
      ...syncHistory[historyIndex],
      endTime: new Date().toISOString(),
      status: 'failed',
      totalRecords,
      processedRecords,
      failedRecords,
      errorDetails: {
        message: errorMessage,
        failedRecords: [
          { id: 'sample-1', error: 'Processing error' },
          { id: 'sample-2', error: 'Validation failed' }
        ]
      }
    };
  }
  
  // If operation is recurring, update next run time
  if (operation.schedule?.isRecurring) {
    await updateSyncOperation(operationId, {
      nextRunAt: calculateNextRunTime(operation.schedule)
    });
  }
}

/**
 * Calculate the next run time based on schedule configuration
 */
function calculateNextRunTime(schedule: SyncOperation['schedule']): string {
  if (!schedule || !schedule.isRecurring) return '';
  
  const now = new Date();
  const [hour, minute] = schedule.startTime.split(':').map(part => parseInt(part, 10));
  let nextRun = new Date(now);
  
  // Set the time part
  nextRun.setHours(hour, minute, 0, 0);
  
  // If this time has already passed today, start from tomorrow
  if (nextRun <= now) {
    nextRun.setDate(nextRun.getDate() + 1);
  }
  
  switch (schedule.frequency) {
    case 'daily':
      // Already set for the next day above
      break;
      
    case 'weekly':
      if (schedule.daysOfWeek && schedule.daysOfWeek.length > 0) {
        // Find the next day that matches one in daysOfWeek
        // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        const currentDay = nextRun.getDay();
        const validDays = schedule.daysOfWeek.sort();
        
        let daysToAdd = 0;
        let found = false;
        
        for (let i = 0; i < 7; i++) {
          const checkDay = (currentDay + i) % 7;
          if (validDays.includes(checkDay)) {
            daysToAdd = i;
            found = true;
            break;
          }
        }
        
        if (found) {
          nextRun.setDate(nextRun.getDate() + daysToAdd);
        }
      } else {
        // Default to same day next week
        nextRun.setDate(nextRun.getDate() + 7);
      }
      break;
      
    case 'monthly':
      const targetDay = schedule.dayOfMonth || now.getDate();
      
      // Move to the next month
      nextRun.setMonth(nextRun.getMonth() + 1);
      
      // Set the target day, clamping to the last day of the month if needed
      const daysInMonth = new Date(nextRun.getFullYear(), nextRun.getMonth() + 1, 0).getDate();
      nextRun.setDate(Math.min(targetDay, daysInMonth));
      break;
  }
  
  return nextRun.toISOString();
}