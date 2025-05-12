#!/usr/bin/env python3
"""
Test script for the stale report expiration functionality.
This script:
1. Creates a report job
2. Updates it to RUNNING status
3. Modifies the started_at time to be older than the timeout
4. Runs the expire_stale_reports function
5. Verifies the job was marked as FAILED with the correct metadata
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from terrafusion_sync.core_models import ReportJob
from terrafusion_sync.plugins.reporting.service import (
    create_report_job,
    update_report_job_status,
    expire_stale_reports
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration (will use the environment variables from the main app)
from terrafusion_sync.database import engine

async def create_stale_report_job(db: AsyncSession):
    """Create a report job and make it stale for testing."""
    # Create a new report job
    job = await create_report_job(
        db=db,
        report_type="test_report",
        county_id="test_county",
        parameters={"test_param": "test_value"}
    )
    
    logger.info(f"Created test report job: {job.report_id}")
    
    # Update job to RUNNING status
    updated_job = await update_report_job_status(
        db=db,
        report_id=job.report_id,
        status="RUNNING",
        message="Test job started"
    )
    
    logger.info(f"Updated job to RUNNING status: {updated_job.status}")
    
    # Manually update the started_at time to make it appear stale
    # This is only for testing - in real usage, we'd wait for jobs to become stale naturally
    stale_time = datetime.utcnow() - timedelta(minutes=31)  # 31 minutes ago (longer than default 30 min timeout)
    
    stmt = (
        update(ReportJob)
        .where(ReportJob.report_id == job.report_id)
        .values(started_at=stale_time)
    )
    
    await db.execute(stmt)
    await db.commit()
    
    logger.info(f"Modified job started_at to {stale_time} to simulate staleness")
    
    # Return the job ID for later verification
    return job.report_id


async def verify_job_expired(db: AsyncSession, report_id: str) -> bool:
    """Verify that a job was properly expired."""
    # Get the job from the database
    from sqlalchemy import select
    
    query = select(ReportJob).where(ReportJob.report_id == report_id)
    result = await db.execute(query)
    job = result.scalars().first()
    
    if not job:
        logger.error(f"Job {report_id} not found for verification")
        return False
    
    # Check if job status is now FAILED
    if job.status != "FAILED":
        logger.error(f"Job {report_id} status is {job.status}, expected FAILED")
        return False
    
    # Check if result_metadata_json contains the timeout reason
    if not job.result_metadata_json or job.result_metadata_json.get("reason") != "timeout":
        logger.error(f"Job {report_id} metadata does not contain timeout reason: {job.result_metadata_json}")
        return False
    
    logger.info(f"Job {report_id} was successfully expired:")
    logger.info(f"  - Status: {job.status}")
    logger.info(f"  - Message: {job.message}")
    logger.info(f"  - Metadata: {job.result_metadata_json}")
    
    return True


async def main():
    """Run the stale report expiration test."""
    async with AsyncSession(engine) as db:
        try:
            # Create a stale job
            report_id = await create_stale_report_job(db)
            
            # Run the expire_stale_reports function
            count, expired_ids = await expire_stale_reports(db, timeout_minutes=30)
            
            logger.info(f"Expired {count} jobs: {expired_ids}")
            
            # Verify the job was properly expired
            success = await verify_job_expired(db, report_id)
            
            if success:
                logger.info("✅ Stale report expiration test passed!")
            else:
                logger.error("❌ Stale report expiration test failed!")
                
        except Exception as e:
            logger.error(f"Error during test: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())