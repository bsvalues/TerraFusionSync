#!/usr/bin/env python3
"""
Standalone test for stale reports detection and handling.

This script tests the CDC Reconciliation feature for stale reports
by creating test reports with backdated timestamps and verifying
they are correctly marked as failed after the timeout period.
"""

import os
import sys
import uuid
import json
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stale_reports_test")

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import required modules
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

# Ensure the URL is compatible with asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_REPORT_TYPE = "test_stale_report"
TEST_PARAMETERS = {
    "test_param": "test_value",
    "year": 2025,
    "month": 5
}

async def setup_database():
    """Import models and ensure they're loaded."""
    # Import here to avoid circular imports
    from terrafusion_sync.core_models import ReportJob
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        # This is safe because FastAPI's startup does this anyway
        # await conn.run_sync(ReportJob.metadata.create_all)
        pass
    
    return ReportJob

async def clean_test_reports(db, ReportJob):
    """Clean up any existing test reports."""
    logger.info("Cleaning up existing test reports")
    
    stmt = select(ReportJob).where(
        (ReportJob.county_id == TEST_COUNTY_ID) &
        (ReportJob.report_type == TEST_REPORT_TYPE)
    )
    
    result = await db.execute(stmt)
    reports = result.scalars().all()
    
    for report in reports:
        logger.info(f"Deleting test report {report.report_id}")
        await db.delete(report)
    
    await db.commit()

async def create_stale_report(db, ReportJob):
    """Create a test report with backdated timestamps."""
    # Generate a unique report ID
    report_id = str(uuid.uuid4())
    
    # Create timestamp for 45 minutes ago
    stale_time = datetime.utcnow() - timedelta(minutes=45)
    
    # Create a report job with RUNNING status
    report = ReportJob(
        report_id=report_id,
        county_id=TEST_COUNTY_ID,
        report_type=TEST_REPORT_TYPE,
        status="RUNNING",
        parameters_json=TEST_PARAMETERS,
        created_at=stale_time,
        updated_at=stale_time,
        started_at=stale_time
    )
    
    logger.info(f"Creating stale report {report_id} with timestamp {stale_time.isoformat()}")
    
    db.add(report)
    await db.commit()
    
    return report_id

async def run_expire_stale_reports(db):
    """Run the expire_stale_reports function from the service."""
    from terrafusion_sync.plugins.reporting.service import expire_stale_reports
    
    logger.info("Running expire_stale_reports with 30 minute timeout")
    count, expired_ids = await expire_stale_reports(db, timeout_minutes=30)
    
    logger.info(f"Expired {count} reports: {expired_ids}")
    
    return count, expired_ids

async def verify_report_status(db, ReportJob, report_id):
    """Verify that the report has been marked as failed."""
    stmt = select(ReportJob).where(ReportJob.report_id == report_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        logger.error(f"Could not find report {report_id}")
        return False
    
    logger.info(f"Report {report_id} status: {report.status}")
    logger.info(f"Report message: {report.message}")
    
    if report.status == "FAILED" and "timeout" in report.message.lower():
        logger.info("✅ Report correctly marked as failed due to timeout")
        
        # Check metadata
        if report.result_metadata_json:
            metadata = report.result_metadata_json
            logger.info(f"Metadata: {json.dumps(metadata, indent=2)}")
            
            if metadata.get("reason") == "timeout":
                logger.info("✅ Metadata contains correct reason")
                return True
    
    logger.error("❌ Report not properly marked as failed")
    return False

async def main():
    """Run the stale reports test."""
    logger.info("Starting stale reports test")
    
    # Setup the database
    ReportJob = await setup_database()
    
    async with async_session() as db:
        # Clean up existing test reports
        await clean_test_reports(db, ReportJob)
        
        # Create a stale report
        report_id = await create_stale_report(db, ReportJob)
        
        # Run the expire_stale_reports function
        count, expired_ids = await run_expire_stale_reports(db)
        
        # Verify the report has been marked as failed
        success = await verify_report_status(db, ReportJob, report_id)
        
        # Clean up
        await clean_test_reports(db, ReportJob)
    
    if success:
        logger.info("✅ Stale reports test passed")
        return 0
    else:
        logger.error("❌ Stale reports test failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Error running stale reports test")
        sys.exit(1)