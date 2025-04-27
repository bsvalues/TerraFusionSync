import { 
  SyncDashboard,
  NewSyncWizard,
  SyncDetails 
} from '@terrafusion/marketplace-sync';

// This mapping connects route component string names to the actual imported components
const componentMapping: Record<string, React.ComponentType<any>> = {
  // Marketplace Sync Plugin components
  'SyncDashboard': SyncDashboard,
  'NewSyncWizard': NewSyncWizard,
  'SyncDetails': SyncDetails,
};

export const getComponentByName = (name: string): React.ComponentType<any> | null => {
  return componentMapping[name] || null;
};

export default componentMapping;