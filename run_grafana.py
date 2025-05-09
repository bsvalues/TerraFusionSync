#!/usr/bin/env python3
"""
Script to run Grafana in the Replit environment.
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
logger = logging.getLogger('grafana-runner')

# Grafana configuration
GRAFANA_PORT = 3000
GRAFANA_VERSION = "10.1.1"
GRAFANA_HOME = "/tmp/grafana"
GRAFANA_CONFIG_DIR = os.path.join(os.getcwd(), "grafana")

def check_grafana_binary():
    """Check if grafana-server binary exists."""
    try:
        result = subprocess.run(
            ['which', 'grafana-server'],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking grafana-server binary: {e}")
        return False

def install_grafana():
    """Install Grafana."""
    logger.info("Installing Grafana...")
    try:
        # Create directory for Grafana
        os.makedirs(GRAFANA_HOME, exist_ok=True)
        os.makedirs(os.path.join(GRAFANA_HOME, 'data'), exist_ok=True)
        os.makedirs(os.path.join(GRAFANA_HOME, 'logs'), exist_ok=True)
        
        # Download Grafana
        download_cmd = [
            'curl', '-L', 
            f'https://dl.grafana.com/oss/release/grafana-{GRAFANA_VERSION}.linux-amd64.tar.gz', 
            '-o', '/tmp/grafana.tar.gz'
        ]
        subprocess.run(download_cmd, check=True)
        
        # Extract Grafana
        extract_cmd = [
            'tar', '-xzf', '/tmp/grafana.tar.gz', 
            '-C', GRAFANA_HOME, 
            '--strip-components=1'
        ]
        subprocess.run(extract_cmd, check=True)
        
        # Create symlink to the grafana-server binary
        subprocess.run([
            'ln', '-sf', 
            os.path.join(GRAFANA_HOME, 'bin/grafana-server'), 
            '/usr/local/bin/grafana-server'
        ], check=True)
        
        logger.info("Grafana installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing Grafana: {e}")
        return False

def setup_grafana_provisioning():
    """Set up Grafana provisioning."""
    logger.info("Setting up Grafana provisioning...")
    try:
        # Create provisioning directories
        grafana_prov_dir = os.path.join(GRAFANA_HOME, 'conf/provisioning')
        os.makedirs(os.path.join(grafana_prov_dir, 'datasources'), exist_ok=True)
        os.makedirs(os.path.join(grafana_prov_dir, 'dashboards'), exist_ok=True)
        
        # Copy datasources from project to Grafana
        if os.path.exists(os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/datasources')):
            for file in os.listdir(os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/datasources')):
                src = os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/datasources', file)
                dst = os.path.join(grafana_prov_dir, 'datasources', file)
                logger.info(f"Copying datasource: {src} -> {dst}")
                subprocess.run(['cp', src, dst], check=True)
        
        # Copy dashboard provisioning from project to Grafana
        if os.path.exists(os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/dashboards')):
            for file in os.listdir(os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/dashboards')):
                src = os.path.join(GRAFANA_CONFIG_DIR, 'provisioning/dashboards', file)
                dst = os.path.join(grafana_prov_dir, 'dashboards', file)
                logger.info(f"Copying dashboard provisioning: {src} -> {dst}")
                subprocess.run(['cp', src, dst], check=True)
                
        # Create dashboards directory and copy dashboards
        os.makedirs(os.path.join(GRAFANA_HOME, 'dashboards'), exist_ok=True)
        if os.path.exists(os.path.join(GRAFANA_CONFIG_DIR, 'dashboards')):
            for file in os.listdir(os.path.join(GRAFANA_CONFIG_DIR, 'dashboards')):
                src = os.path.join(GRAFANA_CONFIG_DIR, 'dashboards', file)
                dst = os.path.join(GRAFANA_HOME, 'dashboards', file)
                logger.info(f"Copying dashboard: {src} -> {dst}")
                subprocess.run(['cp', src, dst], check=True)
                
        logger.info("Grafana provisioning set up successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up Grafana provisioning: {e}")
        return False

def run_grafana():
    """Run Grafana with the specified configuration."""
    logger.info(f"Starting Grafana on port {GRAFANA_PORT}")
    
    # Check if Grafana is already running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'grafana-server'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            logger.warning("Grafana is already running, killing existing process")
            subprocess.run(['pkill', '-f', 'grafana-server'], check=False)
            time.sleep(2)  # Give it time to shut down
    except Exception as e:
        logger.error(f"Error checking if Grafana is running: {e}")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'GF_SERVER_HTTP_PORT': str(GRAFANA_PORT),
        'GF_PATHS_DATA': os.path.join(GRAFANA_HOME, 'data'),
        'GF_PATHS_LOGS': os.path.join(GRAFANA_HOME, 'logs'),
        'GF_PATHS_PLUGINS': os.path.join(GRAFANA_HOME, 'plugins'),
        'GF_PATHS_PROVISIONING': os.path.join(GRAFANA_HOME, 'conf/provisioning'),
        'GF_SECURITY_ADMIN_USER': 'admin',
        'GF_SECURITY_ADMIN_PASSWORD': 'admin',
        'GF_USERS_ALLOW_SIGN_UP': 'false',
        'GF_LOG_LEVEL': 'info'
    })
    
    # Start Grafana
    try:
        cmd = [
            'grafana-server',
            '--homepath=' + GRAFANA_HOME,
            '--config=' + os.path.join(GRAFANA_HOME, 'conf/defaults.ini')
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Set up signal handlers to kill grafana gracefully
        def signal_handler(sig, frame):
            logger.info("Received signal, shutting down Grafana")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Print startup message
        logger.info(f"Grafana is running at: http://localhost:{GRAFANA_PORT}")
        logger.info("Default credentials: admin/admin")
        logger.info("Use Ctrl+C to stop")
        
        # Monitor the process
        while True:
            line = process.stderr.readline()
            if line:
                logger.info(f"Grafana: {line.strip()}")
            
            line = process.stdout.readline()
            if line:
                logger.info(f"Grafana: {line.strip()}")
            
            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"Grafana exited with code {process.returncode}")
                break
            
            time.sleep(0.1)
    
    except Exception as e:
        logger.error(f"Error running Grafana: {e}")
        return False
    
    return True

def main():
    """Main function."""
    logger.info("Starting Grafana Runner")
    
    # Check if grafana binary exists
    if not check_grafana_binary():
        logger.info("Grafana binary not found, installing...")
        if not install_grafana():
            logger.error("Failed to install Grafana")
            return 1
    
    # Set up Grafana provisioning
    if not setup_grafana_provisioning():
        logger.error("Failed to set up Grafana provisioning")
        return 1
    
    # Run Grafana
    if not run_grafana():
        logger.error("Failed to run Grafana")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())