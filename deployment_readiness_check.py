#!/usr/bin/env python
"""
TerraFusion SyncService Deployment Readiness Check

This script performs a comprehensive readiness check before deploying the
TerraFusion SyncService platform, including:

1. Validating configuration files
2. Checking environment variables
3. Verifying database connectivity and schema
4. Testing service health endpoints
5. Validating Docker configuration
6. Checking API endpoints
7. Verifying WebSocket functionality
8. Ensuring monitoring is configured properly

Usage:
    python deployment_readiness_check.py [--fix]

Arguments:
    --fix        Attempt to fix common issues automatically
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import importlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "PGHOST",
    "PGPORT",
    "PGUSER",
    "PGPASSWORD",
    "PGDATABASE"
]

REQUIRED_FILES = [
    "app.py",
    "main.py",
    "models.py",
    "syncservice.py",
    "Dockerfile.api-gateway",
    "Dockerfile.sync-service",
    "docker-compose.yml",
    "monitoring_config.py",
    "syncservice_websocket.py",
    "run_websocket_server.py"
]

API_PORT = 5000
SYNC_PORT = 8080
WEBSOCKET_PORT = 8081

# Results tracking
class CheckResult:
    """Result of a single check."""
    
    def __init__(self, name: str, passed: bool, details: str = None, fix_available: bool = False, fix_applied: bool = False):
        self.name = name
        self.passed = passed
        self.details = details
        self.fix_available = fix_available
        self.fix_applied = fix_applied
        self.timestamp = datetime.now()
    
    def __str__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        fix_status = ""
        if not self.passed and self.fix_available:
            fix_status = " (Fix available)"
        if self.fix_applied:
            fix_status = " (Fix applied)"
        
        result = f"{status} {self.name}{fix_status}"
        if self.details and not self.passed:
            result += f"\n  → {self.details}"
        
        return result

class DeploymentReadinessResults:
    """Track results of deployment readiness checks."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results: Dict[str, CheckResult] = {}
        self.categories: Dict[str, List[str]] = {
            "Configuration": [],
            "Environment": [],
            "Database": [],
            "Services": [],
            "API": [],
            "WebSocket": [],
            "Docker": [],
            "Monitoring": []
        }
    
    def add_result(self, category: str, name: str, passed: bool, details: str = None, 
                  fix_available: bool = False, fix_applied: bool = False):
        """Add a check result."""
        # Create a full name including category
        full_name = f"{category}: {name}"
        
        # Create the result
        result = CheckResult(name, passed, details, fix_available, fix_applied)
        
        # Store the result
        self.results[full_name] = result
        
        # Add to category
        if category in self.categories:
            self.categories[category].append(full_name)
        else:
            self.categories[category] = [full_name]
        
        # Log the result
        if passed:
            logger.info(f"✅ {name} check passed")
        else:
            logger.warning(f"❌ {name} check failed: {details}")
            if fix_available:
                logger.info(f"   (Fix available for {name})")
            if fix_applied:
                logger.info(f"   (Fix applied for {name})")
    
    def all_passed(self) -> bool:
        """Check if all checks passed."""
        return all(result.passed for result in self.results.values())
    
    def category_passed(self, category: str) -> bool:
        """Check if all checks in a category passed."""
        if category not in self.categories:
            return False
        
        return all(self.results[name].passed for name in self.categories[category])
    
    def count_total(self) -> int:
        """Count total number of checks."""
        return len(self.results)
    
    def count_passed(self) -> int:
        """Count number of passed checks."""
        return sum(1 for result in self.results.values() if result.passed)
    
    def count_failed(self) -> int:
        """Count number of failed checks."""
        return sum(1 for result in self.results.values() if not result.passed)
    
    def count_fixed(self) -> int:
        """Count number of fixed checks."""
        return sum(1 for result in self.results.values() if result.fix_applied)
    
    def print_summary(self, show_all: bool = False):
        """Print a summary of the readiness check results."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n============================================")
        print("  DEPLOYMENT READINESS CHECK RESULTS")
        print("============================================")
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration:.2f} seconds")
        print("--------------------------------------------")
        
        # Print categories
        for category, check_names in self.categories.items():
            if not check_names:
                continue
                
            category_status = "✅" if self.category_passed(category) else "❌"
            passed_count = sum(1 for name in check_names if self.results[name].passed)
            total_count = len(check_names)
            
            print(f"{category_status} {category}: {passed_count}/{total_count} checks passed")
            
            # Print individual results if showing all or category failed
            if show_all or not self.category_passed(category):
                for name in check_names:
                    result = self.results[name]
                    status = "✅" if result.passed else "❌"
                    print(f"  {status} {result.name}")
                    if not result.passed and result.details:
                        print(f"     → {result.details}")
                        if result.fix_available and not result.fix_applied:
                            print(f"     → (Fix available, use --fix to apply)")
                        elif result.fix_applied:
                            print(f"     → (Fix was applied)")
                print()
        
        # Print summary
        print("--------------------------------------------")
        total = self.count_total()
        passed = self.count_passed()
        failed = self.count_failed()
        fixed = self.count_fixed()
        
        print(f"CHECKS: {total} total, {passed} passed, {failed} failed")
        if fixed > 0:
            print(f"FIXES:  {fixed} applied")
        
        # Print deployment readiness
        if self.all_passed():
            print("\n✅ SYSTEM IS READY FOR DEPLOYMENT")
        else:
            print("\n❌ SYSTEM IS NOT READY FOR DEPLOYMENT")
            print("   Please address the failed checks before deploying")
        
        print("============================================\n")
        
        return self.all_passed()

# Check functions
def check_file_exists(filename: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    path = Path(filename)
    return path.exists(), None if path.exists() else f"File not found: {filename}"

def check_env_vars() -> Tuple[bool, str, List[str]]:
    """
    Check if required environment variables are set.
    
    Returns:
        (all_set, message, missing_vars)
    """
    missing = []
    for var in REQUIRED_ENV_VARS:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        return False, f"Missing environment variables: {', '.join(missing)}", missing
    return True, None, []

def check_database_connection() -> Tuple[bool, str]:
    """Check database connection."""
    try:
        # Check if we have the psycopg2 module
        import psycopg2
        
        # Get connection parameters from environment
        conn_params = {
            "host": os.environ.get("PGHOST"),
            "port": os.environ.get("PGPORT"),
            "user": os.environ.get("PGUSER"),
            "password": os.environ.get("PGPASSWORD"),
            "dbname": os.environ.get("PGDATABASE")
        }
        
        # Try to connect
        conn = psycopg2.connect(**conn_params)
        conn.close()
        
        return True, None
    except ImportError:
        return False, "psycopg2 module not available"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"

def check_database_tables() -> Tuple[bool, str, Set[str]]:
    """
    Check if required database tables exist.
    
    Returns:
        (exists, message, missing_tables)
    """
    try:
        # Get the required tables from the models
        required_tables = {
            "sync_pair", 
            "sync_operation", 
            "system_metrics", 
            "audit_entry"
        }
        
        # Check if tables exist in the database
        import psycopg2
        
        # Get connection parameters from environment
        conn_params = {
            "host": os.environ.get("PGHOST"),
            "port": os.environ.get("PGPORT"),
            "user": os.environ.get("PGUSER"),
            "password": os.environ.get("PGPASSWORD"),
            "dbname": os.environ.get("PGDATABASE")
        }
        
        # Connect and check tables
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Check which required tables are missing
        missing_tables = required_tables - existing_tables
        
        if missing_tables:
            return False, f"Missing database tables: {', '.join(missing_tables)}", missing_tables
        return True, None, set()
    except Exception as e:
        return False, f"Error checking database tables: {str(e)}", set()

def check_service_running(port: int, name: str) -> Tuple[bool, str]:
    """Check if a service is running on the specified port."""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # 1 second timeout
    
    try:
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            return True, None
        else:
            return False, f"{name} is not running on port {port}"
    except socket.error as e:
        return False, f"Socket error when checking {name}: {str(e)}"
    finally:
        sock.close()

def check_service_health(url: str, name: str) -> Tuple[bool, str]:
    """Check if a service is healthy."""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"{name} returned status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {name}"
    except requests.exceptions.Timeout:
        return False, f"{name} timed out"
    except Exception as e:
        return False, f"Error checking {name} health: {str(e)}"

def check_docker_files() -> Tuple[bool, str, List[str]]:
    """
    Check Docker configuration files.
    
    Returns:
        (valid, message, missing_files)
    """
    docker_files = [
        "Dockerfile.api-gateway",
        "Dockerfile.sync-service",
        "docker-compose.yml"
    ]
    
    missing = []
    for filename in docker_files:
        if not os.path.exists(filename):
            missing.append(filename)
    
    if missing:
        return False, f"Missing Docker files: {', '.join(missing)}", missing
    return True, None, []

def check_valid_yaml(filename: str) -> Tuple[bool, str]:
    """Check if a YAML file is valid."""
    try:
        import yaml
        with open(filename, 'r') as file:
            yaml.safe_load(file)
        return True, None
    except ImportError:
        return False, "yaml module not available"
    except FileNotFoundError:
        return False, f"File not found: {filename}"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {str(e)}"
    except Exception as e:
        return False, f"Error reading YAML file: {str(e)}"

def check_websocket_implementation() -> Tuple[bool, str, List[str]]:
    """
    Check WebSocket implementation.
    
    Returns:
        (implemented, message, missing_files)
    """
    websocket_files = [
        "syncservice_websocket.py",
        "run_websocket_server.py"
    ]
    
    missing = []
    for filename in websocket_files:
        if not os.path.exists(filename):
            missing.append(filename)
    
    if missing:
        return False, f"Missing WebSocket files: {', '.join(missing)}", missing
    
    # If files exist, check if they import the required modules
    with open("syncservice_websocket.py", 'r') as file:
        content = file.read()
        if "import aiohttp" not in content and "from aiohttp import" not in content:
            return False, "WebSocket implementation missing aiohttp import", []
    
    return True, None, []

def fix_missing_env_vars(missing_vars: List[str]) -> bool:
    """
    Fix missing environment variables.
    
    Args:
        missing_vars: List of missing environment variables
        
    Returns:
        True if fixed, False otherwise
    """
    # Try to get variables from .env file if it exists
    env_fixed = False
    
    if os.path.exists(".env"):
        with open(".env", 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                # Parse key=value
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Set environment variable if it's missing
                    if key in missing_vars and key not in os.environ:
                        os.environ[key] = value
                        env_fixed = True
    
    # Check if all variables are now set
    still_missing = [var for var in missing_vars if var not in os.environ]
    
    return env_fixed and not still_missing

def fix_docker_compose(missing_files: List[str]) -> bool:
    """
    Fix missing Docker Compose file.
    
    Args:
        missing_files: List of missing Docker files
        
    Returns:
        True if fixed, False otherwise
    """
    if "docker-compose.yml" in missing_files:
        # Create a basic docker-compose.yml file
        docker_compose = """version: '3'

