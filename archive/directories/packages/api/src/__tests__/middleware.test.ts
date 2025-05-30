import { Request, Response } from 'express';
import { 
  requestLogger, 
  errorHandler, 
  notFoundHandler, 
  authMiddleware 
} from '../middleware';

describe('API Middleware', () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let nextFunction: jest.Mock;

  beforeEach(() => {
    mockRequest = {
      method: 'GET',
      url: '/test',
      ip: '127.0.0.1',
      get: jest.fn().mockReturnValue('Test User Agent'),
      socket: {
        remoteAddress: '127.0.0.1'
      }
    };

    mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
      on: jest.fn().mockImplementation((event, callback) => {
        if (event === 'finish') {
          callback();
        }
        return mockResponse;
      }),
      statusCode: 200
    };

    nextFunction = jest.fn();

    // Mock console methods
    console.log = jest.fn();
    console.warn = jest.fn();
    console.error = jest.fn();
  });

  describe('requestLogger', () => {
    it('should log successful request info on finish', () => {
      requestLogger(
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      // Execute the finish callback
      expect(mockResponse.on).toHaveBeenCalledWith('finish', expect.any(Function));
      expect(nextFunction).toHaveBeenCalled();
      expect(console.log).toHaveBeenCalled();
    });

    it('should log client error request info on finish', () => {
      mockResponse.statusCode = 404;

      requestLogger(
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect(console.warn).toHaveBeenCalled();
    });

    it('should log server error request info on finish', () => {
      mockResponse.statusCode = 500;

      requestLogger(
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('errorHandler', () => {
    it('should handle generic errors with 500 status', () => {
      const error = new Error('Test error');
      
      errorHandler(
        error,
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect(mockResponse.status).toHaveBeenCalledWith(500);
      expect(mockResponse.json).toHaveBeenCalledWith({
        data: null,
        error: {
          code: 'INTERNAL_SERVER_ERROR',
          message: 'An unexpected error occurred',
          details: expect.any(String)
        },
        meta: {}
      });
    });

    it('should handle ValidationError with 400 status', () => {
      const error = new Error('Validation failed');
      error.name = 'ValidationError';
      
      errorHandler(
        error,
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect(mockResponse.status).toHaveBeenCalledWith(400);
      expect(mockResponse.json).toHaveBeenCalledWith({
        data: null,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Validation failed',
          details: expect.any(String)
        },
        meta: {}
      });
    });

    it('should handle NotFoundError with 404 status', () => {
      const error = new Error('Resource not found');
      error.name = 'NotFoundError';
      
      errorHandler(
        error,
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect(mockResponse.status).toHaveBeenCalledWith(404);
      expect(mockResponse.json).toHaveBeenCalledWith({
        data: null,
        error: {
          code: 'NOT_FOUND',
          message: 'Resource not found',
          details: expect.any(String)
        },
        meta: {}
      });
    });
  });

  describe('notFoundHandler', () => {
    it('should return 404 status with route info', () => {
      notFoundHandler(
        mockRequest as Request,
        mockResponse as Response
      );

      expect(mockResponse.status).toHaveBeenCalledWith(404);
      expect(mockResponse.json).toHaveBeenCalledWith({
        data: null,
        error: {
          code: 'NOT_FOUND',
          message: 'Route not found: GET /test'
        },
        meta: {}
      });
    });
  });

  describe('authMiddleware', () => {
    it('should add system user to request and call next', () => {
      authMiddleware(
        mockRequest as Request,
        mockResponse as Response,
        nextFunction
      );

      expect((mockRequest as any).user).toEqual({
        id: 'system',
        name: 'System User',
        roles: ['system']
      });
      
      expect(nextFunction).toHaveBeenCalled();
    });
  });
});