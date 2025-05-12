#!/usr/bin/env python3
"""
Fixes the background task processing in Market Analysis router
to properly handle the AsyncEngine.
"""

import re

router_path = "terrafusion_sync/plugins/market_analysis/router.py"

# Read the file
with open(router_path, "r") as f:
    content = f.read()

# Fix the background task setup
old_engine_code = """        # Add background task to process the job
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = db.get_bind()
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )"""

new_engine_code = """        # Add background task to process the job
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        # Get database session factory directly from our own function
        from terrafusion_sync.database import get_db_session"""

content = content.replace(old_engine_code, new_engine_code)

# Fix the background task parameter
old_task_add = """        background_tasks.add_task(
            _process_market_analysis_job,
            job_id,
            request.analysis_type,
            request.county_id,
            request.parameters,
            async_session_factory
        )"""

new_task_add = """        background_tasks.add_task(
            _process_market_analysis_job,
            job_id,
            request.analysis_type,
            request.county_id,
            request.parameters,
            get_db_session
        )"""

content = content.replace(old_task_add, new_task_add)

# Fix the process job function to handle get_db_session
old_process_function = """async def _process_market_analysis_job(
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters: Optional[Dict[str, Any]],
    db_session_factory
):
    \"\"\"Background task to process a market analysis job.\"\"\"
    start_process_time = time.monotonic()
    job_final_status = "UNKNOWN"

    async with db_session_factory() as db:"""

new_process_function = """async def _process_market_analysis_job(
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters: Optional[Dict[str, Any]],
    db_session_factory
):
    \"\"\"Background task to process a market analysis job.\"\"\"
    start_process_time = time.monotonic()
    job_final_status = "UNKNOWN"

    # Get a session using the factory
    db = await anext(db_session_factory())"""

content = content.replace(old_process_function, new_process_function)

# Write the updated content back to the file
with open(router_path, "w") as f:
    f.write(content)

print("✅ Fixed background task processing in Market Analysis router.")