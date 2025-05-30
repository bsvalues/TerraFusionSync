#!/usr/bin/env python3
"""
Test script for the CountyConfigManager and CountyConfig classes.
"""
import sys
from pathlib import Path

# Add the project root to sys.path
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent
sys.path.append(str(project_root))

from terrafusion_platform.sdk.county_config import CountyConfigManager, CountyConfig


def test_county_config_manager():
    """Test the CountyConfigManager class."""
    print("\n=== Testing CountyConfigManager ===")
    
    # Create a manager
    manager = CountyConfigManager()
    
    # List available counties
    counties = manager.list_available_counties()
    print(f"Available counties: {', '.join(counties)}")
    
    if not counties:
        print("No county configurations found.")
        return
    
    # Test loading each county
    for county in counties:
        try:
            config = manager.get_county_config(county)
            print(f"\n--- County: {config.get_county_name()} ---")
            print(f"County ID: {config.get_county_id()}")
            print(f"Legacy system type: {config.get_legacy_system_type()}")
            
            # Test getting environment variables
            print("\nEnvironment Variables:")
            for key in ["COUNTY_ID", "COUNTY_FRIENDLY_NAME", f"LEGACY_SYSTEM_TYPE_{county.upper()}"]:
                value = config.get_env_var(key)
                print(f"  {key}: {value}")
            
            # Test getting legacy connection parameters
            conn_params = config.get_legacy_connection_params()
            print("\nLegacy Connection Parameters:")
            for key, value in conn_params.items():
                print(f"  {key}: {value}")
            
            # Test getting field mappings
            print("\nField Mappings (top level):")
            for table in config.get_field_mappings().keys():
                print(f"  {table}")
            
            # Test getting users
            users = config.get_users()
            print(f"\nUsers ({len(users)}):")
            for user in users:
                print(f"  {user.get('username')}: {user.get('full_name')}")
            
            # Test getting role definitions
            roles = config.get_role_definitions()
            print(f"\nRoles ({len(roles)}):")
            for role, definition in roles.items():
                print(f"  {role}: {definition.get('description')}")
                
        except Exception as e:
            print(f"Error loading county '{county}': {e}")


if __name__ == "__main__":
    test_county_config_manager()