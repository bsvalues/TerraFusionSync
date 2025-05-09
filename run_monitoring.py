#!/usr/bin/env python3
"""
Script to run both Prometheus and Grafana monitoring together in the Replit environment.
"""

import os
import subprocess
import sys
import time
import signal
import logging
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('monitoring-runner')

# Configuration
PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', 9090))
GRAFANA_PORT = int(os.environ.get('GRAFANA_PORT', 3000))

def run_prometheus():
    """Run Prometheus in a separate process."""
    logger.info("Starting Prometheus...")
    try:
        prometheus_script = os.path.join(os.getcwd(), 'run_prometheus.py')
        process = subprocess.Popen(
            ['python3', prometheus_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor the process output
        def monitor_output():
            while True:
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        logger.info(f"Prometheus: {line.strip()}")
                
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        logger.info(f"Prometheus: {line.strip()}")
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.error(f"Prometheus exited with code {process.returncode}")
                    break
                    
                time.sleep(0.1)
        
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()
        
        return process
        
    except Exception as e:
        logger.error(f"Error starting Prometheus: {e}")
        return None

def run_grafana():
    """Run Grafana in a separate process."""
    logger.info("Starting Grafana...")
    try:
        grafana_script = os.path.join(os.getcwd(), 'run_grafana.py')
        process = subprocess.Popen(
            ['python3', grafana_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor the process output
        def monitor_output():
            while True:
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        logger.info(f"Grafana: {line.strip()}")
                
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        logger.info(f"Grafana: {line.strip()}")
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.error(f"Grafana exited with code {process.returncode}")
                    break
                    
                time.sleep(0.1)
        
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()
        
        return process
        
    except Exception as e:
        logger.error(f"Error starting Grafana: {e}")
        return None

def main():
    """Main function."""
    logger.info("Starting TerraFusion Monitoring Stack")
    
    # Start Prometheus
    prometheus_process = run_prometheus()
    if not prometheus_process:
        logger.error("Failed to start Prometheus")
        return 1
    
    # Wait for Prometheus to be available
    logger.info(f"Waiting for Prometheus to be available at http://localhost:{PROMETHEUS_PORT}...")
    for _ in range(30):  # Wait up to 30 seconds
        try:
            import requests
            response = requests.get(f"http://localhost:{PROMETHEUS_PORT}")
            if response.status_code == 200:
                logger.info("Prometheus is available")
                break
        except Exception:
            pass
        time.sleep(1)
    
    # Start Grafana
    grafana_process = run_grafana()
    if not grafana_process:
        logger.error("Failed to start Grafana")
        prometheus_process.terminate()
        return 1
    
    # Print access info
    logger.info("\n" + "="*50)
    logger.info("TerraFusion Monitoring Stack is running!")
    logger.info("Prometheus UI: http://localhost:%s", PROMETHEUS_PORT)
    logger.info("Grafana UI: http://localhost:%s", GRAFANA_PORT)
    logger.info("Grafana default credentials: admin/admin")
    logger.info("="*50 + "\n")
    
    # Set up signal handlers to kill both processes gracefully
    def signal_handler(sig, frame):
        logger.info("Received signal, shutting down monitoring stack")
        grafana_process.terminate()
        prometheus_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Press Ctrl+C to stop")
    
    # Wait for both processes to complete
    grafana_process.wait()
    prometheus_process.wait()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())