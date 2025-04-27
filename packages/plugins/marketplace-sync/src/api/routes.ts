import { Router } from 'express';
import { z } from 'zod';
import { SyncService } from './services/sync-service';

export const pluginRouter = Router();

// Validation schemas
const CreateSyncSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  source: z.string().min(1, 'Source system is required'),
  target: z.string().min(1, 'Target system is required'),
  dataType: z.string().min(1, 'Data type is required'),
  fields: z.array(z.string()).min(1, 'At least one field must be selected'),
  fieldMapping: z.record(z.string()),
  filters: z.string().optional(),
  schedule: z.object({
    frequency: z.enum(['once', 'hourly', 'daily', 'weekly', 'monthly']),
    startDate: z.string(),
    startTime: z.string(),
    endDate: z.string().optional(),
    isRecurring: z.boolean()
  })
});

const UpdateSyncSchema = z.object({
  name: z.string().optional(),
  status: z.enum(['active', 'paused', 'cancelled']).optional(),
  schedule: z.object({
    frequency: z.enum(['once', 'hourly', 'daily', 'weekly', 'monthly']),
    startDate: z.string(),
    startTime: z.string(),
    endDate: z.string().optional(),
    isRecurring: z.boolean()
  }).optional()
});

const FilterSyncSchema = z.object({
  page: z.number().optional().default(1),
  limit: z.number().optional().default(20),
  status: z.enum(['active', 'completed', 'failed', 'pending', 'scheduled']).optional(),
  source: z.string().optional(),
  target: z.string().optional(),
  dataType: z.string().optional(),
  fromDate: z.string().optional(),
  toDate: z.string().optional()
});

// Standard response wrapper
const createResponse = (data: any, error: any = null, meta: any = {}) => {
  return {
    data,
    error,
    meta
  };
};

// Routes
// GET /api/plugins/marketplace-sync/v1/syncs - List all sync operations with filtering
pluginRouter.get('/v1/syncs', async (req, res) => {
  try {
    const { page = '1', limit = '20', status, source, target, dataType, fromDate, toDate } = req.query;
    
    const filters = {
      page: parseInt(page as string),
      limit: parseInt(limit as string),
      status: status as string,
      source: source as string,
      target: target as string,
      dataType: dataType as string,
      fromDate: fromDate as string,
      toDate: toDate as string
    };

    const validatedFilters = FilterSyncSchema.parse(filters);
    
    const result = await SyncService.list(validatedFilters);
    
    const totalCount = await SyncService.count(validatedFilters);
    const totalPages = Math.ceil(totalCount / validatedFilters.limit);
    
    res.json(createResponse(result, null, {
      pagination: {
        page: validatedFilters.page,
        limit: validatedFilters.limit,
        totalCount,
        totalPages
      }
    }));
  } catch (error) {
    console.error('Error listing sync operations:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve sync operations'
    }));
  }
});

// GET /api/plugins/marketplace-sync/v1/syncs/:id - Get a specific sync operation
pluginRouter.get('/v1/syncs/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const syncOperation = await SyncService.get(id);
    
    if (!syncOperation) {
      return res.status(404).json(createResponse(null, {
        code: 'NOT_FOUND',
        message: 'Sync operation not found'
      }));
    }
    
    res.json(createResponse(syncOperation));
  } catch (error) {
    console.error('Error retrieving sync operation:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve sync operation'
    }));
  }
});

// POST /api/plugins/marketplace-sync/v1/syncs - Create a new sync operation
pluginRouter.post('/v1/syncs', async (req, res) => {
  try {
    const parseResult = CreateSyncSchema.safeParse(req.body);
    
    if (!parseResult.success) {
      return res.status(400).json(createResponse(null, {
        code: 'VALIDATION_ERROR',
        message: 'Invalid sync operation data',
        details: parseResult.error.format()
      }));
    }
    
    const syncData = parseResult.data;
    const newSync = await SyncService.create(syncData);
    
    res.status(201).json(createResponse(newSync));
  } catch (error) {
    console.error('Error creating sync operation:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to create sync operation'
    }));
  }
});

