# TerraFusion Platform SDK

This SDK provides tools for extending and integrating with the TerraFusion Platform.

## County Configuration Scaffolding

The primary feature of this SDK is the ability to generate configuration scaffolding for new counties. This creates a standardized directory structure with template files that can be customized for each county's specific needs.

### Using the CLI

The simplest way to create a new county configuration is to use the provided command-line interface:

```bash
# From the project root directory
./terrafusion-cli.py new-county <county_name> [options]

# Example:
./terrafusion-cli.py new-county benton --legacy-system PACS
```

### Options

- `--legacy-system`: Specify the type of legacy CAMA system (Default: PACS)
- `--force`: Overwrite existing county configuration if it exists

### Generated Directory Structure

The script will create a county-specific directory structure:

```
county_configs/
└── county_name/
    ├── county_name.env              # Environment variables specific to this county
    ├── mappings/
    │   └── county_name_mappings.yaml  # Field mappings from legacy system to TerraFusion
    └── rbac/
        └── county_name_users.json     # RBAC user definitions for this county
```

### Customizing Templates

After scaffolding, you should edit the generated files to:

1. Add actual database connection details for the county's legacy system
2. Adjust the field mappings to match the specific schema of the county's legacy system
3. Define the actual users, roles, and permissions for the county

## Template Reference

### county.env Template

Environment variables for county-specific connections and configurations.

### mappings.yaml Template

Defines how fields from the legacy system map to the TerraFusion canonical data model.

### users.json Template

Defines users, roles, and permissions for the county's instance.

## Adding New SDK Features

To add new SDK features:

1. Add a new module file in the `terrafusion_platform/sdk/` directory
2. Update the CLI in `terrafusion_platform/sdk/cli.py` to include the new functionality
3. Add documentation in this README file