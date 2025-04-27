import { SyncDashboard } from './components/SyncDashboard';
import { NewSyncWizard } from './components/NewSyncWizard';
import { SyncDetails } from './components/SyncDetails';

// Export components
export { SyncDashboard, NewSyncWizard, SyncDetails };

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
  ]
};