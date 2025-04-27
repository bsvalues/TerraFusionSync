import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Default request timeout in milliseconds
const DEFAULT_TIMEOUT = 30000;

// Create an Axios instance with custom configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: '/', // Base URL for the API (can be changed at runtime)
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }
    
    // Add correlation ID for request tracing
    config.headers = {
      ...config.headers,
      'X-Correlation-ID': generateCorrelationId(),
    };
    
    return config;
  },
  (error: AxiosError) => {
    // Log request errors for debugging
    console.error('API request error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Process the response data
    return response;
  },
  (error: AxiosError) => {
    // Handle response errors
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status } = error.response;
      
      // Handle authentication errors
      if (status === 401) {
        console.warn('Authentication error, redirecting to login...');
        // Redirect to login page or trigger auth flow
        // window.location.href = '/login';
      }
      
      // Handle authorization errors
      if (status === 403) {
        console.warn('Authorization error, access denied');
        // Show permission denied screen or message
      }
      
      // Handle server errors
      if (status >= 500) {
        console.error('Server error:', error.response.data);
        // Show server error message
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Network error, no response received:', error.request);
      // Show network error message
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API client error:', error.message);
      // Show generic error message
    }
    
    // Pass the error to the calling code
    return Promise.reject(error);
  }
);

/**
 * Generate a random correlation ID for request tracing
 * 
 * @returns A unique correlation ID
 */
function generateCorrelationId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Configure API client settings
export const configureApiClient = (options: { baseURL?: string; timeout?: number }) => {
  if (options.baseURL) {
    apiClient.defaults.baseURL = options.baseURL;
  }
  
  if (options.timeout) {
    apiClient.defaults.timeout = options.timeout;
  }
};

export default apiClient;