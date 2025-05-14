"""
TerraFusion SyncService - GIS Export Plugin - County Configuration

This module provides functionality to load and apply county-specific configurations
for the GIS Export plugin.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configurations to use if county-specific ones are not available
DEFAULT_GIS_EXPORT_CONFIG = {
    "available_formats": ["GeoJSON", "Shapefile", "KML"],
    "default_coordinate_system": "EPSG:4326",
    "max_export_area_sq_km": 500,  # Maximum area size in square kilometers
    "default_simplify_tolerance": 0.0001,
    "include_attributes_default": True
}

class CountyGisExportConfig:
    """
    Manages county-specific GIS Export plugin configurations.
    """
    
    def __init__(self):
        """Initialize the county configuration handler."""
        self.configs_cache = {}  # Cache for loaded configurations
        self.county_config_dir = os.environ.get("COUNTY_CONFIG_DIR", "county_configs")
    
    def get_config(self, county_id: str) -> Dict[str, Any]:
        """
        Get the GIS Export configuration for a specific county.
        
        Args:
            county_id: The ID of the county (e.g., "benton_wa")
            
        Returns:
            Dictionary containing GIS Export configuration for the county
        """
        # Return from cache if available
        if county_id in self.configs_cache:
            return self.configs_cache[county_id]
        
        # Try to load county-specific configuration
        config = self._load_county_config(county_id)
        
        # Cache the configuration
        self.configs_cache[county_id] = config
        
        return config
    
    def _load_county_config(self, county_id: str) -> Dict[str, Any]:
        """
        Load configuration for a specific county from its JSON config file.
        
        Args:
            county_id: The ID of the county (e.g., "benton_wa")
            
        Returns:
            Dictionary containing GIS Export configuration for the county
        """
        try:
            # Construct path to county config file
            config_path = Path(self.county_config_dir) / county_id / f"{county_id}_config.json"
            
            logger.info(f"Loading GIS Export configuration for county {county_id} from {config_path}")
            
            # Check if file exists
            if not config_path.exists():
                logger.warning(f"No configuration file found for county {county_id} at {config_path}")
                return DEFAULT_GIS_EXPORT_CONFIG
            
            # Load and parse JSON config
            with open(config_path, 'r') as config_file:
                county_config = json.load(config_file)
            
            # Extract GIS Export specific configuration
            if "plugin_settings" in county_config and "gis_export" in county_config["plugin_settings"]:
                gis_export_config = county_config["plugin_settings"]["gis_export"]
                
                # Merge with defaults for any missing settings
                for key, value in DEFAULT_GIS_EXPORT_CONFIG.items():
                    if key not in gis_export_config:
                        gis_export_config[key] = value
                
                logger.info(f"Successfully loaded GIS Export configuration for county {county_id}")
                return gis_export_config
            else:
                logger.warning(f"No GIS Export configuration found in county config for {county_id}")
                return DEFAULT_GIS_EXPORT_CONFIG
                
        except Exception as e:
            logger.error(f"Error loading county configuration for {county_id}: {e}", exc_info=True)
            return DEFAULT_GIS_EXPORT_CONFIG
    
    def get_available_formats(self, county_id: str) -> List[str]:
        """
        Get list of available export formats for a county.
        
        Args:
            county_id: The ID of the county
            
        Returns:
            List of available export formats
        """
        config = self.get_config(county_id)
        return config.get("available_formats", DEFAULT_GIS_EXPORT_CONFIG["available_formats"])
    
    def get_default_coordinate_system(self, county_id: str) -> str:
        """
        Get default coordinate system for a county.
        
        Args:
            county_id: The ID of the county
            
        Returns:
            Default coordinate system (e.g., "EPSG:4326")
        """
        config = self.get_config(county_id)
        return config.get("default_coordinate_system", DEFAULT_GIS_EXPORT_CONFIG["default_coordinate_system"])
    
    def validate_export_format(self, county_id: str, format_name: str) -> bool:
        """
        Validate that the requested export format is supported for the county.
        
        Args:
            county_id: The ID of the county
            format_name: The export format to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        valid_formats = self.get_available_formats(county_id)
        return format_name in valid_formats
    
    def get_max_export_area(self, county_id: str) -> float:
        """
        Get maximum allowed export area size in square kilometers.
        
        Args:
            county_id: The ID of the county
            
        Returns:
            Maximum area size in square kilometers
        """
        config = self.get_config(county_id)
        return config.get("max_export_area_sq_km", DEFAULT_GIS_EXPORT_CONFIG["max_export_area_sq_km"])
    
    def get_default_parameters(self, county_id: str) -> Dict[str, Any]:
        """
        Get default export parameters for a county.
        
        Args:
            county_id: The ID of the county
            
        Returns:
            Dictionary of default parameters
        """
        config = self.get_config(county_id)
        return {
            "simplify_tolerance": config.get("default_simplify_tolerance", 
                                            DEFAULT_GIS_EXPORT_CONFIG["default_simplify_tolerance"]),
            "include_attributes": config.get("include_attributes_default", 
                                            DEFAULT_GIS_EXPORT_CONFIG["include_attributes_default"]),
            "coordinate_system": self.get_default_coordinate_system(county_id)
        }

# Create singleton instance
county_config = CountyGisExportConfig()

def get_county_config() -> CountyGisExportConfig:
    """Get the GIS Export county configuration handler."""
    return county_config