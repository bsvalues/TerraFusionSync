#!/usr/bin/env python3
"""
TerraFusion Rust Bridge

This script provides a bridge between the existing Python services
and the new Rust-based services, allowing for a gradual migration.

It can be used to start, stop, and monitor the Rust-based services.
"""

import os
import sys
import time
import signal
import subprocess
import logging
import json
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("terrarust_bridge")

# Constants
RUST_DIR = Path("terrarust")
SERVICES = ["api_gateway", "sync_service", "gis_export"]
DEFAULT_PORTS = {
    "api_gateway": 5000,
    "sync_service": 5001,
    "gis_export": 8080
}


def check_rust_compiled(service_name):
    """Check if the Rust service is compiled."""
    bin_path = RUST_DIR / "target" / "release" / service_name
    return bin_path.exists()


def compile_rust_services(services=None):
    """Compile the specified Rust services or all services if none specified."""
    if services is None:
        services = SERVICES
    
    logger.info(f"Compiling Rust services: {', '.join(services)}")
    
    # Navigate to the Rust workspace directory
    os.chdir(RUST_DIR)
    
    # Build the services
    for service in services:
        logger.info(f"Compiling {service}...")
        result = subprocess.run(
            ["cargo", "build", "--release", "--package", service],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to compile {service}: {result.stderr}")
            return False
        
        logger.info(f"Successfully compiled {service}")
    
    # Return to the original directory
    os.chdir("..")
    return True


def start_rust_service(service_name, port=None):
    """Start a Rust-based service."""
    if port is None:
        port = DEFAULT_PORTS.get(service_name)
    
    bin_path = RUST_DIR / "target" / "release" / service_name
    
    if not bin_path.exists():
        logger.error(f"Cannot start {service_name}: binary not found at {bin_path}")
        return None
    
    logger.info(f"Starting {service_name} on port {port}...")
    
    # Define environment variables
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["DATABASE_URL"] = os.environ.get("DATABASE_URL", "")
    env["RUST_LOG"] = "info"
    
    # Start the process
    try:
        proc = subprocess.Popen(
            [str(bin_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit to make sure it started
        time.sleep(2)
        
        # Check if the process is still running
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            logger.error(f"Service {service_name} failed to start: {stderr}")
            return None
        
        logger.info(f"Service {service_name} started with PID {proc.pid}")
        return proc
    
    except Exception as e:
        logger.error(f"Error starting {service_name}: {e}")
        return None


def stop_rust_service(proc):
    """Stop a running Rust-based service."""
    if proc is None:
        return
    
    logger.info(f"Stopping service with PID {proc.pid}...")
    
    # Try to terminate gracefully first
    proc.terminate()
    
    try:
        # Wait for up to 5 seconds for the process to terminate
        proc.wait(timeout=5)
        logger.info(f"Service with PID {proc.pid} terminated gracefully")
    except subprocess.TimeoutExpired:
        # If it's still running, kill it
        logger.warning(f"Service with PID {proc.pid} did not terminate gracefully, killing it")
        proc.kill()
        proc.wait()


def check_service_health(service_name, port=None):
    """Check the health of a running service."""
    if port is None:
        port = DEFAULT_PORTS.get(service_name)
    
    import requests
    
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Health check for {service_name}: {json.dumps(health_data, indent=2)}")
            return True
        else:
            logger.warning(f"Health check for {service_name} failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error checking health for {service_name}: {e}")
        return False


def start_gis_export_service():
    """Start the GIS Export service on port 8080 for the TerraFusion workflow."""
    # Check if the service is compiled
    if not check_rust_compiled("gis_export"):
        logger.info("GIS Export service is not compiled, compiling now...")
        if not compile_rust_services(["gis_export"]):
            logger.error("Failed to compile GIS Export service, cannot start")
            return None
    
    # Start the service
    proc = start_rust_service("gis_export", 8080)
    
    if proc is None:
        logger.error("Failed to start GIS Export service")
        return None
    
    # Check the health
    if not check_service_health("gis_export", 8080):
        logger.warning("GIS Export service started but health check failed")
    
    return proc


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="TerraFusion Rust Bridge")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile Rust services")
    compile_parser.add_argument(
        "services",
        nargs="*",
        help="Services to compile (default: all)",
        choices=SERVICES + [["all"]]
    )
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a Rust service")
    start_parser.add_argument(
        "service",
        help="Service to start",
        choices=SERVICES
    )
    start_parser.add_argument(
        "--port",
        type=int,
        help="Port to use (default: service-specific default)",
        default=None
    )
    
    # Run GIS Export command (for workflow)
    gis_export_parser = subparsers.add_parser(
        "run_gis_export",
        help="Start the GIS Export service for TerraFusion workflow"
    )
    
    args = parser.parse_args()
    
    if args.command == "compile":
        services_to_compile = args.services
        if not services_to_compile or "all" in services_to_compile:
            services_to_compile = SERVICES
        
        success = compile_rust_services(services_to_compile)
        sys.exit(0 if success else 1)
    
    elif args.command == "start":
        proc = start_rust_service(args.service, args.port)
        
        if proc is None:
            sys.exit(1)
        
        # Keep the service running and handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            stop_rust_service(proc)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for the process to complete
        try:
            proc.wait()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            stop_rust_service(proc)
    
    elif args.command == "run_gis_export":
        proc = start_gis_export_service()
        
        if proc is None:
            sys.exit(1)
        
        # Keep the service running and handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            stop_rust_service(proc)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for the process to complete
        try:
            proc.wait()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            stop_rust_service(proc)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()