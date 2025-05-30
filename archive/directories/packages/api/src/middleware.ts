import { Request, Response, NextFunction } from 'express';

/**
 * Middleware to log all API requests
 */
export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  
  // Log the request
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  
  // Add a listener for when the response is finished
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} ${res.statusCode} - ${duration}ms`);
  });
  
  next();
};

/**
 * Middleware to handle errors
 */
export const errorHandler = (err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('API Error:', err);
  
  // Determine if this is a known error type or a generic one
  if (err instanceof SyntaxError && 'body' in err) {
    // Handle JSON parsing errors
    return res.status(400).json({
      data: null,
      error: {
        code: 'INVALID_JSON',
        message: 'Invalid JSON payload',
      },
      meta: {}
    });
  }
  
  // Default error response
  res.status(500).json({
    data: null,
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected error occurred'
    },
    meta: {}
  });
};

/**
 * Middleware to handle 404 errors
 */
export const notFoundHandler = (req: Request, res: Response) => {
  res.status(404).json({
    data: null,
    error: {
      code: 'NOT_FOUND',
      message: 'The requested endpoint does not exist'
    },
    meta: {}
  });
};

/**
 * Middleware for basic authentication validation
 * In a real app, this would validate JWT tokens or API keys
 */
export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // Get the authorization header
  const authHeader = req.headers.authorization;
  
  // For now, we're not enforcing authentication
  // But this is where you would validate tokens
  
  // Example token validation logic (commented out):
  /*
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      data: null,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Authentication required'
      },
      meta: {}
    });
  }
  
  const token = authHeader.split(' ')[1];
  
  try {
    // Verify the token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    // Add user info to request
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({
      data: null,
      error: {
        code: 'INVALID_TOKEN',
        message: 'Invalid or expired token'
      },
      meta: {}
    });
  }
  */
  
  // For now, just pass through
  next();
};