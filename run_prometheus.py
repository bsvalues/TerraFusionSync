#!/usr/bin/env python3
"""
Script to run Prometheus in the Replit environment.
"""

import os
import subprocess
import sys
import time
import signal
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('prometheus-runner')

# Prometheus configuration
PROMETHEUS_PORT = 9090
PROMETHEUS_CONFIG = os.path.join(os.getcwd(), 'prometheus.yml')

def check_prometheus_binary():
    """Check if prometheus binary exists."""
    try:
        result = subprocess.run(
            ['which', 'prometheus'],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking prometheus binary: {e}")
        return False

def install_prometheus():
    """Install Prometheus."""
    logger.info("Installing Prometheus...")
    try:
        # Create directory for Prometheus
        os.makedirs('/tmp/prometheus', exist_ok=True)
        
        # Download Prometheus
        download_cmd = [
            'curl', '-L', 
            'https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz', 
            '-o', '/tmp/prometheus.tar.gz'
        ]
        subprocess.run(download_cmd, check=True)
        
        # Extract Prometheus
        extract_cmd = [
            'tar', '-xzf', '/tmp/prometheus.tar.gz', 
            '-C', '/tmp/prometheus', 
            '--strip-components=1'
        ]
        subprocess.run(extract_cmd, check=True)
        
        # Create symlink to the prometheus binary
        subprocess.run([
            'ln', '-sf', 
            '/tmp/prometheus/prometheus', 
            '/usr/local/bin/prometheus'
        ], check=True)
        
        logger.info("Prometheus installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing Prometheus: {e}")
        return False

def run_prometheus():
    """Run Prometheus with the specified configuration."""
    logger.info(f"Starting Prometheus with config: {PROMETHEUS_CONFIG}")
    
    # Check if Prometheus is already running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'prometheus'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            logger.warning("Prometheus is already running, killing existing process")
            subprocess.run(['pkill', '-f', 'prometheus'], check=False)
            time.sleep(2)  # Give it time to shut down
    except Exception as e:
        logger.error(f"Error checking if Prometheus is running: {e}")
    
    # Start Prometheus
    try:
        cmd = [
            'prometheus',
            '--config.file=' + PROMETHEUS_CONFIG,
            '--web.listen-address=0.0.0.0:' + str(PROMETHEUS_PORT),
            '--storage.tsdb.path=/tmp/prometheus-data',
            '--web.enable-lifecycle',
            '--log.level=info'
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Set up signal handlers to kill prometheus gracefully
        def signal_handler(sig, frame):
            logger.info("Received signal, shutting down Prometheus")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Print startup message
        logger.info(f"Prometheus is running at: http://localhost:{PROMETHEUS_PORT}")
        logger.info("Use Ctrl+C to stop")
        
        # Monitor the process
        while True:
            line = process.stderr.readline()
            if line:
                logger.info(f"Prometheus: {line.strip()}")
            
            line = process.stdout.readline()
            if line:
                logger.info(f"Prometheus: {line.strip()}")
            
            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"Prometheus exited with code {process.returncode}")
                break
            
            time.sleep(0.1)
    
    except Exception as e:
        logger.error(f"Error running Prometheus: {e}")
        return False
    
    return True

def main():
    """Main function."""
    logger.info("Starting Prometheus Runner")
    
    # Check if prometheus binary exists
    if not check_prometheus_binary():
        logger.info("Prometheus binary not found, installing...")
        if not install_prometheus():
            logger.error("Failed to install Prometheus")
            return 1
    
    # Run Prometheus
    if not run_prometheus():
        logger.error("Failed to run Prometheus")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())