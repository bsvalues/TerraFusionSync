import express from 'express';
import cors from 'cors';
import { loadPluginRoutes } from './plugin-loader';
import { requestLogger, errorHandler, notFoundHandler, authMiddleware } from './middleware';

// Create Express application
const app = express();

// Basic middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Custom middleware
app.use(requestLogger);
app.use(authMiddleware);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    data: {
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    },
    error: null,
    meta: {}
  });
});

// API documentation
app.get('/api', (req, res) => {
  res.json({
    data: {
      message: 'TerraFusion API Gateway',
      version: '1.0.0',
      endpoints: [
        { path: '/api/health', method: 'GET', description: 'Health check endpoint' },
        { path: '/api/plugins/marketplace-sync/v1/syncs', method: 'GET', description: 'List all sync operations' },
        { path: '/api/plugins/marketplace-sync/v1/syncs/:id', method: 'GET', description: 'Get a specific sync operation' },
        { path: '/api/plugins/marketplace-sync/v1/syncs', method: 'POST', description: 'Create a new sync operation' },
        { path: '/api/plugins/marketplace-sync/v1/systems', method: 'GET', description: 'Get available systems' },
        { path: '/api/plugins/marketplace-sync/v1/datatypes', method: 'GET', description: 'Get available data types' },
      ]
    },
    error: null,
    meta: {}
  });
});

// Load plugin routes
loadPluginRoutes(app);

// API version info
app.get('/api/version', (req, res) => {
  res.json({
    data: {
      version: '1.0.0',
      buildDate: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development'
    },
    error: null,
    meta: {}
  });
});

// 404 handler - must come after all valid routes
app.use(notFoundHandler);

// Error handler - must be the last middleware
app.use(errorHandler);

// Start server
const PORT = process.env.API_PORT || 4000;
app.listen(PORT, () => {
  console.log(`API server listening on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
  console.log(`API documentation: http://localhost:${PORT}/api`);
});

export default app;