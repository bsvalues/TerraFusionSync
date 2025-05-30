#!/usr/bin/env python
"""
Script to generate the initial database migration using Alembic.
This creates a new migration file with the current database schema.
"""
import os
import sys
import subprocess
from pathlib import Path

# Get the absolute path to the terrafusion_sync directory
CURRENT_DIR = Path(__file__).parent.absolute()
os.chdir(CURRENT_DIR)

# Make sure alembic can find our models
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

def main():
    """Generate the initial Alembic migration."""
    print("Generating initial database migration...")
    
    # Run alembic command to generate migration
    try:
        # Use --autogenerate to automatically generate migration based on models
        subprocess.run(
            [
                "alembic", "revision", 
                "--autogenerate", 
                "-m", "create_initial_operational_tables"
            ],
            check=True
        )
        print("Initial migration generated successfully!")
        print("To apply this migration, run: alembic upgrade head")
    except subprocess.CalledProcessError as e:
        print(f"Error generating migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()