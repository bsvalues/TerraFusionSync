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

// Export components
export { SyncDashboard } from './components/SyncDashboard';
export { NewSyncWizard } from './components/NewSyncWizard';
export { SyncDetails } from './components/SyncDetails';
export { SyncOperationsList } from './components/SyncOperationsList';

// Export plugin info for registration
export const pluginInfo = {
  name: 'Marketplace Sync',
  version: '0.1.0',
  description: 'Synchronize data between enterprise systems and marketplace platforms',
  routes: [
    {
      path: '/sync',
      component: 'SyncDashboard',
      exact: true,
      name: 'Sync Dashboard',
      menuItem: true,
      menuGroup: 'Data Operations',
      menuIcon: 'sync-alt'
    },
    {
      path: '/sync/new',
      component: 'NewSyncWizard',
      exact: true,
      name: 'New Sync Operation',
      menuItem: false
    },
    {
      path: '/sync/:id',
      component: 'SyncDetails',
      exact: true,
      name: 'Sync Details',
      menuItem: false
    }
  ]
};