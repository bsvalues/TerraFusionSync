import { pluginInfo as marketplaceSync } from '@terrafusion/marketplace-sync';

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

// This registry holds references to all available plugins
const pluginRegistry: Record<string, Plugin> = {
  'marketplace-sync': marketplaceSync as unknown as Plugin,
};

export const getPlugins = (): Plugin[] => {
  return Object.values(pluginRegistry);
};

export const getPluginByName = (name: string): Plugin | undefined => {
  return pluginRegistry[name];
};

export const getPluginRoutes = (): PluginRoute[] => {
  return getPlugins().flatMap(plugin => plugin.routes);
};

export const getMenuItems = (): PluginRoute[] => {
  return getPluginRoutes().filter(route => route.menuItem);
};

export default pluginRegistry;