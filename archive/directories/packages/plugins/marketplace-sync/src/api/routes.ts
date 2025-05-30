import express, { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import * as syncService from './services/sync-service';
import { validateSyncOperation } from './validators/sync-validator';

// Create router instance with mergeParams option
const pluginRouter = express.Router({ mergeParams: true });

/**
 * Standard API response format for consistent responses across endpoints
 */
interface ApiResponse<T> {
  data: T;
  error: {
    code: string;
    message: string;
    details?: any;
  } | null;
  meta: Record<string, any>;
}

/**
 * Return a standardized API response
 */
function apiResponse<T>(
  data: T,
  error: { code: string; message: string; details?: any } | null = null,
  meta: Record<string, any> = {}
): ApiResponse<T> {
  return { data, error, meta };
}

/**
 * Format API error response
 */
function errorResponse(
  code: string,
  message: string,
  details?: any,
  statusCode: number = 500
): { statusCode: number; response: ApiResponse<null> } {
  return {
    statusCode,
    response: {
      data: null,
      error: { code, message, details },
      meta: {}
    }
  };
}

// Configure base path prefix for all routes in this plugin
pluginRouter.use('/v1', (req, res, next) => {
  console.log(`[marketplace-sync] ${req.method} ${req.path}`);
  next();
});

/**
 * GET /api/plugins/marketplace-sync/v1/syncs
 * List all sync operations with optional filtering and pagination
 */
pluginRouter.get('/v1/syncs', async (req: Request, res: Response) => {
  try {
    // Parse query parameters for filtering and pagination
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const status = req.query.status as string;
    const source = req.query.source as string;
    const target = req.query.target as string;
    const dataType = req.query.dataType as string;

    // Construct filter options
    const filters: any = {};
    if (status) filters.status = status;
    if (source) filters.source = source;
    if (target) filters.target = target;
    if (dataType) filters.dataType = dataType;

    // Get sync operations from service
    const { items, total } = await syncService.getSyncOperations(page, limit, filters);

    // Return paginated response
    return res.json(apiResponse(items, null, {
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    }));
  } catch (error: any) {
    console.error('Error fetching sync operations:', error);
    const { statusCode, response } = errorResponse(
      'FETCH_ERROR',
      'Failed to fetch sync operations',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * GET /api/plugins/marketplace-sync/v1/syncs/:id
 * Get a specific sync operation by ID
 */
pluginRouter.get('/v1/syncs/:id', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const syncOperation = await syncService.getSyncOperation(syncId);

    if (!syncOperation) {
      const { statusCode, response } = errorResponse(
        'NOT_FOUND',
        `Sync operation with ID ${syncId} not found`,
        null,
        404
      );
      return res.status(statusCode).json(response);
    }

    return res.json(apiResponse(syncOperation));
  } catch (error: any) {
    console.error(`Error fetching sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'FETCH_ERROR',
      'Failed to fetch sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * POST /api/plugins/marketplace-sync/v1/syncs
 * Create a new sync operation
 */
pluginRouter.post('/v1/syncs', async (req: Request, res: Response) => {
  try {
    // Validate request body
    const validationResult = validateSyncOperation(req.body);
    if (!validationResult.valid) {
      const { statusCode, response } = errorResponse(
        'VALIDATION_ERROR',
        'Invalid sync operation data',
        validationResult.errors,
        400
      );
      return res.status(statusCode).json(response);
    }

    // Create new sync operation with generated ID
    const newSyncOperation = {
      id: uuidv4(),
      ...req.body,
      status: 'pending',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Save through service
    const createdSync = await syncService.createSyncOperation(newSyncOperation);

    // Return created entity
    return res.status(201).json(apiResponse(createdSync));
  } catch (error: any) {
    console.error('Error creating sync operation:', error);
    const { statusCode, response } = errorResponse(
      'CREATE_ERROR',
      'Failed to create sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * PATCH /api/plugins/marketplace-sync/v1/syncs/:id
 * Update an existing sync operation
 */
pluginRouter.patch('/v1/syncs/:id', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const existingSync = await syncService.getSyncOperation(syncId);

    if (!existingSync) {
      const { statusCode, response } = errorResponse(
        'NOT_FOUND',
        `Sync operation with ID ${syncId} not found`,
        null,
        404
      );
      return res.status(statusCode).json(response);
    }

    // Don't allow updating certain fields
    const { id, createdAt, ...updateableFields } = req.body;

    // Merge with existing and update timestamp
    const updatedSync = {
      ...existingSync,
      ...updateableFields,
      updatedAt: new Date().toISOString()
    };

    // Save through service
    const result = await syncService.updateSyncOperation(syncId, updatedSync);

    return res.json(apiResponse(result));
  } catch (error: any) {
    console.error(`Error updating sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'UPDATE_ERROR',
      'Failed to update sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * DELETE /api/plugins/marketplace-sync/v1/syncs/:id
 * Delete a sync operation
 */
pluginRouter.delete('/v1/syncs/:id', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const existingSync = await syncService.getSyncOperation(syncId);

    if (!existingSync) {
      const { statusCode, response } = errorResponse(
        'NOT_FOUND',
        `Sync operation with ID ${syncId} not found`,
        null,
        404
      );
      return res.status(statusCode).json(response);
    }

    // Delete through service
    await syncService.deleteSyncOperation(syncId);

    // Return success with no content
    return res.status(204).end();
  } catch (error: any) {
    console.error(`Error deleting sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'DELETE_ERROR',
      'Failed to delete sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * POST /api/plugins/marketplace-sync/v1/syncs/:id/actions/run
 * Run a sync operation manually
 */
pluginRouter.post('/v1/syncs/:id/actions/run', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const existingSync = await syncService.getSyncOperation(syncId);

    if (!existingSync) {
      const { statusCode, response } = errorResponse(
        'NOT_FOUND',
        `Sync operation with ID ${syncId} not found`,
        null,
        404
      );
      return res.status(statusCode).json(response);
    }

    // Trigger sync run through service
    const result = await syncService.runSyncOperation(syncId);

    return res.json(apiResponse(result));
  } catch (error: any) {
    console.error(`Error running sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'RUN_ERROR',
      'Failed to run sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * POST /api/plugins/marketplace-sync/v1/syncs/:id/actions/retry
 * Retry a failed sync operation
 */
pluginRouter.post('/v1/syncs/:id/actions/retry', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const existingSync = await syncService.getSyncOperation(syncId);

    if (!existingSync) {
      const { statusCode, response } = errorResponse(
        'NOT_FOUND',
        `Sync operation with ID ${syncId} not found`,
        null,
        404
      );
      return res.status(statusCode).json(response);
    }

    if (existingSync.status !== 'failed') {
      const { statusCode, response } = errorResponse(
        'INVALID_OPERATION',
        'Only failed sync operations can be retried',
        null,
        400
      );
      return res.status(statusCode).json(response);
    }

    // Retry sync through service
    const result = await syncService.retrySyncOperation(syncId);

    return res.json(apiResponse(result));
  } catch (error: any) {
    console.error(`Error retrying sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'RETRY_ERROR',
      'Failed to retry sync operation',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * GET /api/plugins/marketplace-sync/v1/systems
 * Get all available systems
 */
pluginRouter.get('/v1/systems', async (req, res) => {
  try {
    const systems = await syncService.getAvailableSystems();
    return res.json(apiResponse(systems));
  } catch (error: any) {
    console.error('Error fetching available systems:', error);
    const { statusCode, response } = errorResponse(
      'SYSTEMS_ERROR',
      'Failed to fetch available systems',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * GET /api/plugins/marketplace-sync/v1/datatypes
 * Get all available data types
 */
pluginRouter.get('/v1/datatypes', async (req, res) => {
  try {
    const dataTypes = await syncService.getAvailableDataTypes();
    return res.json(apiResponse(dataTypes));
  } catch (error: any) {
    console.error('Error fetching available data types:', error);
    const { statusCode, response } = errorResponse(
      'DATATYPES_ERROR',
      'Failed to fetch available data types',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

/**
 * GET /api/plugins/marketplace-sync/v1/syncs/:id/history
 * Get history entries for a specific sync operation
 */
pluginRouter.get('/v1/syncs/:id/history', async (req: Request<{ id: string }>, res: Response) => {
  try {
    const syncId = req.params.id;
    const history = await syncService.getSyncHistory(syncId);
    
    return res.json(apiResponse(history));
  } catch (error: any) {
    console.error(`Error fetching history for sync operation ${req.params.id}:`, error);
    const { statusCode, response } = errorResponse(
      'HISTORY_ERROR',
      'Failed to fetch sync operation history',
      error.message,
      500
    );
    return res.status(statusCode).json(response);
  }
});

export { pluginRouter };