#!/usr/bin/env python
"""
GIS Export Service Runner

This script launches the simplified GIS Export API service
for testing and development.
"""

import os
import sys
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting GIS Export Service")
    
    # Ensure environment variable is set before importing any modules
    os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"
    
    # Run the server
    port = int(os.environ.get("PORT", 8083))
    logger.info(f"GIS Export Service will run on port {port}")
    
    # Run server using uvicorn
    uvicorn.run(
        "simplified_gis_export_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )