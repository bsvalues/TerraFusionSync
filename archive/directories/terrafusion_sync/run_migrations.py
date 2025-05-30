#!/usr/bin/env python
"""
Script to run database migrations using Alembic.
This applies any pending migrations to bring the database schema up to date.
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
    """Run pending database migrations."""
    print("Running database migrations...")
    
    # Run alembic command to upgrade the database to the latest version
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database migrations completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()