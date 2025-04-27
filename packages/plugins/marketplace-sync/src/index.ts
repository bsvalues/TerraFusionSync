// Export the components
export { SyncDashboard } from './components/SyncDashboard';
export { NewSyncWizard } from './components/NewSyncWizard';
export { SyncDetails } from './components/SyncDetails';

// Define plugin metadata
export const pluginInfo = {
  name: 'marketplace-sync',
  version: '0.1.0',
  description: 'Marketplace-style sync wizard for TerraFusion',
  routes: [
    {
      path: '/marketplace/sync',
      component: 'SyncDashboard',
      exact: true,
      name: 'Sync Marketplace',
      menuItem: true,
      menuGroup: 'Sync',
      menuIcon: 'sync-alt'
    },
    {
      path: '/marketplace/sync/new',
      component: 'NewSyncWizard',
      exact: true,
      name: 'New Sync',
      menuItem: false
    },
    {
      path: '/marketplace/sync/:id',
      component: 'SyncDetails',
      exact: true,
      name: 'Sync Details',
      menuItem: false
    }
  ]
};