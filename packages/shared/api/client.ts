import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// API response type
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

// Configure API client defaults
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Add request interceptor for authentication tokens, etc.
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Get auth token from storage if it exists
    const token = localStorage.getItem('auth_token');
    
    // If token exists, add to headers
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for standard error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      
      return Promise.reject({
        error: {
          code: 'NETWORK_ERROR',
          message: 'Unable to connect to the server. Please check your internet connection.',
        }
      });
    }
    
    // Handle API errors with standard format
    if (error.response.status === 401) {
      // Handle unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      
      // If we have a custom event for unauthorized, dispatch it
      const unauthorizedEvent = new CustomEvent('auth:unauthorized');
      window.dispatchEvent(unauthorizedEvent);
    }
    
    // Log error for debugging
    console.error('API Error:', {
      status: error.response.status,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response.data
    });
    
    return Promise.reject(error.response.data);
  }
);

// Export for app-wide use
export default apiClient;

// API utilities
export const api = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.get<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      if (error && typeof error === 'object' && 'error' in error) {
        return error as ApiResponse<T>;
      }
      throw error;
    }
  },
  
  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.post<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      if (error && typeof error === 'object' && 'error' in error) {
        return error as ApiResponse<T>;
      }
      throw error;
    }
  },
  
  put: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.put<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      if (error && typeof error === 'object' && 'error' in error) {
        return error as ApiResponse<T>;
      }
      throw error;
    }
  },
  
  patch: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.patch<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      if (error && typeof error === 'object' && 'error' in error) {
        return error as ApiResponse<T>;
      }
      throw error;
    }
  },
  
  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.delete<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      if (error && typeof error === 'object' && 'error' in error) {
        return error as ApiResponse<T>;
      }
      throw error;
    }
  }
};