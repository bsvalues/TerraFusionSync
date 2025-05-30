"""
TerraFusion SyncService Backup Utilities

This module provides database backup and recovery utilities for the TerraFusion SyncService platform.
"""

import os
import sys
import gzip
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('backup_utilities')

# Backup directory
BACKUP_DIR = os.path.join(os.getcwd(), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Maximum number of backups to keep
MAX_BACKUPS = 7


def get_database_env_vars():
    """
    Get PostgreSQL connection details from environment variables.
    
    Returns:
        Dictionary with database connection parameters
    """
    required_vars = [
        'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE'
    ]
    
    env_vars = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            env_vars[var] = value
        else:
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return None
    
    return env_vars


def create_database_backup(backup_dir: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of the PostgreSQL database.
    
    Args:
        backup_dir: Directory to store the backup (default: BACKUP_DIR)
        
    Returns:
        Path to the backup file or None if failed
    """
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    
    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get database connection parameters
    db_vars = get_database_env_vars()
    if not db_vars:
        return None
    
    # Create a timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f"{db_vars['PGDATABASE']}_{timestamp}.sql")
    compressed_file = f"{backup_file}.gz"
    
    try:
        # Execute pg_dump
        logger.info(f"Creating database backup to {backup_file}")
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        for key, value in db_vars.items():
            env[key] = value
        
        # Run pg_dump to create the backup
        with open(backup_file, 'w') as f:
            process = subprocess.Popen(
                ['pg_dump', '-c', '--if-exists'],
                stdout=f,
                stderr=subprocess.PIPE,
                env=env
            )
            _, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"pg_dump failed: {stderr.decode()}")
            os.unlink(backup_file)
            return None
        
        # Compress the backup
        logger.info(f"Compressing backup to {compressed_file}")
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove the uncompressed file
        os.unlink(backup_file)
        
        # Clean up old backups
        cleanup_old_backups(backup_dir)
        
        return compressed_file
    
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        # Clean up partial backups
        if os.path.exists(backup_file):
            os.unlink(backup_file)
        if os.path.exists(compressed_file):
            os.unlink(compressed_file)
        return None


def restore_database_backup(backup_file: str) -> bool:
    """
    Restore a database from a backup file.
    
    Args:
        backup_file: Path to the backup file (.sql or .sql.gz)
        
    Returns:
        True if restore was successful, False otherwise
    """
    # Get database connection parameters
    db_vars = get_database_env_vars()
    if not db_vars:
        return False
    
    try:
        # Check if the file exists
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Set environment variables for psql
        env = os.environ.copy()
        for key, value in db_vars.items():
            env[key] = value
        
        # If the file is compressed, decompress it first
        is_compressed = backup_file.endswith('.gz')
        if is_compressed:
            temp_file = backup_file[:-3]  # Remove .gz extension
            logger.info(f"Decompressing {backup_file} to {temp_file}")
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = temp_file
        
        # Run psql to restore the backup
        logger.info(f"Restoring database from {backup_file}")
        process = subprocess.Popen(
            ['psql'],
            stdin=open(backup_file, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        stdout, stderr = process.communicate()
        
        # Clean up temporary decompressed file
        if is_compressed and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        if process.returncode != 0:
            logger.error(f"psql restore failed: {stderr.decode()}")
            return False
        
        logger.info("Database restore completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        return False


def list_backups(backup_dir: Optional[str] = None) -> List[str]:
    """
    List available database backups.
    
    Args:
        backup_dir: Directory containing backups (default: BACKUP_DIR)
        
    Returns:
        List of backup file paths
    """
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    
    if not os.path.exists(backup_dir):
        logger.warning(f"Backup directory not found: {backup_dir}")
        return []
    
    # Get all .sql.gz files in the backup directory
    backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
              if f.endswith('.sql.gz')]
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return backups


def cleanup_old_backups(backup_dir: Optional[str] = None, max_backups: int = MAX_BACKUPS):
    """
    Remove old backups to maintain the maximum number of backups.
    
    Args:
        backup_dir: Directory containing backups (default: BACKUP_DIR)
        max_backups: Maximum number of backups to keep
    """
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    
    backups = list_backups(backup_dir)
    
    # If we have more backups than the maximum, remove the oldest ones
    if len(backups) > max_backups:
        for old_backup in backups[max_backups:]:
            logger.info(f"Removing old backup: {old_backup}")
            os.unlink(old_backup)


if __name__ == "__main__":
    # Simple command-line interface
    if len(sys.argv) < 2:
        print("Usage: python backup_utilities.py [backup|restore|list]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        backup_file = create_database_backup()
        if backup_file:
            print(f"Backup created: {backup_file}")
        else:
            print("Backup failed")
            sys.exit(1)
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Usage: python backup_utilities.py restore <backup_file>")
            sys.exit(1)
        
        backup_file = sys.argv[2]
        if restore_database_backup(backup_file):
            print(f"Database restored from {backup_file}")
        else:
            print("Restore failed")
            sys.exit(1)
    
    elif command == 'list':
        backups = list_backups()
        if backups:
            print("Available backups:")
            for i, backup in enumerate(backups, 1):
                size_mb = os.path.getsize(backup) / (1024 * 1024)
                mtime = datetime.fromtimestamp(os.path.getmtime(backup))
                print(f"{i}. {os.path.basename(backup)} ({size_mb:.2f} MB, {mtime})")
        else:
            print("No backups found")
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: python backup_utilities.py [backup|restore|list]")
        sys.exit(1)