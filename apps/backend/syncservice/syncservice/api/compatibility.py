"""
Compatibility Matrix API for the SyncService.

This module provides endpoints for managing system compatibility configurations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from ..auth import verify_api_key

# Create router
router = APIRouter(
    prefix="/api/compatibility",
    tags=["Compatibility Matrix"],
    dependencies=[Depends(verify_api_key)]
)

# Logger
logger = logging.getLogger("syncservice.api.compatibility")

# Path to compatibility configurations
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "compatibility")

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)


@router.get("/systems")
async def get_available_systems():
    """
    Get all available system types with their capabilities.
    
    Returns:
        List of system type definitions with capabilities
    """
    # In a real implementation, this might come from a database
    systems = [
        {
            "id": "pacs",
            "name": "PACS",
            "description": "Property Assessment and Collection System",
            "type": "source",
            "icon": "database",
            "capabilities": ["property", "owner", "valuation", "tax"],
            "connections": ["odbc", "api", "file"],
        },
        {
            "id": "cama",
            "name": "CAMA",
            "description": "Computer-Assisted Mass Appraisal System",
            "type": "target",
            "icon": "home",
            "capabilities": ["property", "owner", "valuation", "tax", "appeals"],
            "connections": ["api", "database"],
        },
        {
            "id": "gis",
            "name": "GIS",
            "description": "Geographic Information System",
            "type": "both",
            "icon": "map",
            "capabilities": ["property", "spatial", "layers", "boundaries"],
            "connections": ["api", "shapefile", "database"],
        },
        {
            "id": "erp",
            "name": "ERP",
            "description": "Enterprise Resource Planning System",
            "type": "both",
            "icon": "building",
            "capabilities": ["finance", "hr", "inventory", "procurement"],
            "connections": ["api", "database", "file"],
        },
        {
            "id": "crm",
            "name": "CRM",
            "description": "Customer Relationship Management System",
            "type": "both",
            "icon": "users",
            "capabilities": ["customer", "interaction", "service", "marketing"],
            "connections": ["api", "database"],
        },
        {
            "id": "edms",
            "name": "EDMS",
            "description": "Electronic Document Management System",
            "type": "both",
            "icon": "file",
            "capabilities": ["document", "workflow", "scanning", "storage"],
            "connections": ["api", "file"],
        },
        {
            "id": "lims",
            "name": "LIMS",
            "description": "Land Information Management System",
            "type": "both",
            "icon": "landmark",
            "capabilities": ["property", "deed", "title", "zoning"],
            "connections": ["api", "database", "file"],
        },
    ]
    
    return {"systems": systems}


@router.get("/templates")
async def get_compatibility_templates():
    """
    Get predefined compatibility templates.
    
    Returns:
        List of predefined compatibility templates
    """
    templates = [
        {
            "id": "pacs-to-cama",
            "name": "PACS to CAMA Migration",
            "description": "Basic property and owner data migration from PACS to CAMA",
            "sourceSystem": "pacs",
            "targetSystem": "cama",
            "entityMappings": [
                {
                    "sourceEntity": "property",
                    "targetEntity": "property",
                    "compatibility": 0.9,
                    "transformationComplexity": "medium",
                },
                {
                    "sourceEntity": "owner",
                    "targetEntity": "owner",
                    "compatibility": 0.95,
                    "transformationComplexity": "low",
                },
                {
                    "sourceEntity": "valuation",
                    "targetEntity": "valuation",
                    "compatibility": 0.7,
                    "transformationComplexity": "high",
                },
            ],
        },
        {
            "id": "gis-to-cama",
            "name": "GIS to CAMA Integration",
            "description": "Spatial data integration from GIS to CAMA",
            "sourceSystem": "gis",
            "targetSystem": "cama",
            "entityMappings": [
                {
                    "sourceEntity": "property",
                    "targetEntity": "property",
                    "compatibility": 0.8,
                    "transformationComplexity": "medium",
                },
                {
                    "sourceEntity": "spatial",
                    "targetEntity": "property",
                    "compatibility": 0.85,
                    "transformationComplexity": "medium",
                },
                {
                    "sourceEntity": "boundaries",
                    "targetEntity": "property",
                    "compatibility": 0.75,
                    "transformationComplexity": "high",
                },
            ],
        },
        {
            "id": "erp-to-cama",
            "name": "ERP to CAMA Integration",
            "description": "Financial data integration from ERP to CAMA",
            "sourceSystem": "erp",
            "targetSystem": "cama",
            "entityMappings": [
                {
                    "sourceEntity": "finance",
                    "targetEntity": "tax",
                    "compatibility": 0.7,
                    "transformationComplexity": "high",
                },
            ],
        },
    ]
    
    return {"templates": templates}


@router.get("/configurations")
async def get_saved_configurations():
    """
    Get all saved compatibility configurations.
    
    Returns:
        List of saved compatibility configurations
    """
    try:
        configurations = []
        
        # List all json files in the config directory
        if os.path.exists(CONFIG_DIR):
            for filename in os.listdir(CONFIG_DIR):
                if filename.endswith(".json"):
                    file_path = os.path.join(CONFIG_DIR, filename)
                    with open(file_path, "r") as f:
                        config = json.load(f)
                        configurations.append(config)
        
        return {"configurations": configurations}
    except Exception as e:
        logger.error(f"Error loading configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading configurations: {str(e)}")


@router.get("/configuration/{config_id}")
async def get_configuration(config_id: str):
    """
    Get a specific compatibility configuration.
    
    Args:
        config_id: ID of the configuration to get
        
    Returns:
        Compatibility configuration
    """
    try:
        file_path = os.path.join(CONFIG_DIR, f"{config_id}.json")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
        
        with open(file_path, "r") as f:
            config = json.load(f)
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading configuration: {str(e)}")


@router.post("/configuration")
async def save_configuration(configuration: Dict[str, Any] = Body(...)):
    """
    Save a compatibility configuration.
    
    Args:
        configuration: Compatibility configuration to save
        
    Returns:
        Saved compatibility configuration
    """
    try:
        if "id" not in configuration:
            # Generate a new ID based on timestamp
            configuration["id"] = f"config-{int(datetime.now().timestamp())}"
        
        if "createdAt" not in configuration:
            configuration["createdAt"] = datetime.now().isoformat()
        
        configuration["updatedAt"] = datetime.now().isoformat()
        
        # Save to file
        file_path = os.path.join(CONFIG_DIR, f"{configuration['id']}.json")
        with open(file_path, "w") as f:
            json.dump(configuration, f, indent=2)
        
        return configuration
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")


@router.delete("/configuration/{config_id}")
async def delete_configuration(config_id: str):
    """
    Delete a compatibility configuration.
    
    Args:
        config_id: ID of the configuration to delete
        
    Returns:
        Deletion status
    """
    try:
        file_path = os.path.join(CONFIG_DIR, f"{config_id}.json")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
        
        os.remove(file_path)
        
        return {"status": "deleted", "id": config_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")


@router.get("/analyze")
async def analyze_compatibility(source_system: str, target_system: str):
    """
    Analyze compatibility between source and target systems.
    
    Args:
        source_system: Source system ID
        target_system: Target system ID
        
    Returns:
        Compatibility analysis
    """
    # In a real implementation, this would use a more sophisticated algorithm
    try:
        systems = (await get_available_systems())["systems"]
        
        source = next((s for s in systems if s["id"] == source_system), None)
        target = next((s for s in systems if s["id"] == target_system), None)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source system {source_system} not found")
        
        if not target:
            raise HTTPException(status_code=404, detail=f"Target system {target_system} not found")
        
        # Simple compatibility analysis
        compatible_entities = []
        for src_capability in source["capabilities"]:
            if src_capability in target["capabilities"]:
                # Calculate a pseudo-compatibility score
                compatibility = 0.7 + (0.3 * (
                    sum(1 for c in source["connections"] if c in target["connections"]) / 
                    max(len(source["connections"]), 1)
                ))
                
                compatible_entities.append({
                    "sourceEntity": src_capability,
                    "targetEntity": src_capability,
                    "compatibility": round(compatibility, 2),
                    "transformationComplexity": "medium" if compatibility < 0.8 else "low",
                })
        
        return {
            "sourceSystem": source,
            "targetSystem": target,
            "overallCompatibility": round(sum(e["compatibility"] for e in compatible_entities) / max(len(compatible_entities), 1), 2),
            "entityMappings": compatible_entities,
            "connectionOptions": [c for c in source["connections"] if c in target["connections"]],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing compatibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing compatibility: {str(e)}")