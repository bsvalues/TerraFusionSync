import express from 'express';
import cors from 'cors';
import { loadPluginRoutes } from './plugin-loader';

// Create Express application
const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});

// Load plugin routes
loadPluginRoutes(app);

// API documentation
app.get('/api', (req, res) => {
  res.json({
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
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: {
      code: 'NOT_FOUND',
      message: 'The requested endpoint does not exist'
    }
  });
});

// Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected error occurred'
    }
  });
});

// Start server
const PORT = process.env.API_PORT || 4000;
app.listen(PORT, () => {
  console.log(`API server listening on port ${PORT}`);
});

export default app;