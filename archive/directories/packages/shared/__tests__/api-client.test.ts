import { api } from '../api/client';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET', () => {
    it('should make a GET request and return data', async () => {
      const mockResponse = {
        data: {
          data: [{ id: '1', name: 'Test' }],
          error: null,
          meta: {}
        }
      };
      
      mockedAxios.get.mockResolvedValueOnce(mockResponse);
      
      const result = await api.get('/test');
      
      expect(mockedAxios.get).toHaveBeenCalledWith('/test', undefined);
      expect(result).toEqual(mockResponse.data);
    });
    
    it('should handle errors', async () => {
      const error = {
        error: {
          code: 'TEST_ERROR',
          message: 'Test error'
        }
      };
      
      mockedAxios.get.mockRejectedValueOnce(error);
      
      try {
        await api.get('/test');
        fail('Should have thrown an error');
      } catch (e) {
        expect(e).toEqual(error);
      }
    });
  });
  
  describe('POST', () => {
    it('should make a POST request with data', async () => {
      const mockResponse = {
        data: {
          data: { id: '1', name: 'Created' },
          error: null,
          meta: {}
        }
      };
      
      const postData = { name: 'New item' };
      
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const result = await api.post('/test', postData);
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/test', postData, undefined);
      expect(result).toEqual(mockResponse.data);
    });
  });
  
  describe('PATCH', () => {
    it('should make a PATCH request with data', async () => {
      const mockResponse = {
        data: {
          data: { id: '1', name: 'Updated' },
          error: null,
          meta: {}
        }
      };
      
      const patchData = { name: 'Updated name' };
      
      mockedAxios.patch.mockResolvedValueOnce(mockResponse);
      
      const result = await api.patch('/test/1', patchData);
      
      expect(mockedAxios.patch).toHaveBeenCalledWith('/test/1', patchData, undefined);
      expect(result).toEqual(mockResponse.data);
    });
  });
  
  describe('DELETE', () => {
    it('should make a DELETE request', async () => {
      const mockResponse = {
        data: {
          data: true,
          error: null,
          meta: {}
        }
      };
      
      mockedAxios.delete.mockResolvedValueOnce(mockResponse);
      
      const result = await api.delete('/test/1');
      
      expect(mockedAxios.delete).toHaveBeenCalledWith('/test/1', undefined);
      expect(result).toEqual(mockResponse.data);
    });
  });
});