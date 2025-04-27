import { Express } from 'express';
import fs from 'fs';
import path from 'path';

/**
 * Plugin manifest interface
 * Structure of a plugin's manifest.json file that defines its metadata and configuration
 */
interface PluginManifest {
  name: string;
  version: string;
  description: string;
  apiBasePath: string;
  entryPoint: string;
  dependencies?: string[];
  permissions?: string[];
}

/**
 * Load plugin manifest file
 * Reads and parses a plugin's manifest.json file
 */
function loadPluginManifest(pluginDir: string): PluginManifest | null {
  try {
    const manifestPath = path.join(pluginDir, 'manifest.json');
    if (!fs.existsSync(manifestPath)) {
      console.warn(`No manifest.json found in plugin directory: ${pluginDir}`);
      return null;
    }

    const manifestContent = fs.readFileSync(manifestPath, 'utf8');
    return JSON.parse(manifestContent) as PluginManifest;
  } catch (error) {
    console.error(`Error loading plugin manifest from ${pluginDir}:`, error);
    return null;
  }
}

/**
 * Load a plugin's routes
 * Dynamically imports a plugin's routes and registers them with the Express app
 */
function loadPluginRoutes(app: Express): void {
  try {
    // Hardcoded for marketplace-sync plugin during development
    // In a production system, this would scan the plugins directory
    const pluginDir = path.resolve(__dirname, '../../plugins/marketplace-sync');
    const manifest = loadPluginManifest(pluginDir);
    
    if (!manifest) {
      console.warn('Could not load marketplace-sync plugin manifest');
      return;
    }
    
    // Import the plugin's router
    // Note: In a more flexible setup, this would use the entryPoint from the manifest
    const pluginRouterPath = '../../plugins/marketplace-sync/src/api/routes';
    
    try {
      // Dynamic import
      import(pluginRouterPath)
        .then(module => {
          const pluginRouter = module.pluginRouter;
          if (!pluginRouter) {
            console.error(`Plugin ${manifest.name} does not export a 'pluginRouter'`);
            return;
          }
          
          // Register the router under the plugin's API base path
          app.use(`/api/plugins/${manifest.name}`, pluginRouter);
          console.log(`Loaded plugin routes for: ${manifest.name} at /api/plugins/${manifest.name}`);
        })
        .catch(importError => {
          console.error(`Failed to import plugin router from ${pluginRouterPath}:`, importError);
        });
    } catch (importError) {
      console.error(`Failed to import plugin router from ${pluginRouterPath}:`, importError);
    }
  } catch (error) {
    console.error('Error loading plugin routes:', error);
  }
}

export { loadPluginRoutes };