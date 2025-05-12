#!/usr/bin/env python3
"""
TerraFusion SyncService - Market Analysis Plugin Integration Fix

This script creates and configures the necessary files for the 
Market Analysis plugin integration with the SyncService.

The script ensures that:
1. All required market analysis plugin files exist
2. Plugin is properly registered with the SyncService
3. Database tables are created for the plugin models
"""

import os
import sys
import json
import logging
import importlib
import asyncio
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required directory structure
REQUIRED_DIRS = [
    'terrafusion_sync/plugins/market_analysis',
]

# Required files check
REQUIRED_FILES = [
    'terrafusion_sync/plugins/market_analysis/__init__.py',
    'terrafusion_sync/plugins/market_analysis/router.py',
    'terrafusion_sync/plugins/market_analysis/schemas.py',
    'terrafusion_sync/plugins/market_analysis/service.py',
    'terrafusion_sync/plugins/market_analysis/models.py',
    'terrafusion_sync/plugins/market_analysis/metrics.py',
]

def run_command(cmd, shell=False, timeout=None):
    """Run a command and return the output."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_required_components():
    """Check that all required directories and files exist."""
    # Check directories
    missing_dirs = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing_dirs.append(d)
            
    if missing_dirs:
        logger.warning(f"Missing directories: {missing_dirs}")
        for d in missing_dirs:
            os.makedirs(d, exist_ok=True)
            logger.info(f"Created directory: {d}")
    
    # Check files
    missing_files = []
    for f in REQUIRED_FILES:
        if not os.path.isfile(f):
            missing_files.append(f)
    
    if missing_files:
        logger.warning(f"Missing files: {missing_files}")
        return False
    
    return True

def check_plugin_registration():
    """Check that the plugin is properly registered."""
    syncservice_app_path = 'terrafusion_sync/app.py'
    
    if not os.path.isfile(syncservice_app_path):
        logger.error(f"SyncService app file not found: {syncservice_app_path}")
        return False
    
    with open(syncservice_app_path, 'r') as f:
        content = f.read()
        
    if 'from terrafusion_sync.plugins.market_analysis import plugin_router' not in content:
        logger.warning("Market Analysis plugin not imported in app.py")
        return False
        
    if 'app.include_router(plugin_router)' not in content:
        logger.warning("Market Analysis plugin router not registered in app.py")
        return False
        
    return True

def fix_plugin_registration():
    """Fix plugin registration in the SyncService app."""
    syncservice_app_path = 'terrafusion_sync/app.py'
    
    if not os.path.isfile(syncservice_app_path):
        logger.error(f"SyncService app file not found: {syncservice_app_path}")
        return False
    
    with open(syncservice_app_path, 'r') as f:
        lines = f.readlines()
    
    # Check for imports section to add our import
    import_section_found = False
    import_added = False
    plugin_registered = False
    
    for i, line in enumerate(lines):
        if 'from terrafusion_sync.plugins.market_analysis import plugin_router' in line:
            import_added = True
            
        if 'app.include_router(plugin_router' in line and 'plugins.market_analysis' in line:
            plugin_registered = True
            
        if 'import' in line:
            import_section_found = True
    
    # If imports section found but our import is missing, add it
    if import_section_found and not import_added:
        for i, line in enumerate(lines):
            if 'import' in line:
                # Find the last import line
                j = i
                while j < len(lines) and ('import' in lines[j] or lines[j].strip() == ''):
                    j += 1
                
                # Add our import after the last import
                lines.insert(j, 'from terrafusion_sync.plugins.market_analysis import plugin_router as market_analysis_router\n')
                logger.info("Added market analysis plugin import")
                break
    
    # Now find where routers are registered
    if not plugin_registered:
        for i, line in enumerate(lines):
            if 'app.include_router(' in line:
                # Find the last router registration
                j = i
                while j < len(lines) and 'app.include_router(' in lines[j]:
                    j += 1
                
                # Add our router registration
                lines.insert(j, 'app.include_router(market_analysis_router, tags=["Market Analysis"])\n')
                logger.info("Added market analysis plugin router registration")
                break
    
    # Write changes back to file
    with open(syncservice_app_path, 'w') as f:
        f.writelines(lines)
    
    return True

def ensure_database_initialized():
    """Initialize database tables for the plugin."""
    try:
        # First try to import the model to verify it's accessible
        from terrafusion_sync.plugins.market_analysis.models import MarketAnalysisJob, Base
        logger.info("Successfully imported MarketAnalysisJob model")
        
        # Create DB initialization script in a temp file
        init_script = """
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from terrafusion_sync.database import DATABASE_URL
from terrafusion_sync.plugins.market_analysis.models import Base

async def init_db():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(init_db())
        """
        
        temp_file = 'init_market_analysis_db.py'
        with open(temp_file, 'w') as f:
            f.write(init_script)
        
        # Run the script
        returncode, stdout, stderr = run_command([sys.executable, temp_file])
        if returncode != 0:
            logger.error(f"Failed to initialize database: {stderr}")
            return False
        
        os.unlink(temp_file)
        logger.info("Database tables for Market Analysis plugin initialized")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import models: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def restart_syncservice():
    """Restart the SyncService workflow."""
    logger.info("Attempting to restart SyncService workflow")
    script_path = "restart_syncservice_workflow.py"
    
    if os.path.exists(script_path):
        return_code, stdout, stderr = run_command([sys.executable, script_path])
        if return_code == 0:
            logger.info("SyncService workflow restarted successfully")
            return True
        else:
            logger.error(f"Failed to restart SyncService workflow: {stderr}")
            return False
    else:
        logger.warning(f"Restart script not found: {script_path}, trying to kill and restart manually")
        
        # Kill any running syncservice process
        run_command("pkill -f run_syncservice_workflow", shell=True)
        
        # Start the workflow in the background
        return_code, stdout, stderr = run_command(
            f"{sys.executable} run_syncservice_workflow.py &", 
            shell=True
        )
        
        if return_code == 0:
            logger.info("SyncService workflow started manually")
            return True
        else:
            logger.error(f"Failed to manually start SyncService: {stderr}")
            return False

def main():
    """Main function to fix the market analysis plugin integration."""
    logger.info("Starting Market Analysis plugin integration fix")
    
    # Check and fix if needed
    if not check_required_components():
        logger.error("Missing required components. Please create them first.")
        return False
    
    if not check_plugin_registration():
        logger.info("Fixing plugin registration...")
        if not fix_plugin_registration():
            logger.error("Failed to fix plugin registration.")
            return False
    
    # Initialize database
    if not ensure_database_initialized():
        logger.error("Failed to initialize database for Market Analysis plugin.")
        return False
    
    # Restart syncservice
    if not restart_syncservice():
        logger.error("Failed to restart SyncService workflow.")
        return False
    
    logger.info("Market Analysis plugin integration fixed successfully.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)