import axios, { AxiosRequestConfig } from 'axios';

// Default API configuration
const API_BASE_URL = process.env.API_URL || '/api';

// Create an API client instance with default config
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000,
});

// Response interface
export interface ApiResponse<T> {
  data: T;
  error: {
    code: string;
    message: string;
    details?: any;
  } | null;
  meta: Record<string, any>;
}

// Add request interceptor for auth tokens, etc.
axiosInstance.interceptors.request.use(
  (config) => {
    // You can add auth tokens here
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for global error handling
axiosInstance.interceptors.response.use(
  (response) => {
    // Pass through successful responses
    return response;
  },
  (error) => {
    // Handle API errors
    if (error.response) {
      // The server responded with a status code outside the 2xx range
      console.error('API Error:', error.response.status, error.response.data);
      
      // You can add global error handling here
      // if (error.response.status === 401) {
      //   // Handle authentication errors
      // }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Network Error:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error.response?.data || error);
  }
);

// API client interface
export const api = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const response = await axiosInstance.get<ApiResponse<T>>(url, config);
    return response.data;
  },
  
  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const response = await axiosInstance.post<ApiResponse<T>>(url, data, config);
    return response.data;
  },
  
  patch: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const response = await axiosInstance.patch<ApiResponse<T>>(url, data, config);
    return response.data;
  },
  
  put: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const response = await axiosInstance.put<ApiResponse<T>>(url, data, config);
    return response.data;
  },
  
  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const response = await axiosInstance.delete<ApiResponse<T>>(url, config);
    return response.data;
  }
};