services:
  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile.api-gateway
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SYNCSERVICE_URL=http://sync-service:8080
      - WEBSOCKET_URL=http://websocket-server:8081
    depends_on:
      - sync-service
      - websocket-server
    networks:
      - terrafusion-network

  sync-service:
    build:
      context: .
      dockerfile: Dockerfile.sync-service
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    networks:
      - terrafusion-network

  websocket-server:
    build:
      context: .
      dockerfile: Dockerfile.api-gateway
    command: python run_websocket_server.py
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    networks:
      - terrafusion-network

networks:
  terrafusion-network:
"""
        
        with open("docker-compose.yml", 'w') as file:
            file.write(docker_compose)
        
        return True
    
    return False

def fix_websocket_implementation(missing_files: List[str]) -> bool:
    """
    Fix missing WebSocket implementation files.
    
    Args:
        missing_files: List of missing WebSocket files
        
    Returns:
        True if fixed, False otherwise
    """
    fixed = False
    
    if "run_websocket_server.py" in missing_files:
        # Create a basic run_websocket_server.py file
        websocket_server = """#!/usr/bin/env python
\"\"\"
WebSocket server for TerraFusion SyncService.

This script starts the WebSocket server that provides real-time updates
for sync operations.
\"\"\"

import os
import sys
import logging
import asyncio
from syncservice_websocket import create_websocket_app

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default port
DEFAULT_PORT = 8081

