import express, { Router } from 'express';
import { existsSync } from 'fs';
import path from 'path';

/**
 * Loads API routes from plugins dynamically.
 * 
 * This function looks for api routes in the plugin folders and registers them.
 * 
 * @param app Express application instance
 */
export function loadPluginRoutes(app: express.Application): void {
  try {
    // Define the path to the plugins directory
    const pluginsDir = path.resolve(__dirname, '../../plugins');
    
    console.log(`Loading plugin routes from: ${pluginsDir}`);
    
    // Look for marketplace-sync plugin first (our main plugin)
    const syncPluginPath = path.join(pluginsDir, 'marketplace-sync');
    
    // Check if the plugin exists
    if (existsSync(syncPluginPath)) {
      try {
        // Import the plugin's API router
        const { apiRouter } = require(path.join(syncPluginPath, 'src'));
        
        if (apiRouter && typeof apiRouter === 'function') {
          // Mount the router at the plugin-specific path
          app.use('/api/plugins/marketplace-sync', apiRouter);
          console.log('Mounted marketplace-sync plugin API at /api/plugins/marketplace-sync');
        } else {
          console.warn('Plugin marketplace-sync does not export a valid apiRouter');
        }
      } catch (err) {
        console.error(`Error loading marketplace-sync plugin routes:`, err);
      }
    } else {
      console.warn(`Plugin directory not found: ${syncPluginPath}`);
    }
    
    // This could be expanded to scan all plugin folders and mount their apiRouters
    // For now, we're just handling the marketplace-sync plugin
    
  } catch (error) {
    console.error('Error in loadPluginRoutes:', error);
  }
}