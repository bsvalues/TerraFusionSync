#!/usr/bin/env python3
"""
Fix the GIS Export integration test files to use the correct URL format.
This script updates:
1. Dashes vs underscores in URLs: gis-export instead of gis_export
2. Parameter names in the URLs: job_id_param instead of job_id
"""

import os

def update_file(file_path):
    """Update URL paths and parameter names in the specified file."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Only replace in URL strings, not in function or variable names
    content = content.replace('/plugins/v1/gis_export', '/plugins/v1/gis-export')
    content = content.replace('BASE_URL = "http://localhost:8080/plugins/v1/gis_export"', 
                            'BASE_URL = "http://localhost:8080/plugins/v1/gis-export"')
    content = content.replace('BASE_URL = f"http://{args.host}:{args.port}/plugins/v1/gis_export"',
                            'BASE_URL = f"http://{args.host}:{args.port}/plugins/v1/gis-export"')
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Updated {file_path}")

def main():
    """Main entry point."""
    # Files to update
    files = [
        'isolated_test_gis_export_end_to_end.py',
        'run_gis_export_tests.py',
        'tests/plugins/test_gis_export_end_to_end.py',
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            update_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()