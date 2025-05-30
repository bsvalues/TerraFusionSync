"""
TerraFusion Platform - County Configuration Manager

This module provides utilities for loading and accessing county-specific configurations.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dotenv import dotenv_values


class CountyConfig:
    """
    Represents the configuration for a specific county.
    Provides access to environment variables, data mappings, and RBAC settings.
    """
    
    def __init__(self, county_name: str, config_base_dir: Optional[Path] = None):
        """
        Initialize a county configuration.
        
        Args:
            county_name: Name of the county (e.g., 'benton', 'franklin')
            config_base_dir: Base directory for county configs (defaults to PROJECT_ROOT/county_configs)
        """
        self.county_name = county_name.lower().replace(" ", "_").replace("-", "_")
        
        # Set base directory
        if config_base_dir is None:
            # Default to PROJECT_ROOT/county_configs
            sdk_dir = Path(__file__).parent.resolve()
            project_root = sdk_dir.parent.parent
            self.config_base_dir = project_root / "terrafusion_platform" / "county_configs"
        else:
            self.config_base_dir = config_base_dir
            
        # Set county directory
        self.county_dir = self.config_base_dir / self.county_name
        
        if not self.county_dir.exists():
            raise ValueError(f"County configuration for '{county_name}' not found at {self.county_dir}")
            
        # Set config file paths
        self.env_file = self.county_dir / f"{self.county_name}.env"
        self.mappings_file = self.county_dir / "mappings" / f"{self.county_name}_mappings.yaml"
        self.users_file = self.county_dir / "rbac" / f"{self.county_name}_users.json"
        
        # Validate file existence
        self._validate_files()
        
        # Load configurations
        self._load_configs()
    
    def _validate_files(self):
        """Validate that all required config files exist."""
        missing_files = []
        
        if not self.env_file.exists():
            missing_files.append(str(self.env_file))
        if not self.mappings_file.exists():
            missing_files.append(str(self.mappings_file))
        if not self.users_file.exists():
            missing_files.append(str(self.users_file))
            
        if missing_files:
            raise FileNotFoundError(f"Missing required configuration files for county '{self.county_name}': {', '.join(missing_files)}")
    
    def _load_configs(self):
        """Load all configuration files."""
        # Load environment variables
        self.env_vars = dotenv_values(self.env_file)
        
        # Load mappings configuration
        with open(self.mappings_file, 'r') as f:
            self.mappings = yaml.safe_load(f)
            
        # Load RBAC configuration
        with open(self.users_file, 'r') as f:
            self.rbac = json.load(f)
    
    def get_env_var(self, key: str, default: Any = None) -> Optional[str]:
        """
        Get an environment variable from the county configuration.
        
        Args:
            key: The environment variable key
            default: Default value if the key is not found
            
        Returns:
            The environment variable value or default
        """
        return self.env_vars.get(key, default)
    
    def get_county_id(self) -> str:
        """
        Get the county ID.
        
        Returns:
            The county ID
        """
        return self.get_env_var("COUNTY_ID", self.county_name) or self.county_name
    
    def get_county_name(self) -> str:
        """
        Get the friendly county name.
        
        Returns:
            The friendly county name (e.g., "Franklin County")
        """
        default = f"{self.county_name.title()} County"
        return self.get_env_var("COUNTY_FRIENDLY_NAME", default) or default
    
    def get_legacy_system_type(self) -> str:
        """
        Get the type of legacy system used by this county.
        
        Returns:
            The legacy system type (e.g., "PACS", "TYLER", "PATRIOT")
        """
        key = f"LEGACY_SYSTEM_TYPE_{self.county_name.upper()}"
        return self.get_env_var(key, "UNKNOWN") or "UNKNOWN"
    
    def get_legacy_connection_params(self) -> Dict[str, str]:
        """
        Get the legacy system connection parameters.
        
        Returns:
            Dictionary of connection parameters
        """
        county_upper = self.county_name.upper()
        prefix = f"PACS_DB_" # This might need to be adjusted based on system type
        
        connection_params = {}
        for key, value in self.env_vars.items():
            if key.startswith(prefix) and key.endswith(f"_{county_upper}_SOURCE"):
                # Extract param name from key (e.g., HOST from PACS_DB_HOST_FRANKLIN_SOURCE)
                param_name = key[len(prefix):-len(f"_{county_upper}_SOURCE")]
                connection_params[param_name.lower()] = value
                
        return connection_params
    
    def get_field_mappings(self, source_table: Optional[str] = None) -> Dict[str, Any]:
        """
        Get field mappings for the county.
        
        Args:
            source_table: Optional table name to filter mappings
            
        Returns:
            Dictionary of field mappings
        """
        if source_table:
            return self.mappings.get(source_table, {})
        return self.mappings
    
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get the county users configuration.
        
        Returns:
            List of user dictionaries
        """
        return self.rbac.get("users", [])
    
    def get_role_definitions(self) -> Dict[str, Any]:
        """
        Get the role definitions for the county.
        
        Returns:
            Dictionary of role definitions
        """
        return self.rbac.get("role_definitions", {})


class CountyConfigManager:
    """
    Manages access to county configurations.
    Provides a central point for accessing all county configurations.
    """
    
    def __init__(self, config_base_dir: Optional[Path] = None):
        """
        Initialize the county configuration manager.
        
        Args:
            config_base_dir: Base directory for county configs (defaults to PROJECT_ROOT/county_configs)
        """
        # Set base directory
        if config_base_dir is None:
            # Default to PROJECT_ROOT/county_configs
            sdk_dir = Path(__file__).parent.resolve()
            project_root = sdk_dir.parent.parent
            self.config_base_dir = project_root / "terrafusion_platform" / "county_configs"
        else:
            self.config_base_dir = config_base_dir
            
        # Cache for loaded county configurations
        self._county_configs: Dict[str, CountyConfig] = {}
    
    def get_county_config(self, county_name: str) -> CountyConfig:
        """
        Get a county configuration.
        
        Args:
            county_name: Name of the county
            
        Returns:
            CountyConfig for the specified county
            
        Raises:
            ValueError: If the county configuration does not exist
        """
        county_key = county_name.lower().replace(" ", "_").replace("-", "_")
        
        # Return from cache if available
        if county_key in self._county_configs:
            return self._county_configs[county_key]
        
        # Load and cache county config
        config = CountyConfig(county_name, self.config_base_dir)
        self._county_configs[county_key] = config
        
        return config
    
    def list_available_counties(self) -> List[str]:
        """
        List all available county configurations.
        
        Returns:
            List of county names with available configurations
        """
        if not self.config_base_dir.exists():
            return []
            
        return [
            d.name for d in self.config_base_dir.iterdir()
            if d.is_dir() and (d / f"{d.name}.env").exists()
        ]
    
    def reload_county_config(self, county_name: str) -> CountyConfig:
        """
        Force reload a county configuration.
        
        Args:
            county_name: Name of the county
            
        Returns:
            Reloaded CountyConfig
        """
        county_key = county_name.lower().replace(" ", "_").replace("-", "_")
        
        # Remove from cache if exists
        if county_key in self._county_configs:
            del self._county_configs[county_key]
            
        # Load and cache county config
        return self.get_county_config(county_name)