// PATCH /api/plugins/marketplace-sync/v1/syncs/:id - Update a sync operation
pluginRouter.patch('/v1/syncs/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const parseResult = UpdateSyncSchema.safeParse(req.body);
    
    if (!parseResult.success) {
      return res.status(400).json(createResponse(null, {
        code: 'VALIDATION_ERROR',
        message: 'Invalid update data',
        details: parseResult.error.format()
      }));
    }
    
    const syncOperation = await SyncService.get(id);
    
    if (!syncOperation) {
      return res.status(404).json(createResponse(null, {
        code: 'NOT_FOUND',
        message: 'Sync operation not found'
      }));
    }
    
    const updatedSync = await SyncService.update(id, parseResult.data);
    
    res.json(createResponse(updatedSync));
  } catch (error) {
    console.error('Error updating sync operation:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to update sync operation'
    }));
  }
});

// POST /api/plugins/marketplace-sync/v1/syncs/:id/actions/retry - Retry a failed sync operation
pluginRouter.post('/v1/syncs/:id/actions/retry', async (req, res) => {
  try {
    const { id } = req.params;
    const syncOperation = await SyncService.get(id);
    
    if (!syncOperation) {
      return res.status(404).json(createResponse(null, {
        code: 'NOT_FOUND',
        message: 'Sync operation not found'
      }));
    }
    
    if (syncOperation.status !== 'failed') {
      return res.status(400).json(createResponse(null, {
        code: 'INVALID_OPERATION',
        message: 'Only failed operations can be retried'
      }));
    }
    
    const retriedSync = await SyncService.retry(id);
    
    res.json(createResponse(retriedSync));
  } catch (error) {
    console.error('Error retrying sync operation:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retry sync operation'
    }));
  }
});

// POST /api/plugins/marketplace-sync/v1/syncs/:id/actions/cancel - Cancel an active sync operation
pluginRouter.post('/v1/syncs/:id/actions/cancel', async (req, res) => {
  try {
    const { id } = req.params;
    const syncOperation = await SyncService.get(id);
    
    if (!syncOperation) {
      return res.status(404).json(createResponse(null, {
        code: 'NOT_FOUND',
        message: 'Sync operation not found'
      }));
    }
    
    if (syncOperation.status !== 'active' && syncOperation.status !== 'scheduled') {
      return res.status(400).json(createResponse(null, {
        code: 'INVALID_OPERATION',
        message: 'Only active or scheduled operations can be cancelled'
      }));
    }
    
    const cancelledSync = await SyncService.cancel(id);
    
    res.json(createResponse(cancelledSync));
  } catch (error) {
    console.error('Error cancelling sync operation:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to cancel sync operation'
    }));
  }
});

// GET /api/plugins/marketplace-sync/v1/syncs/:id/history - Get the history of a sync operation
pluginRouter.get('/v1/syncs/:id/history', async (req, res) => {
  try {
    const { id } = req.params;
    const syncOperation = await SyncService.get(id);
    
    if (!syncOperation) {
      return res.status(404).json(createResponse(null, {
        code: 'NOT_FOUND',
        message: 'Sync operation not found'
      }));
    }
    
    const history = await SyncService.getHistory(id);
    
    res.json(createResponse(history));
  } catch (error) {
    console.error('Error retrieving sync history:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve sync history'
    }));
  }
});

// GET /api/plugins/marketplace-sync/v1/systems - Get available systems
pluginRouter.get('/v1/systems', async (req, res) => {
  try {
    const systems = await SyncService.getSystems();
    res.json(createResponse(systems));
  } catch (error) {
    console.error('Error retrieving systems:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve systems'
    }));
  }
});

// GET /api/plugins/marketplace-sync/v1/datatypes - Get available data types
pluginRouter.get('/v1/datatypes', async (req, res) => {
  try {
    const dataTypes = await SyncService.getDataTypes();
    res.json(createResponse(dataTypes));
  } catch (error) {
    console.error('Error retrieving data types:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve data types'
    }));
  }
});

// GET /api/plugins/marketplace-sync/v1/metrics - Get sync operation metrics
pluginRouter.get('/v1/metrics', async (req, res) => {
  try {
    const metrics = await SyncService.getMetrics();
    res.json(createResponse(metrics));
  } catch (error) {
    console.error('Error retrieving metrics:', error);
    res.status(500).json(createResponse(null, {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Failed to retrieve metrics'
    }));
  }
});