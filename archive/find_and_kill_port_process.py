#!/usr/bin/env python
"""
Script to find and kill a process using a specific port
"""

import os
import sys
import socket
import signal
import logging
import time
import subprocess
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_process_using_port(port: int) -> Optional[int]:
    """
    Find the process ID using the specified port using /proc/net/tcp
    
    Args:
        port: Port number to check
        
    Returns:
        Process ID or None if no process is using the port
    """
    try:
        # Convert port to hexadecimal format (network byte order)
        hex_port = format(port, '04X')
        
        # Read the TCP connections
        with open('/proc/net/tcp', 'r') as f:
            # Skip header line
            next(f)
            for line in f:
                parts = line.strip().split()
                # Local address is in the format: 0100007F:1388 (127.0.0.1:5000)
                # where the port is after the colon in hex
                local_addr = parts[1]
                local_port = local_addr.split(':')[1]
                
                if local_port.lower() == hex_port.lower():
                    # Get inode
                    inode = parts[9]
                    
                    # Find process using this inode
                    for pid in os.listdir('/proc'):
                        if not pid.isdigit():
                            continue
                        
                        try:
                            fd_dir = f'/proc/{pid}/fd'
                            if not os.path.isdir(fd_dir):
                                continue
                                
                            for fd in os.listdir(fd_dir):
                                try:
                                    fd_path = os.readlink(f'{fd_dir}/{fd}')
                                    if f'socket:[{inode}]' in fd_path:
                                        return int(pid)
                                except (FileNotFoundError, PermissionError):
                                    continue
                        except (FileNotFoundError, PermissionError):
                            continue
    except Exception as e:
        logger.error(f"Error finding process using port {port}: {e}")
    
    return None

def find_process_using_ss(port: int) -> Optional[int]:
    """
    Find process using port using the ss command
    
    Args:
        port: Port number to check
        
    Returns:
        Process ID or None if no process is using the port
    """
    try:
        output = subprocess.check_output(['ss', '-tlnp'], text=True)
        for line in output.splitlines():
            if f':{port}' in line and 'users:' in line:
                # Extract PID from output
                # Format: users:(("process_name",pid=12345,fd=3))
                pid_part = line.split('pid=')[1].split(',')[0]
                return int(pid_part)
    except (subprocess.SubprocessError, ValueError, IndexError):
        pass
    return None

def kill_process(pid: int, force: bool = False) -> bool:
    """
    Kill a process by its PID
    
    Args:
        pid: Process ID to kill
        force: Whether to use SIGKILL (force) instead of SIGTERM
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Killing process {pid}")
        os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
        
        # Wait a bit to make sure the process is terminated
        time.sleep(2)
        
        # Check if the process still exists
        try:
            os.kill(pid, 0)  # Signal 0 doesn't send a signal but checks if process exists
            
            if force:
                logger.error(f"Process {pid} could not be killed even with SIGKILL")
                return False
            else:
                # Try with SIGKILL
                logger.info(f"Process {pid} did not terminate with SIGTERM, trying SIGKILL")
                return kill_process(pid, force=True)
        except ProcessLookupError:
            # Process is gone
            logger.info(f"Process {pid} successfully terminated")
            return True
    except ProcessLookupError:
        logger.info(f"Process {pid} does not exist")
        return True
    except PermissionError:
        logger.error(f"No permission to kill process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def main():
    """Main entry point for the script"""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PORT")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid port number: {sys.argv[1]}")
        sys.exit(1)
    
    logger.info(f"Looking for process using port {port}")
    
    # Try both methods
    pid = find_process_using_port(port)
    if pid is None:
        pid = find_process_using_ss(port)
    
    if pid is None:
        logger.info(f"No process found using port {port}")
        sys.exit(0)
    
    logger.info(f"Found process {pid} using port {port}")
    
    # Try to get command line of the process
    try:
        with open(f'/proc/{pid}/cmdline', 'r') as f:
            cmdline = f.read().replace('\0', ' ')
            logger.info(f"Process command line: {cmdline}")
    except (FileNotFoundError, PermissionError):
        logger.info(f"Could not read command line for process {pid}")
    
    # Kill the process
    if kill_process(pid):
        logger.info(f"Successfully killed process {pid}")
        sys.exit(0)
    else:
        logger.error(f"Failed to kill process {pid}")
        sys.exit(1)

if __name__ == "__main__":
    main()