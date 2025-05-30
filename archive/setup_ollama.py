#!/usr/bin/env python3
"""
TerraFusion Platform - Ollama Setup Script

This script helps set up Ollama for offline AI capabilities.
Perfect for county networks with limited internet connectivity.
"""

import os
import sys
import subprocess
import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ollama_installed():
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            logger.warning("Ollama command found but returned error")
            return False
    except FileNotFoundError:
        logger.info("Ollama is not installed")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("Ollama command timed out")
        return False

def install_ollama():
    """Install Ollama using the official installer."""
    logger.info("Installing Ollama...")
    
    try:
        # Download and run Ollama installer
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            install_cmd = 'curl -fsSL https://ollama.ai/install.sh | sh'
            result = subprocess.run(install_cmd, shell=True, 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info("Ollama installed successfully")
                return True
            else:
                logger.error(f"Ollama installation failed: {result.stderr}")
                return False
        else:
            logger.warning("Automatic installation not supported on Windows")
            logger.info("Please download Ollama from https://ollama.ai and install manually")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Ollama installation timed out")
        return False
    except Exception as e:
        logger.error(f"Ollama installation error: {e}")
        return False

def start_ollama_service():
    """Start the Ollama service."""
    logger.info("Starting Ollama service...")
    
    try:
        # Start Ollama in background
        if sys.platform.startswith('linux'):
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(['ollama', 'serve'])
        
        # Wait for service to start
        time.sleep(5)
        
        # Check if service is running
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=10)
            if response.status_code == 200:
                logger.info("Ollama service is running")
                return True
            else:
                logger.warning("Ollama service may not be ready yet")
                return False
        except requests.exceptions.RequestException:
            logger.warning("Could not connect to Ollama service")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start Ollama service: {e}")
        return False

def pull_model(model_name="llama2"):
    """Download and pull an AI model."""
    logger.info(f"Downloading AI model: {model_name}")
    logger.info("This may take several minutes depending on your internet connection...")
    
    try:
        result = subprocess.run(['ollama', 'pull', model_name], 
                              capture_output=True, text=True, timeout=1800)  # 30 min timeout
        if result.returncode == 0:
            logger.info(f"Model {model_name} downloaded successfully")
            return True
        else:
            logger.error(f"Failed to download model: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Model download timed out (30 minutes)")
        return False
    except Exception as e:
        logger.error(f"Model download error: {e}")
        return False

def test_ai_functionality():
    """Test AI functionality with a simple query."""
    logger.info("Testing AI functionality...")
    
    try:
        test_data = {
            "model": "llama2",
            "prompt": "Summarize the benefits of GIS technology for county government in 2 sentences.",
            "stream": False,
            "options": {
                "num_predict": 100,
                "temperature": 0.7
            }
        }
        
        response = requests.post('http://localhost:11434/api/generate', 
                               json=test_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            if ai_response:
                logger.info("AI test successful!")
                logger.info(f"AI Response: {ai_response}")
                return True
            else:
                logger.warning("AI responded but with empty content")
                return False
        else:
            logger.error(f"AI test failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"AI test failed: {e}")
        return False

def setup_environment_variables():
    """Set up environment variables for Ollama."""
    env_vars = {
        'OLLAMA_URL': 'http://localhost:11434',
        'AI_MODEL_NAME': 'llama2',
        'AI_MAX_TOKENS': '2000',
        'AI_TEMPERATURE': '0.7',
        'ENABLE_CLOUD_AI': 'false'
    }
    
    logger.info("Setting up environment variables...")
    
    # Check if .env file exists
    env_file = '.env'
    env_content = []
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Add or update environment variables
    updated = False
    for key, value in env_vars.items():
        found = False
        for i, line in enumerate(env_content):
            if line.startswith(f'{key}='):
                env_content[i] = f'{key}={value}\n'
                found = True
                break
        
        if not found:
            env_content.append(f'{key}={value}\n')
            updated = True
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    logger.info(f"Environment variables configured in {env_file}")

def main():
    """Main setup function."""
    logger.info("🤖 Setting up Ollama AI for TerraFusion Platform")
    logger.info("=" * 60)
    
    # Step 1: Check if Ollama is installed
    if not check_ollama_installed():
        logger.info("Ollama not found. Attempting installation...")
        if not install_ollama():
            logger.error("❌ Failed to install Ollama")
            logger.info("Please install Ollama manually from https://ollama.ai")
            return False
    
    # Step 2: Start Ollama service
    if not start_ollama_service():
        logger.error("❌ Failed to start Ollama service")
        return False
    
    # Step 3: Download AI model
    logger.info("Checking for AI model...")
    if not pull_model("llama2"):
        logger.warning("⚠️  Failed to download llama2 model")
        logger.info("You can try downloading manually with: ollama pull llama2")
        return False
    
    # Step 4: Test AI functionality
    if not test_ai_functionality():
        logger.warning("⚠️  AI test failed")
        return False
    
    # Step 5: Setup environment variables
    setup_environment_variables()
    
    logger.info("=" * 60)
    logger.info("✅ Ollama AI setup completed successfully!")
    logger.info("")
    logger.info("Your TerraFusion Platform now has AI capabilities:")
    logger.info("• Intelligent GIS export analysis")
    logger.info("• Smart data synchronization insights") 
    logger.info("• Automated report generation")
    logger.info("• Natural language data summaries")
    logger.info("")
    logger.info("Test the AI with: curl http://localhost:5000/api/v1/ai/demo")
    logger.info("")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)