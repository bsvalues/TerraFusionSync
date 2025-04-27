// Export all components
export { SyncDashboard } from './components/SyncDashboard';
export { NewSyncWizard } from './components/NewSyncWizard';
export { SyncDetails } from './components/SyncDetails';

// Import the plugin manifest
import manifest from '../manifest.json';

// Export plugin information
export const pluginInfo = {
  ...manifest
};