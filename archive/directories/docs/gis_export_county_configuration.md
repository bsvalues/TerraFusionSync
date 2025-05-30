# GIS Export County Configuration Guide

This document explains how to configure and use county-specific settings for the GIS Export plugin in the TerraFusion Platform.

## Overview

The GIS Export plugin allows counties to download and export geographic data in various formats. The plugin is designed to be flexible and configurable on a per-county basis, allowing each county to have its own set of allowed export formats, default coordinate systems, and other parameters.

## County Configuration Files

County-specific configurations are stored in JSON files at the following location:

```
county_configs/{county_id}/{county_id}_config.json
```

For example, the configuration for Benton County, WA would be at:

```
county_configs/benton_wa/benton_wa_config.json
```

## GIS Export Configuration Schema

Within each county configuration file, the GIS Export settings are defined under the `plugin_settings.gis_export` section:

```json
{
  "county_id": "benton_wa",
  "county_friendly_name": "Benton County, WA",
  "plugin_settings": {
    "gis_export": {
      "available_formats": ["GeoJSON", "Shapefile", "KML"],
      "default_coordinate_system": "EPSG:4326",
      "max_export_area_sq_km": 750,
      "default_simplify_tolerance": 0.0001,
      "include_attributes_default": true
    }
  }
}
```

### Configuration Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `available_formats` | Array | List of supported export formats for this county | `["GeoJSON", "Shapefile", "KML"]` |
| `default_coordinate_system` | String | Default coordinate system to use for exports | `"EPSG:4326"` |
| `max_export_area_sq_km` | Number | Maximum allowed export area size in square kilometers | `500` |
| `default_simplify_tolerance` | Number | Default tolerance for geometry simplification | `0.0001` |
| `include_attributes_default` | Boolean | Whether to include attributes by default | `true` |

## Default Values

If a county configuration file doesn't exist or doesn't contain GIS Export settings, the following defaults are used:

```json
{
  "available_formats": ["GeoJSON", "Shapefile", "KML"],
  "default_coordinate_system": "EPSG:4326",
  "max_export_area_sq_km": 500,
  "default_simplify_tolerance": 0.0001,
  "include_attributes_default": true
}
```

## How It Works

When a GIS Export job is submitted through the API, the following happens:

1. The system validates that the requested export format is in the `available_formats` list for the county
2. If the request doesn't include parameters, the county's default parameters are automatically applied
3. The maximum export area is enforced based on the county configuration
4. The county's default coordinate system is used if not specified in the request

## Adding a New County Configuration

To add GIS Export configuration for a new county:

1. Create a new directory for the county under `county_configs/`
2. Create a configuration file named `{county_id}_config.json`
3. Add the GIS Export settings under the `plugin_settings.gis_export` section:

```json
{
  "county_id": "new_county_id",
  "county_friendly_name": "New County Name",
  "plugin_settings": {
    "gis_export": {
      "available_formats": ["GeoJSON", "Shapefile"],
      "default_coordinate_system": "EPSG:3857",
      "max_export_area_sq_km": 1000,
      "default_simplify_tolerance": 0.0005,
      "include_attributes_default": true
    }
  }
}
```

## API Endpoints

The following API endpoints use county-specific configurations:

- `POST /plugins/v1/gis-export/run` - Validates export format and applies default parameters
- `GET /plugins/v1/gis-export/formats/{county_id}` - Returns available formats for a county
- `GET /plugins/v1/gis-export/defaults/{county_id}` - Returns default parameters for a county

## Testing County Configurations

You can test county configurations using the provided test script:

```bash
python test_gis_export_county_config_standalone.py
```

This script verifies that:
- Available formats are correctly returned
- Format validation works properly
- Default parameters are applied correctly
- County-specific settings override global defaults

## Troubleshooting

Common issues:

- **Invalid Format Errors**: The requested export format is not in the county's `available_formats` list
- **Missing County Configuration**: Check that the county directory and configuration file exist
- **Parameter Validation Failures**: Check if the county has specific validation requirements

## Further Reading

- [GIS Export API Documentation](./gis_export_api.md)
- [Platform Administration Guide](./admin_guide.md)
- [County Configuration Schema](./county_config_schema.md)