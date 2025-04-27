import { Request, Response, NextFunction } from 'express';

/**
 * Request logger middleware
 * Logs information about incoming requests
 */
export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();

  // Add response finish listener to calculate duration
  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = {
      timestamp: new Date().toISOString(),
      method: req.method,
      url: req.originalUrl || req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip || req.socket.remoteAddress,
      userAgent: req.get('user-agent') || 'unknown',
    };

    // For successful requests
    if (res.statusCode < 400) {
      console.log(`[INFO] ${JSON.stringify(logData)}`);
    } 
    // For client errors
    else if (res.statusCode < 500) {
      console.warn(`[WARN] ${JSON.stringify(logData)}`);
    } 
    // For server errors
    else {
      console.error(`[ERROR] ${JSON.stringify(logData)}`);
    }
  });

  next();
};

/**
 * Error handler middleware
 * Handles errors thrown during request processing
 */
export const errorHandler = (err: Error, req: Request, res: Response, next: NextFunction) => {
  // Log the error
  console.error('[ERROR] Unhandled exception:', err);

  // Determine error type and appropriate status code
  let statusCode = 500;
  let errorCode = 'INTERNAL_SERVER_ERROR';
  let errorMessage = 'An unexpected error occurred';

  // Check for specific error types and customize the response
  if (err.name === 'ValidationError') {
    statusCode = 400;
    errorCode = 'VALIDATION_ERROR';
    errorMessage = err.message || 'Invalid request data';
  } else if (err.name === 'NotFoundError') {
    statusCode = 404;
    errorCode = 'NOT_FOUND';
    errorMessage = err.message || 'Resource not found';
  } else if (err.name === 'UnauthorizedError') {
    statusCode = 401;
    errorCode = 'UNAUTHORIZED';
    errorMessage = 'Authentication required';
  } else if (err.name === 'ForbiddenError') {
    statusCode = 403;
    errorCode = 'FORBIDDEN';
    errorMessage = 'Access denied';
  }

  // Send error response
  return res.status(statusCode).json({
    data: null,
    error: {
      code: errorCode,
      message: errorMessage,
      details: process.env.NODE_ENV === 'development' ? err.stack : undefined
    },
    meta: {}
  });
};

/**
 * 404 Not Found handler middleware
 * Handles requests to non-existent routes
 */
export const notFoundHandler = (req: Request, res: Response) => {
  return res.status(404).json({
    data: null,
    error: {
      code: 'NOT_FOUND',
      message: `Route not found: ${req.method} ${req.originalUrl || req.url}`
    },
    meta: {}
  });
};

/**
 * Authentication middleware
 * Verifies authentication for protected routes
 * Currently a placeholder that allows all requests through
 */
export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // For now, we're not implementing actual authentication
  // This is a placeholder for future implementation
  
  // Add user info to request object for logging/auditing
  (req as any).user = {
    id: 'system',
    name: 'System User',
    roles: ['system']
  };
  
  next();
};