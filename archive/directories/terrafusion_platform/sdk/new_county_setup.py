#!/usr/bin/env python3
import os
import argparse
import shutil
from pathlib import Path

# Define the root of the SDK, assuming this script is in terrafusion_platform/sdk/
SDK_ROOT = Path(__file__).parent.resolve()
TEMPLATES_DIR = SDK_ROOT / "templates"
# Define where county configurations will be stored, relative to project root
# Assuming project root is one level up from SDK_ROOT
PROJECT_ROOT = SDK_ROOT.parent 
COUNTY_CONFIGS_BASE_DIR = PROJECT_ROOT / "county_configs"

def main():
    parser = argparse.ArgumentParser(description="TerraFusion New County Setup CLI")
    parser.add_argument(
        "county_name", 
        type=str, 
        help="The name of the county (e.g., 'benton', 'franklin'). Used for directory and file naming."
    )
    parser.add_argument(
        "--legacy-system",
        type=str,
        default="PACS",
        help="Type of the legacy CAMA system for the county (e.g., PACS, TYLER, PATRIOT). Default: PACS"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing county configuration directory if it exists."
    )

    args = parser.parse_args()

    county_name_lower = args.county_name.lower().replace(" ", "_").replace("-", "_")
    county_name_title_case = args.county_name.replace("_", " ").replace("-", " ").title()
    county_name_upper = county_name_lower.upper()

    county_dir = COUNTY_CONFIGS_BASE_DIR / county_name_lower

    if county_dir.exists():
        if args.force:
            print(f"Warning: Directory {county_dir} already exists. Overwriting due to --force flag.")
            shutil.rmtree(county_dir)
        else:
            print(f"Error: Directory {county_dir} already exists. Use --force to overwrite.")
            return

    try:
        # Create directory structure
        mappings_dir = county_dir / "mappings"
        rbac_dir = county_dir / "rbac"
        mappings_dir.mkdir(parents=True, exist_ok=True)
        rbac_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory structure at: {county_dir}")

        # Template context
        context = {
            "county_name": county_name_lower,
            "county_name_title_case": county_name_title_case,
            "county_name_upper": county_name_upper,
            "legacy_system_type_placeholder": args.legacy_system.upper()
        }

        # Process .env template
        process_template(
            TEMPLATES_DIR / "county.env.template",
            county_dir / f"{county_name_lower}.env",
            context
        )

        # Process mappings.yaml template
        process_template(
            TEMPLATES_DIR / "mappings.yaml.template",
            mappings_dir / f"{county_name_lower}_mappings.yaml",
            context
        )

        # Process users.json template
        process_template(
            TEMPLATES_DIR / "users.json.template",
            rbac_dir / f"{county_name_lower}_users.json",
            context
        )

        print(f"\nSuccessfully scaffolded configuration for {county_name_title_case} County.")
        print(f"  Environment file: {county_dir / f'{county_name_lower}.env'}")
        print(f"  Mappings file:    {mappings_dir / f'{county_name_lower}_mappings.yaml'}")
        print(f"  RBAC users file:  {rbac_dir / f'{county_name_lower}_users.json'}")
        print("\nPlease review and customize these files with actual data for the county.")

    except Exception as e:
        print(f"An error occurred during scaffolding: {e}")
        # Clean up partially created directory if error occurs
        if county_dir.exists():
            # shutil.rmtree(county_dir) # Be cautious with auto-cleanup
            print(f"Partial setup at {county_dir} might exist due to error.")

def process_template(template_path: Path, output_path: Path, context: dict):
    """Reads a template file, replaces placeholders, and writes to output path."""
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Process all template formats
        for key, value in context.items():
            # Format 1: {{ key }} (Jinja2/Liquid style with spaces)
            template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))
            
            # Format 2: {{key}} (Jinja2/Liquid style without spaces)
            template_content = template_content.replace(f"{{{{{key}}}}}", str(value))
            
            # Format 3: ${key} (Shell/JavaScript style)
            template_content = template_content.replace(f"${{{key}}}", str(value))
            
            # Format 4: $key (Simple shell style)
            # Being careful here to avoid replacing parts of other words
            # So we only replace patterns that look like variable references
            lines = template_content.split('\n')
            for i, line in enumerate(lines):
                # Look for $varname pattern at word boundaries
                parts = []
                j = 0
                while j < len(line):
                    if line[j] == '$' and j + 1 < len(line) and (line[j+1].isalpha() or line[j+1] == '_'):
                        # Found potential variable
                        var_start = j + 1
                        var_end = var_start
                        while var_end < len(line) and (line[var_end].isalnum() or line[var_end] == '_'):
                            var_end += 1
                        
                        var_name = line[var_start:var_end]
                        if var_name == key:
                            parts.append(line[:j])
                            parts.append(str(value))
                            line = line[var_end:]
                            j = 0
                        else:
                            parts.append(line[:var_end])
                            line = line[var_end:]
                            j = 0
                    else:
                        j += 1
                if parts:
                    parts.append(line)
                    lines[i] = ''.join(parts)
            
            template_content = '\n'.join(lines)

        with open(output_path, 'w') as f:
            f.write(template_content)
        print(f"  Created: {output_path}")
    except FileNotFoundError:
        print(f"Error: Template file not found at {template_path}")
        raise
    except Exception as e:
        print(f"Error processing template {template_path} to {output_path}: {e}")
        raise

if __name__ == "__main__":
    # Create the base directory for county configs if it doesn't exist
    if not COUNTY_CONFIGS_BASE_DIR.exists():
        COUNTY_CONFIGS_BASE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created base county configurations directory: {COUNTY_CONFIGS_BASE_DIR}")
    main()