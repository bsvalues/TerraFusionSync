#!/usr/bin/env python3
"""
Test runner for reporting plugin functionality, including stale report expiration.

This script runs within the FastAPI application context to ensure
proper database session management.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.database import engine
from terrafusion_sync.core_models import ReportJob
from terrafusion_sync.plugins.reporting.service import (
    create_report_job,
    update_report_job_status,
    expire_stale_reports
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stale_reports_test")

async def test_stale_report_expiration():
    """Test the stale report expiration functionality."""
    logger.info("Starting stale report expiration test")
    
    async with AsyncSession(engine) as db:
        try:
            # Create a test report job
            job = await create_report_job(
                db=db,
                report_type="test_stale_report",
                county_id="TEST_COUNTY",
                parameters={"test": True}
            )
            report_id = job.report_id
            logger.info(f"Created test report job: {report_id}")
            
            # Set status to RUNNING
            await update_report_job_status(
                db=db,
                report_id=report_id,
                status="RUNNING",
                message="Test report running"
            )
            logger.info(f"Updated job status to RUNNING")
            
            # Backdate the started_at time to make it appear stale
            stale_start_time = datetime.utcnow() - timedelta(minutes=45)  # 45 min ago (past the 30 min threshold)
            
            update_stmt = (
                update(ReportJob)
                .where(ReportJob.report_id == report_id)
                .values(started_at=stale_start_time)
            )
            await db.execute(update_stmt)
            await db.commit()
            logger.info(f"Backdated job start time to {stale_start_time}")
            
            # Verify the job is in the expected state before running expiration
            query = select(ReportJob).where(ReportJob.report_id == report_id)
            result = await db.execute(query)
            job_before = result.scalars().first()
            
            if job_before and job_before.status == "RUNNING":
                logger.info(f"Job is in expected RUNNING state with start time {job_before.started_at}")
            else:
                logger.error(f"Job is not in expected state: {job_before.status if job_before else 'Not found'}")
                return False
            
            # Run the expire_stale_reports function
            count, expired_ids = await expire_stale_reports(db, timeout_minutes=30)
            logger.info(f"Expired {count} stale jobs: {expired_ids}")
            
            # Verify the job was marked as failed
            query = select(ReportJob).where(ReportJob.report_id == report_id)
            result = await db.execute(query)
            updated_job = result.scalars().first()
            
            if not updated_job:
                logger.error(f"Job {report_id} not found after expiration")
                return False
            
            logger.info(f"Job status after expiration: {updated_job.status}")
            logger.info(f"Job message: {updated_job.message}")
            logger.info(f"Job result metadata: {updated_job.result_metadata_json}")
            
            if updated_job.status == "FAILED" and updated_job.result_metadata_json and updated_job.result_metadata_json.get('reason') == 'timeout':
                logger.info("✅ Test passed: Job was correctly marked as failed due to timeout")
                return True
            else:
                logger.error("❌ Test failed: Job was not correctly marked as failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during test: {e}", exc_info=True)
            return False

async def main():
    """Run all reporting tests."""
    try:
        stale_reports_result = await test_stale_report_expiration()
        
        if stale_reports_result:
            logger.info("✅ All tests completed successfully!")
            return 0
        else:
            logger.error("❌ Some tests failed!")
            return 1
    except Exception as e:
        logger.error(f"Unhandled exception in tests: {e}", exc_info=True)
        return 2

if __name__ == "__main__":
    # Run the test and exit with appropriate code
    exit_code = asyncio.run(main())
    sys.exit(exit_code)