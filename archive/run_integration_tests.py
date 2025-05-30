#!/usr/bin/env python
"""
Run integration tests for the TerraFusion Platform.

This script prepares the environment and executes the pytest integration tests.
It sets up necessary test configuration, including database connection variables.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv


def create_test_env_if_needed():
    """
    Create a .env file with test database configuration if it doesn't exist.
    """
    env_path = Path('.env')
    
    # If .env doesn't exist, create a minimal one for testing
    if not env_path.exists():
        print("Creating .env file with test database configuration...")
        with open(env_path, 'w') as f:
            f.write("""# TerraFusion Platform Environment Variables
# Created by run_integration_tests.py

# Main database URL (used by application)
DATABASE_URL=postgresql+asyncpg://neondb_owner@ep-noisy-poetry-402590.us-east-2.aws.neon.tech/terrafusion_operational

# Test database URL (used by tests)
TEST_DATABASE_URL=postgresql+asyncpg://neondb_owner@ep-noisy-poetry-402590.us-east-2.aws.neon.tech/terrafusion_test

# Set to 'True' to see SQL echo in tests
SQLALCHEMY_TEST_ECHO=False
""")
            print("Created default .env file. Please update with your actual database credentials.")
    else:
        # Check if TEST_DATABASE_URL exists in the .env file
        env_vars = {}
        with open(env_path, 'r') as f:
            for line in f:
                if not line.strip() or line.strip().startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        
        # If TEST_DATABASE_URL is missing, add it
        if 'TEST_DATABASE_URL' not in env_vars:
            print("Adding TEST_DATABASE_URL to .env file...")
            with open(env_path, 'a') as f:
                f.write("\n# Test database URL (used by tests)\n")
                if 'DATABASE_URL' in env_vars:
                    # Create a test database URL based on the main one
                    db_url = env_vars['DATABASE_URL']
                    # Replace the database name with _test suffix
                    if '/' in db_url:
                        base, db_name = db_url.rsplit('/', 1)
                        test_db_url = f"{base}/{'_'.join(db_name.split('_')[:-1]) + '_test' if '_' in db_name else db_name + '_test'}"
                        f.write(f"TEST_DATABASE_URL={test_db_url}\n")
                    else:
                        f.write("TEST_DATABASE_URL=postgresql+asyncpg://neondb_owner@ep-noisy-poetry-402590.us-east-2.aws.neon.tech/terrafusion_test\n")
                else:
                    # Create a default test database URL
                    f.write("TEST_DATABASE_URL=postgresql+asyncpg://neondb_owner@ep-noisy-poetry-402590.us-east-2.aws.neon.tech/terrafusion_test\n")
                f.write("\n# Set to 'True' to see SQL echo in tests\nSQLALCHEMY_TEST_ECHO=False\n")


def run_tests(test_path, verbose=False, keywords=None):
    """
    Run pytest on the specified test path.
    
    Args:
        test_path: Path to the test file or directory
        verbose: Whether to use verbose output
        keywords: Keywords to filter tests
    """
    # Ensure we're in the project root
    os.chdir(Path(__file__).parent)
    
    # Load environment variables
    load_dotenv()
    
    # Build pytest command
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if keywords:
        cmd.extend(["-k", keywords])
    
    # Add test path
    cmd.append(str(test_path))
    
    # Print the command being run
    print(f"Running: {' '.join(cmd)}")
    
    # Run pytest
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted.")
        return 130  # Standard exit code for SIGINT


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run TerraFusion Platform integration tests")
    parser.add_argument("--path", default="terrafusion_platform/tests/integration",
                        help="Path to test file or directory (default: terrafusion_platform/tests/integration)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-k", "--keyword", help="Only run tests which match the given keyword expression")
    
    args = parser.parse_args()
    
    # Create or update test environment if needed
    create_test_env_if_needed()
    
    # Run the tests
    exit_code = run_tests(args.path, verbose=args.verbose, keywords=args.keyword)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()