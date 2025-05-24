#!/usr/bin/env python3
"""
TerraFusion Platform - Database Setup

This script initializes the PostgreSQL database with the required tables
and populates them with some initial county data.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, County, User, GisExportJob, SyncJob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database and create tables."""
    try:
        # Get database connection string from environment variable
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
        
        # Create engine and tables
        logger.info(f"Connecting to database: {db_url}")
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        return session
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)

def create_sample_counties(session):
    """Create sample county records."""
    counties = [
        {
            "county_id": "benton-wa",
            "name": "Benton County",
            "state": "WA",
            "config_path": "county_configs/benton-wa/"
        },
        {
            "county_id": "king-wa",
            "name": "King County",
            "state": "WA",
            "config_path": "county_configs/king-wa/"
        },
        {
            "county_id": "pierce-wa",
            "name": "Pierce County",
            "state": "WA",
            "config_path": "county_configs/pierce-wa/"
        },
        {
            "county_id": "snohomish-wa",
            "name": "Snohomish County",
            "state": "WA",
            "config_path": "county_configs/snohomish-wa/"
        }
    ]
    
    for county_data in counties:
        # Check if county already exists
        existing = session.query(County).filter_by(county_id=county_data["county_id"]).first()
        if existing:
            logger.info(f"County {county_data['name']} already exists")
            continue
        
        # Create new county
        county = County(
            county_id=county_data["county_id"],
            name=county_data["name"],
            state=county_data["state"],
            config_path=county_data["config_path"]
        )
        session.add(county)
        logger.info(f"Created county: {county_data['name']}, {county_data['state']}")
    
    session.commit()
    logger.info("Sample counties created successfully")

def create_admin_user(session):
    """Create an admin user account."""
    # Check if admin already exists
    existing = session.query(User).filter_by(username="admin").first()
    if existing:
        logger.info("Admin user already exists")
        return
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@terrafusion.com",
        password_hash="$2b$12$GxvFJtTJYR5hZQz9ZFvD7.JVJz8QUbY7dV0qGNPxG5gPtWU0QLTK2",  # hashed version of 'admin123'
        first_name="Admin",
        last_name="User",
        county="benton-wa",  # Changed from county_id to county
        role="admin",
        is_active=True,
        last_login=datetime.utcnow()
    )
    session.add(admin)
    session.commit()
    logger.info("Admin user created successfully")

def import_existing_jobs(session):
    """Import existing jobs from JSON files into database."""
    try:
        # Import GIS Export jobs
        import_gis_export_jobs(session)
        
        # Import Sync jobs
        import_sync_jobs(session)
        
        logger.info("Existing jobs imported successfully")
    except Exception as e:
        logger.error(f"Error importing existing jobs: {str(e)}")

def import_gis_export_jobs(session):
    """Import existing GIS Export jobs from JSON files."""
    import json
    import os
    
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        logger.info(f"Exports directory {exports_dir} not found, skipping GIS Export job import")
        return
    
    # Find all job JSON files
    count = 0
    for filename in os.listdir(exports_dir):
        if filename.endswith('.json'):
            try:
                # Read job data from file
                with open(os.path.join(exports_dir, filename), 'r') as f:
                    job_data = json.load(f)
                
                # Check if job already exists in database
                job_id = job_data.get('job_id')
                if not job_id:
                    continue
                
                existing = session.query(GisExportJob).filter_by(job_id=job_id).first()
                if existing:
                    logger.info(f"GIS Export job {job_id} already exists in database")
                    continue
                
                # Create database record
                job = GisExportJob(
                    job_id=job_id,
                    county_id=job_data.get('county_id'),
                    username=job_data.get('username'),
                    export_format=job_data.get('export_format'),
                    area_of_interest=job_data.get('area_of_interest'),
                    layers=job_data.get('layers'),
                    parameters=job_data.get('parameters', {}),
                    status=job_data.get('status'),
                    message=job_data.get('message'),
                    file_path=job_data.get('file_path'),
                    file_size=job_data.get('file_size'),
                    download_url=job_data.get('download_url')
                )
                
                # Set timestamps
                if job_data.get('created_at'):
                    job.created_at = datetime.fromisoformat(job_data['created_at'])
                if job_data.get('started_at'):
                    job.started_at = datetime.fromisoformat(job_data['started_at'])
                if job_data.get('completed_at'):
                    job.completed_at = datetime.fromisoformat(job_data['completed_at'])
                
                # Add to session
                session.add(job)
                count += 1
            except Exception as e:
                logger.error(f"Error importing GIS Export job from {filename}: {str(e)}")
    
    # Commit changes
    session.commit()
    logger.info(f"Imported {count} GIS Export jobs from JSON files")

def import_sync_jobs(session):
    """Import existing Sync jobs from JSON files."""
    import json
    import os
    
    syncs_dir = "syncs"
    if not os.path.exists(syncs_dir):
        logger.info(f"Syncs directory {syncs_dir} not found, skipping Sync job import")
        return
    
    # Find all job JSON files
    count = 0
    for filename in os.listdir(syncs_dir):
        if filename.endswith('.json'):
            try:
                # Read job data from file
                with open(os.path.join(syncs_dir, filename), 'r') as f:
                    job_data = json.load(f)
                
                # Check if job already exists in database
                job_id = job_data.get('job_id')
                if not job_id:
                    continue
                
                existing = session.query(SyncJob).filter_by(job_id=job_id).first()
                if existing:
                    logger.info(f"Sync job {job_id} already exists in database")
                    continue
                
                # Create database record
                job = SyncJob(
                    job_id=job_id,
                    county_id=job_data.get('county_id'),
                    username=job_data.get('username'),
                    data_types=job_data.get('data_types'),
                    source_system=job_data.get('source_system'),
                    target_system=job_data.get('target_system'),
                    parameters=job_data.get('parameters', {}),
                    status=job_data.get('status'),
                    message=job_data.get('message'),
                    stats=job_data.get('stats', {})
                )
                
                # Set timestamps
                if job_data.get('created_at'):
                    job.created_at = datetime.fromisoformat(job_data['created_at'])
                if job_data.get('started_at'):
                    job.started_at = datetime.fromisoformat(job_data['started_at'])
                if job_data.get('completed_at'):
                    job.completed_at = datetime.fromisoformat(job_data['completed_at'])
                
                # Calculate duration if needed
                if job.started_at and job.completed_at:
                    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
                
                # Add to session
                session.add(job)
                count += 1
            except Exception as e:
                logger.error(f"Error importing Sync job from {filename}: {str(e)}")
    
    # Commit changes
    session.commit()
    logger.info(f"Imported {count} Sync jobs from JSON files")

def main():
    """Run database setup and initialization."""
    logger.info("Starting TerraFusion Platform database setup")
    
    # Initialize database
    session = init_database()
    
    # Create sample counties
    create_sample_counties(session)
    
    # Create admin user
    create_admin_user(session)
    
    # Import existing jobs
    import_existing_jobs(session)
    
    logger.info("Database setup completed successfully")

if __name__ == "__main__":
    main()