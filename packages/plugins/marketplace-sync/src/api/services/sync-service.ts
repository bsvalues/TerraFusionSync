import { apiClient } from '../client';
import { SyncOperation } from '../../hooks/useSyncOperations';

// Base API path for sync operations
const API_PATH = '/api/sync-operations';

// Response type for API calls
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

/**
 * Get all sync operations
 * 
 * @param filters - Optional filters for the query
 * @returns Promise with the list of sync operations
 */
export const getSyncOperations = async (filters?: Record<string, string>): Promise<ApiResponse<SyncOperation[]>> => {
  try {
    const queryParams = filters 
      ? '?' + new URLSearchParams(filters).toString()
      : '';
    
    const response = await apiClient.get(`${API_PATH}${queryParams}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching sync operations:', error);
    throw error;
  }
};

/**
 * Get a single sync operation by ID
 * 
 * @param id - The ID of the sync operation
 * @returns Promise with the sync operation details
 */
export const getSyncOperation = async (id: string): Promise<ApiResponse<SyncOperation>> => {
  try {
    const response = await apiClient.get(`${API_PATH}/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching sync operation ${id}:`, error);
    throw error;
  }
};

/**
 * Create a new sync operation
 * 
 * @param data - The sync operation data
 * @returns Promise with the created sync operation
 */
export const createSyncOperation = async (data: Partial<SyncOperation>): Promise<ApiResponse<SyncOperation>> => {
  try {
    const response = await apiClient.post(API_PATH, data);
    return response.data;
  } catch (error) {
    console.error('Error creating sync operation:', error);
    throw error;
  }
};

/**
 * Update an existing sync operation
 * 
 * @param id - The ID of the sync operation to update
 * @param data - The updated sync operation data
 * @returns Promise with the updated sync operation
 */
export const updateSyncOperation = async (id: string, data: Partial<SyncOperation>): Promise<ApiResponse<SyncOperation>> => {
  try {
    const response = await apiClient.put(`${API_PATH}/${id}`, data);
    return response.data;
  } catch (error) {
    console.error(`Error updating sync operation ${id}:`, error);
    throw error;
  }
};

/**
 * Delete a sync operation
 * 
 * @param id - The ID of the sync operation to delete
 * @returns Promise with the deletion result
 */
export const deleteSyncOperation = async (id: string): Promise<ApiResponse> => {
  try {
    const response = await apiClient.delete(`${API_PATH}/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting sync operation ${id}:`, error);
    throw error;
  }
};

/**
 * Start a sync operation
 * 
 * @param id - The ID of the sync operation to start
 * @returns Promise with the started sync operation
 */
export const startSyncOperation = async (id: string): Promise<ApiResponse<SyncOperation>> => {
  try {
    const response = await apiClient.post(`${API_PATH}/${id}/start`);
    return response.data;
  } catch (error) {
    console.error(`Error starting sync operation ${id}:`, error);
    throw error;
  }
};

/**
 * Cancel a running sync operation
 * 
 * @param id - The ID of the sync operation to cancel
 * @returns Promise with the cancelled sync operation
 */
export const cancelSyncOperation = async (id: string): Promise<ApiResponse<SyncOperation>> => {
  try {
    const response = await apiClient.post(`${API_PATH}/${id}/cancel`);
    return response.data;
  } catch (error) {
    console.error(`Error cancelling sync operation ${id}:`, error);
    throw error;
  }
};

/**
 * Get validation results for a sync operation
 * 
 * @param id - The ID of the sync operation
 * @returns Promise with the validation results
 */
export const getValidationResults = async (id: string): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/${id}/validation`);
    return response.data;
  } catch (error) {
    console.error(`Error getting validation results for ${id}:`, error);
    throw error;
  }
};

/**
 * Run validation for a sync operation
 * 
 * @param id - The ID of the sync operation
 * @param options - Optional validation options
 * @returns Promise with the validation results
 */
export const runValidation = async (id: string, options?: Record<string, any>): Promise<ApiResponse> => {
  try {
    const response = await apiClient.post(`${API_PATH}/${id}/validation`, options || {});
    return response.data;
  } catch (error) {
    console.error(`Error running validation for ${id}:`, error);
    throw error;
  }
};

/**
 * Get sync operation history
 * 
 * @param id - The ID of the sync operation
 * @returns Promise with the history records
 */
export const getSyncOperationHistory = async (id: string): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/${id}/history`);
    return response.data;
  } catch (error) {
    console.error(`Error getting history for ${id}:`, error);
    throw error;
  }
};

/**
 * Get sync operation logs
 * 
 * @param id - The ID of the sync operation
 * @param limit - Optional limit for the number of log entries
 * @returns Promise with the log entries
 */
export const getSyncOperationLogs = async (id: string, limit?: number): Promise<ApiResponse> => {
  try {
    const queryParams = limit ? `?limit=${limit}` : '';
    const response = await apiClient.get(`${API_PATH}/${id}/logs${queryParams}`);
    return response.data;
  } catch (error) {
    console.error(`Error getting logs for ${id}:`, error);
    throw error;
  }
};

/**
 * Get available data sources for sync operations
 * 
 * @returns Promise with the available data sources
 */
export const getDataSources = async (): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/sources`);
    return response.data;
  } catch (error) {
    console.error('Error getting data sources:', error);
    throw error;
  }
};

/**
 * Get available data destinations for sync operations
 * 
 * @returns Promise with the available data destinations
 */
export const getDataDestinations = async (): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/destinations`);
    return response.data;
  } catch (error) {
    console.error('Error getting data destinations:', error);
    throw error;
  }
};

/**
 * Get schema for a specific data source
 * 
 * @param sourceId - The ID of the data source
 * @returns Promise with the schema information
 */
export const getSourceSchema = async (sourceId: string): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/sources/${sourceId}/schema`);
    return response.data;
  } catch (error) {
    console.error(`Error getting schema for source ${sourceId}:`, error);
    throw error;
  }
};

/**
 * Get schema for a specific data destination
 * 
 * @param destinationId - The ID of the data destination
 * @returns Promise with the schema information
 */
export const getDestinationSchema = async (destinationId: string): Promise<ApiResponse> => {
  try {
    const response = await apiClient.get(`${API_PATH}/destinations/${destinationId}/schema`);
    return response.data;
  } catch (error) {
    console.error(`Error getting schema for destination ${destinationId}:`, error);
    throw error;
  }
};