def main():
    \"\"\"Main entry point for the script.\"\"\"
    # Get port from environment or use default
    port = int(os.environ.get("WEBSOCKET_PORT", DEFAULT_PORT))
    
    logger.info(f"Starting WebSocket server on port {port}")
    
    # Create and run the app
    app = create_websocket_app()
    
    # Run the server
    try:
        asyncio.run(app.run_server(host="0.0.0.0", port=port))
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped by user")
    except Exception as e:
        logger.error(f"WebSocket server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
        
        with open("run_websocket_server.py", 'w') as file:
            file.write(websocket_server)
        
        fixed = True
    
    return fixed

def run_deployment_readiness_check(fix_issues: bool = False) -> DeploymentReadinessResults:
    """
    Run deployment readiness checks.
    
    Args:
        fix_issues: Whether to attempt to fix issues
        
    Returns:
        DeploymentReadinessResults object
    """
    results = DeploymentReadinessResults()
    
    # Check required files
    logger.info("Checking required files...")
    for filename in REQUIRED_FILES:
        exists, error_message = check_file_exists(filename)
        results.add_result("Configuration", f"File '{filename}'", exists, error_message)
    
    # Check environment variables
    logger.info("Checking environment variables...")
    env_vars_set, env_error, missing_vars = check_env_vars()
    
    # Try to fix missing env vars if needed
    fix_applied = False
    if not env_vars_set and fix_issues:
        fix_applied = fix_missing_env_vars(missing_vars)
        if fix_applied:
            # Check again after fix
            env_vars_set, env_error, missing_vars = check_env_vars()
    
    results.add_result(
        "Environment", 
        "Required environment variables", 
        env_vars_set, 
        env_error, 
        not env_vars_set,  # Fix available if not set
        fix_applied
    )
    
    # Check database connection
    logger.info("Checking database connection...")
    db_connected, db_error = check_database_connection()
    results.add_result("Database", "Database connection", db_connected, db_error)
    
    # Check database tables
    if db_connected:
        logger.info("Checking database tables...")
        tables_exist, tables_error, missing_tables = check_database_tables()
        results.add_result("Database", "Required database tables", tables_exist, tables_error)
    
    # Check Docker configuration
    logger.info("Checking Docker configuration...")
    docker_valid, docker_error, missing_docker_files = check_docker_files()
    
    # Try to fix Docker files if needed
    docker_fix_applied = False
    if not docker_valid and fix_issues:
        docker_fix_applied = fix_docker_compose(missing_docker_files)
        if docker_fix_applied:
            # Check again after fix
            docker_valid, docker_error, missing_docker_files = check_docker_files()
    
    results.add_result(
        "Docker", 
        "Docker configuration files", 
        docker_valid, 
        docker_error, 
        not docker_valid,  # Fix available if not valid
        docker_fix_applied
    )
    
    # Check docker-compose.yml validity
    if os.path.exists("docker-compose.yml"):
        logger.info("Checking docker-compose.yml validity...")
        compose_valid, compose_error = check_valid_yaml("docker-compose.yml")
        results.add_result("Docker", "docker-compose.yml validity", compose_valid, compose_error)
    
    # Check WebSocket implementation
    logger.info("Checking WebSocket implementation...")
    websocket_valid, websocket_error, missing_websocket_files = check_websocket_implementation()
    
    # Try to fix WebSocket files if needed
    websocket_fix_applied = False
    if not websocket_valid and fix_issues:
        websocket_fix_applied = fix_websocket_implementation(missing_websocket_files)
        if websocket_fix_applied:
            # Check again after fix
            websocket_valid, websocket_error, missing_websocket_files = check_websocket_implementation()
    
    results.add_result(
        "WebSocket", 
        "WebSocket implementation", 
        websocket_valid, 
        websocket_error, 
        not websocket_valid,  # Fix available if not valid
        websocket_fix_applied
    )
    
    # Check if services are running
    logger.info("Checking if services are running...")
    
    # API Gateway
    api_running, api_error = check_service_running(API_PORT, "API Gateway")
    results.add_result("Services", "API Gateway running", api_running, api_error)
    
    # SyncService
    sync_running, sync_error = check_service_running(SYNC_PORT, "SyncService")
    results.add_result("Services", "SyncService running", sync_running, sync_error)
    
    # WebSocket Server
    websocket_running, websocket_error = check_service_running(WEBSOCKET_PORT, "WebSocket Server")
    results.add_result("Services", "WebSocket Server running", websocket_running, websocket_error)
    
    # If services are running, check their health
    if api_running:
        logger.info("Checking API Gateway health...")
        api_healthy, api_health_error = check_service_health(f"http://localhost:{API_PORT}", "API Gateway")
        results.add_result("Services", "API Gateway health", api_healthy, api_health_error)
    
    if sync_running:
        logger.info("Checking SyncService health...")
        sync_healthy, sync_health_error = check_service_health(f"http://localhost:{SYNC_PORT}", "SyncService")
        results.add_result("Services", "SyncService health", sync_healthy, sync_health_error)
    
    if websocket_running:
        logger.info("Checking WebSocket Server health...")
        websocket_healthy, websocket_health_error = check_service_health(f"http://localhost:{WEBSOCKET_PORT}", "WebSocket Server")
        results.add_result("Services", "WebSocket Server health", websocket_healthy, websocket_health_error)
    
    return results

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Check deployment readiness of TerraFusion SyncService")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues")
    args = parser.parse_args()
    
    logger.info("Starting deployment readiness check...")
    
    # Run checks
    results = run_deployment_readiness_check(args.fix)
    
    # Print results
    all_passed = results.print_summary(show_all=True)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()