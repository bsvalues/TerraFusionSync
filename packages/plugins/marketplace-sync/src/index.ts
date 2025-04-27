/**
 * Marketplace Sync Plugin
 * 
 * This plugin provides functionality for synchronizing data between
 * enterprise systems and marketplace platforms.
 */

// Export main hook
export { useSyncOperations } from './hooks/useSyncOperations';

// Export API adapter
export * from '../../../shared/api';

// When components are implemented, export them here:
// export { SyncDashboard } from './components/SyncDashboard';
// export { NewSyncWizard } from './components/NewSyncWizard';
// export { SyncDetails } from './components/SyncDetails';