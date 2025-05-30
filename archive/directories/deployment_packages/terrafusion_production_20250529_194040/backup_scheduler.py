"""
TerraFusion Platform - Automated Backup Scheduler

This module provides automated backup scheduling for the TerraFusion Platform,
ensuring county data is regularly backed up and protected against data loss.
"""

import os
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import subprocess
import json
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupScheduler:
    """
    Automated backup scheduler for TerraFusion Platform.
    
    Handles:
    - Database backups
    - File system backups
    - Configuration backups
    - Scheduled execution
    - Retention management
    """
    
    def __init__(self, backup_config: Dict = None):
        """
        Initialize the backup scheduler.
        
        Args:
            backup_config: Configuration dictionary for backup settings
        """
        self.config = backup_config or self._get_default_config()
        self.backup_dir = Path(self.config.get('backup_directory', 'backups'))
        self.running = False
        self.scheduler_thread = None
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupScheduler initialized with backup directory: {self.backup_dir}")
    
    def _get_default_config(self) -> Dict:
        """Get default backup configuration."""
        return {
            'backup_directory': 'backups',
            'database_backup_interval': 3600,  # 1 hour in seconds
            'file_backup_interval': 21600,     # 6 hours in seconds
            'retention_days': 30,
            'max_backups': 100,
            'backup_types': ['database', 'files', 'config'],
            'compress_backups': True,
            'backup_schedule': {
                'database': '0 */1 * * *',  # Every hour
                'files': '0 */6 * * *',     # Every 6 hours
                'config': '0 0 * * *'       # Daily at midnight
            }
        }
    
    def start_scheduler(self):
        """Start the automated backup scheduler."""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Backup scheduler started")
    
    def stop_scheduler(self):
        """Stop the automated backup scheduler."""
        if not self.running:
            logger.warning("Backup scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Backup scheduler loop started")
        
        last_database_backup = datetime.min
        last_file_backup = datetime.min
        last_config_backup = datetime.min
        
        while self.running:
            try:
                now = datetime.now()
                
                # Check if database backup is due
                if (now - last_database_backup).total_seconds() >= self.config['database_backup_interval']:
                    logger.info("Starting scheduled database backup")
                    if self.backup_database():
                        last_database_backup = now
                
                # Check if file backup is due
                if (now - last_file_backup).total_seconds() >= self.config['file_backup_interval']:
                    logger.info("Starting scheduled file backup")
                    if self.backup_files():
                        last_file_backup = now
                
                # Check if config backup is due (daily)
                if now.date() > last_config_backup.date():
                    logger.info("Starting scheduled configuration backup")
                    if self.backup_configuration():
                        last_config_backup = now
                
                # Clean up old backups
                self._cleanup_old_backups()
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in backup scheduler loop: {str(e)}", exc_info=True)
                time.sleep(300)  # Sleep for 5 minutes on error
    
    def backup_database(self) -> bool:
        """
        Create a database backup.
        
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"database_backup_{timestamp}.sql"
            backup_path = self.backup_dir / backup_filename
            
            # Get database connection details from environment
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL environment variable not found")
                return False
            
            # Extract connection details
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            
            db_host = parsed.hostname
            db_port = parsed.port or 5432
            db_name = parsed.path.lstrip('/')
            db_user = parsed.username
            db_password = parsed.password
            
            # Create pg_dump command with version compatibility
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            # Use the correct PostgreSQL 16 pg_dump to match server version
            pg_dump_cmd = '/nix/store/yz718sizpgsnq2y8gfv8bba8l8r4494l-postgresql-16.3/bin/pg_dump'
            
            # Verify the pg_dump version matches the server
            try:
                version_check = subprocess.run([pg_dump_cmd, '--version'], 
                                             capture_output=True, text=True)
                if version_check.returncode == 0:
                    logger.info(f"Using pg_dump: {version_check.stdout.strip()}")
                else:
                    logger.warning("Could not verify pg_dump version, using default")
                    pg_dump_cmd = 'pg_dump'
            except Exception as e:
                logger.warning(f"Error checking pg_dump version: {e}, using default")
                pg_dump_cmd = 'pg_dump'
            
            cmd = [
                pg_dump_cmd,
                '-h', str(db_host),
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '--no-password',
                '--verbose',
                '--clean',
                '--create',
                '-f', str(backup_path)
            ]
            
            logger.info(f"Creating database backup: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Compress the backup if configured
                if self.config.get('compress_backups', True):
                    compressed_path = self._compress_file(backup_path)
                    if compressed_path:
                        backup_path.unlink()  # Remove uncompressed file
                        backup_path = compressed_path
                
                file_size = backup_path.stat().st_size
                logger.info(f"Database backup created successfully: {backup_path.name} ({file_size} bytes)")
                
                # Record backup metadata
                self._record_backup_metadata('database', backup_path, file_size)
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                if backup_path.exists():
                    backup_path.unlink()
                return False
                
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}", exc_info=True)
            return False
    
    def backup_files(self) -> bool:
        """
        Create a backup of important files and directories.
        
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"files_backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename
            
            # Define directories to backup
            backup_dirs = [
                'exports',
                'syncs',
                'templates',
                'static',
                'county_configs',
                'logs'
            ]
            
            # Filter existing directories
            existing_dirs = [d for d in backup_dirs if os.path.exists(d)]
            
            if not existing_dirs:
                logger.warning("No directories found to backup")
                return False
            
            logger.info(f"Creating file backup: {backup_filename}")
            logger.info(f"Backing up directories: {existing_dirs}")
            
            # Create tar.gz archive
            import tarfile
            with tarfile.open(backup_path, 'w:gz') as tar:
                for directory in existing_dirs:
                    tar.add(directory, arcname=directory)
            
            file_size = backup_path.stat().st_size
            logger.info(f"File backup created successfully: {backup_path.name} ({file_size} bytes)")
            
            # Record backup metadata
            self._record_backup_metadata('files', backup_path, file_size)
            return True
            
        except Exception as e:
            logger.error(f"Error creating file backup: {str(e)}", exc_info=True)
            return False
    
    def backup_configuration(self) -> bool:
        """
        Create a backup of configuration files.
        
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename
            
            # Define configuration files to backup
            config_files = [
                '.env',
                'requirements.txt',
                'pyproject.toml',
                'docker-compose.yml',
                'prometheus.yml',
                '.replit',
                'county_users.json'
            ]
            
            # Filter existing files
            existing_files = [f for f in config_files if os.path.exists(f)]
            
            if not existing_files:
                logger.warning("No configuration files found to backup")
                return False
            
            logger.info(f"Creating configuration backup: {backup_filename}")
            logger.info(f"Backing up files: {existing_files}")
            
            # Create tar.gz archive
            import tarfile
            with tarfile.open(backup_path, 'w:gz') as tar:
                for file_path in existing_files:
                    tar.add(file_path, arcname=file_path)
            
            file_size = backup_path.stat().st_size
            logger.info(f"Configuration backup created successfully: {backup_path.name} ({file_size} bytes)")
            
            # Record backup metadata
            self._record_backup_metadata('config', backup_path, file_size)
            return True
            
        except Exception as e:
            logger.error(f"Error creating configuration backup: {str(e)}", exc_info=True)
            return False
    
    def _compress_file(self, file_path: Path) -> Optional[Path]:
        """
        Compress a file using gzip.
        
        Args:
            file_path: Path to the file to compress
            
        Returns:
            Path to the compressed file or None if compression failed
        """
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            import gzip
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"File compressed: {file_path.name} -> {compressed_path.name}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Error compressing file {file_path}: {str(e)}")
            return None
    
    def _record_backup_metadata(self, backup_type: str, backup_path: Path, file_size: int):
        """
        Record metadata about a backup.
        
        Args:
            backup_type: Type of backup (database, files, config)
            backup_path: Path to the backup file
            file_size: Size of the backup file in bytes
        """
        try:
            metadata_file = self.backup_dir / 'backup_metadata.json'
            
            # Load existing metadata
            metadata = []
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Add new backup record
            backup_record = {
                'timestamp': datetime.now().isoformat(),
                'type': backup_type,
                'filename': backup_path.name,
                'file_size': file_size,
                'path': str(backup_path),
                'created_at': datetime.now().isoformat()
            }
            
            metadata.append(backup_record)
            
            # Save updated metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error recording backup metadata: {str(e)}")
    
    def _cleanup_old_backups(self):
        """Clean up old backup files based on retention policy."""
        try:
            retention_days = self.config.get('retention_days', 30)
            max_backups = self.config.get('max_backups', 100)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backup_files = list(self.backup_dir.glob('*backup_*.sql*')) + \
                          list(self.backup_dir.glob('*backup_*.tar.gz'))
            
            # Sort by creation time
            backup_files.sort(key=lambda f: f.stat().st_mtime)
            
            deleted_count = 0
            
            # Delete old files
            for backup_file in backup_files:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    logger.info(f"Deleting old backup: {backup_file.name}")
                    backup_file.unlink()
                    deleted_count += 1
            
            # Delete excess files if we have too many
            remaining_files = [f for f in backup_files if f.exists()]
            if len(remaining_files) > max_backups:
                excess_count = len(remaining_files) - max_backups
                for backup_file in remaining_files[:excess_count]:
                    logger.info(f"Deleting excess backup: {backup_file.name}")
                    backup_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        try:
            metadata_file = self.backup_dir / 'backup_metadata.json'
            
            if not metadata_file.exists():
                return []
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Filter to only include existing files
            existing_backups = []
            for backup in metadata:
                backup_path = Path(backup['path'])
                if backup_path.exists():
                    backup['exists'] = True
                    backup['current_size'] = backup_path.stat().st_size
                    existing_backups.append(backup)
            
            return existing_backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []

# Global backup scheduler instance
backup_scheduler = BackupScheduler()

def start_backup_service():
    """Start the backup service."""
    backup_scheduler.start_scheduler()
    logger.info("TerraFusion backup service started")

def stop_backup_service():
    """Stop the backup service."""
    backup_scheduler.stop_scheduler()
    logger.info("TerraFusion backup service stopped")

if __name__ == '__main__':
    # Start backup service if run directly
    start_backup_service()
    try:
        # Keep the service running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_backup_service()