import { SyncDashboard } from './components/SyncDashboard';
import { NewSyncWizard } from './components/NewSyncWizard';
import { SyncDetails } from './components/SyncDetails';

// Export hooks
export {
  useSyncList,
  useSyncOperation,
  useSyncHistory,
  useCreateSync,
  useUpdateSync,
  useRetrySync,
  useCancelSync,
  useSystems,
  useDataTypes,
  type SyncStatus,
  type SyncOperation,
  type SyncHistoryEntry,
  type SystemInfo,
  type DataTypeInfo,
  type FilterOptions,
  type PaginationMetadata,
  type ApiResponse
} from './hooks/useSyncOperations';

// Export components
export { SyncDashboard, NewSyncWizard, SyncDetails };

// Export API routes
export { pluginRouter as apiRouter } from './api/routes';

// Plugin information including routes
export const pluginInfo = {
  name: 'Marketplace Sync',
  version: '0.1.0',
  description: 'Synchronize data across marketplace systems.',
  routes: [
    {
      path: '/sync-dashboard',
      component: 'SyncDashboard',
      exact: true,
      name: 'Sync Dashboard',
      menuItem: true,
      menuGroup: 'Data Operations',
      menuIcon: 'sync-alt'
    },
    {
      path: '/sync-new',
      component: 'NewSyncWizard',
      exact: true,
      name: 'New Sync Operation',
      menuItem: false
    },
    {
      path: '/sync-details/:id',
      component: 'SyncDetails',
      exact: true,
      name: 'Sync Details',
      menuItem: false
    }
  ],
  apiEndpoints: [
    {
      path: '/api/plugins/marketplace-sync/v1/syncs',
      method: 'GET',
      description: 'List all sync operations'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs/:id',
      method: 'GET',
      description: 'Get a specific sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs',
      method: 'POST',
      description: 'Create a new sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs/:id',
      method: 'PATCH',
      description: 'Update a sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs/:id/actions/retry',
      method: 'POST',
      description: 'Retry a failed sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs/:id/actions/cancel',
      method: 'POST',
      description: 'Cancel an active sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/syncs/:id/history',
      method: 'GET',
      description: 'Get the history of a sync operation'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/systems',
      method: 'GET',
      description: 'Get available systems'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/datatypes',
      method: 'GET',
      description: 'Get available data types'
    },
    {
      path: '/api/plugins/marketplace-sync/v1/metrics',
      method: 'GET',
      description: 'Get sync operation metrics'
    }
  ]
};