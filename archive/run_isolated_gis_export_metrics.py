#!/usr/bin/env python3
"""
Run Isolated GIS Export Metrics API

This script runs the isolated GIS Export metrics API on a separate port
to avoid conflicts with the main SyncService.
"""

import os
import sys
import time
import argparse
import logging
import uvicorn
from terrafusion_sync.plugins.gis_export.isolated_metrics_api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the isolated GIS Export metrics API."""
    parser = argparse.ArgumentParser(description="Run Isolated GIS Export Metrics API")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8090, help='Port to use')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    logger.info(f"Starting Isolated GIS Export Metrics API on {args.host}:{args.port}")
    
    uvicorn.run(
        "terrafusion_sync.plugins.gis_export.isolated_metrics_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()