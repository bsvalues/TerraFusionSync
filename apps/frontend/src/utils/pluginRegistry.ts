import { pluginInfo as marketplaceSyncPlugin } from '@terrafusion/marketplace-sync';

export interface PluginRoute {
  path: string;
  component: string;
  exact: boolean;
  name: string;
  menuItem: boolean;
  menuGroup?: string;
  menuIcon?: string;
}

export interface Plugin {
  name: string;
  version: string;
  description: string;
  routes: PluginRoute[];
}

// Registry of all available plugins
export const plugins: Plugin[] = [
  marketplaceSyncPlugin,
  // Additional plugins would be registered here
];

// Get all available plugin routes
export const getAllPluginRoutes = (): PluginRoute[] => {
  return plugins.flatMap(plugin => plugin.routes);
};

// Get all menu items from plugin routes
export const getMenuItems = (): PluginRoute[] => {
  return getAllPluginRoutes().filter(route => route.menuItem);
};

// Get menu items grouped by their menu group
export const getMenuItemsByGroup = (): Record<string, PluginRoute[]> => {
  const menuItems = getMenuItems();
  return menuItems.reduce((acc, route) => {
    const group = route.menuGroup || 'Other';
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(route);
    return acc;
  }, {} as Record<string, PluginRoute[]>);
};