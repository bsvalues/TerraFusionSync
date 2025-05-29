"""
TerraFusion Production Deployment Package

Complete production deployment system for county implementation.
Includes validation, configuration, and deployment scripts.
"""

import os
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TerraFusionDeploymentPackager:
    """
    Production deployment packager for TerraFusion Platform.
    
    Creates complete deployment packages for county production environments.
    """
    
    def __init__(self):
        """Initialize deployment packager."""
        self.deployment_dir = Path("deployment_packages")
        self.package_name = f"terrafusion_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.package_path = self.deployment_dir / self.package_name
        
        # Required production files
        self.core_files = [
            "app.py",
            "main.py",
            "models.py",
            "requirements.txt",
            "pyproject.toml",
            "Dockerfile.api-gateway",
            "Dockerfile.sync-service",
            "docker-compose.yml"
        ]
        
        self.service_modules = [
            "gis_export.py",
            "sync_service.py",
            "benton_district_lookup.py",
            "narrator_ai_plugin.py",
            "exemption_seer_ai.py",
            "enhanced_api_endpoints.py",
            "api_extensions.py",
            "rbac_manager.py",
            "monitoring.py",
            "backup_scheduler.py",
            "backup_utilities.py"
        ]
        
        self.implementation_modules = [
            "historical_ai_enrichment.py",
            "pacs_api_sync_suite.py",
            "compliance_tracking_layer.py",
            "narrative_intelligence_uplift.py",
            "system_packaging_deployment.py",
            "terrafusion_full_implementation.py"
        ]
        
        self.config_files = [
            ".env.example",
            ".replit",
            "county_users.json"
        ]
        
        self.documentation = [
            "README.md",
            "README_QUICKSTART_WINDOWS.md",
            "README_IT.md",
            "DUO_SECURITY_IMPLEMENTATION_COMPLETE.md",
            "PACS_INTEGRATION_PRD.md",
            "DEPLOYMENT_STRATEGY.md"
        ]
    
    def create_deployment_package(self) -> Path:
        """
        Create complete deployment package.
        
        Returns:
            Path: Path to the created deployment package
        """
        logger.info("🚀 Creating TerraFusion Production Deployment Package")
        
        # Create deployment directory
        self.deployment_dir.mkdir(exist_ok=True)
        self.package_path.mkdir(exist_ok=True)
        
        # Copy core application files
        self._copy_core_files()
        
        # Copy service modules
        self._copy_service_modules()
        
        # Copy implementation modules
        self._copy_implementation_modules()
        
        # Copy configuration files
        self._copy_config_files()
        
        # Copy documentation
        self._copy_documentation()
        
        # Create deployment scripts
        self._create_deployment_scripts()
        
        # Create production environment template
        self._create_production_env_template()
        
        # Create validation scripts
        self._create_validation_scripts()
        
        # Create deployment manifest
        self._create_deployment_manifest()
        
        logger.info(f"✅ Deployment package created: {self.package_path}")
        return self.package_path
    
    def _copy_core_files(self):
        """Copy core application files."""
        logger.info("📋 Copying core application files...")
        
        for file in self.core_files:
            if Path(file).exists():
                shutil.copy2(file, self.package_path / file)
                logger.info(f"✅ Copied: {file}")
            else:
                logger.warning(f"⚠️ Missing core file: {file}")
    
    def _copy_service_modules(self):
        """Copy service modules."""
        logger.info("🔧 Copying service modules...")
        
        for module in self.service_modules:
            if Path(module).exists():
                shutil.copy2(module, self.package_path / module)
                logger.info(f"✅ Copied: {module}")
            else:
                logger.warning(f"⚠️ Missing service module: {module}")
    
    def _copy_implementation_modules(self):
        """Copy implementation modules."""
        logger.info("🧠 Copying implementation modules...")
        
        for module in self.implementation_modules:
            if Path(module).exists():
                shutil.copy2(module, self.package_path / module)
                logger.info(f"✅ Copied: {module}")
            else:
                logger.warning(f"⚠️ Missing implementation module: {module}")
    
    def _copy_config_files(self):
        """Copy configuration files."""
        logger.info("⚙️ Copying configuration files...")
        
        for config in self.config_files:
            if Path(config).exists():
                shutil.copy2(config, self.package_path / config)
                logger.info(f"✅ Copied: {config}")
            else:
                logger.warning(f"⚠️ Missing config file: {config}")
    
    def _copy_documentation(self):
        """Copy documentation files."""
        logger.info("📚 Copying documentation...")
        
        # Create docs directory
        docs_dir = self.package_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        for doc in self.documentation:
            if Path(doc).exists():
                shutil.copy2(doc, docs_dir / doc)
                logger.info(f"✅ Copied: {doc}")
            else:
                logger.warning(f"⚠️ Missing documentation: {doc}")
    
    def _create_deployment_scripts(self):
        """Create deployment scripts."""
        logger.info("📜 Creating deployment scripts...")
        
        # Windows deployment script
        windows_script = self.package_path / "deploy_windows.bat"
        with open(windows_script, 'w') as f:
            f.write("""@echo off
echo TerraFusion Production Deployment
echo ==================================

echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available
    echo Please ensure Docker Compose is installed
    pause
    exit /b 1
)

echo Building TerraFusion containers...
docker-compose build

echo Starting TerraFusion services...
docker-compose up -d

echo Waiting for services to start...
timeout /t 30

echo Running deployment validation...
python terrafusion_deployment_validator.py

echo TerraFusion deployment complete!
echo Access the platform at: http://localhost:5000
pause
""")
        
        # Linux deployment script
        linux_script = self.package_path / "deploy_linux.sh"
        with open(linux_script, 'w') as f:
            f.write("""#!/bin/bash
echo "TerraFusion Production Deployment"
echo "=================================="

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Please install Docker and try again"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not available"
    echo "Please install Docker Compose and try again"
    exit 1
fi

echo "Building TerraFusion containers..."
docker-compose build

echo "Starting TerraFusion services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 30

echo "Running deployment validation..."
python3 terrafusion_deployment_validator.py

echo "TerraFusion deployment complete!"
echo "Access the platform at: http://localhost:5000"
""")
        
        # Make Linux script executable
        os.chmod(linux_script, 0o755)
        
        logger.info("✅ Deployment scripts created")
    
    def _create_production_env_template(self):
        """Create production environment template."""
        logger.info("🔐 Creating production environment template...")
        
        env_template = self.package_path / ".env.production.template"
        with open(env_template, 'w') as f:
            f.write("""# TerraFusion Production Environment Configuration
# Copy this file to .env and configure with your county's credentials

# Database Configuration (Required)
DATABASE_URL=postgresql://username:password@localhost:5432/terrafusion_production

# Session Security (Required - Generate a secure random key)
SESSION_SECRET=your_secure_session_secret_key_here

# Duo MFA Configuration (Required for production security)
DUO_INTEGRATION_KEY=your_duo_integration_key
DUO_SECRET_KEY=your_duo_secret_key  
DUO_API_HOSTNAME=your_duo_api_hostname

# PACS API Configuration (Required for county data integration)
PACS_API_URL=https://your_county_pacs_api_url
PACS_API_KEY=your_pacs_api_key
PACS_API_SECRET=your_pacs_api_secret

# County Configuration
COUNTY_ID=your_county_id
COUNTY_NAME=Your County Name
COUNTY_STATE=Your State

# AI Configuration (Optional - for enhanced functionality)
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=your_openai_api_key_if_using_openai

# Monitoring Configuration (Optional)
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=hourly
BACKUP_RETENTION_DAYS=30

# Production Settings
FLASK_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security Settings
SECURE_COOKIES=true
SESSION_TIMEOUT=3600
CSRF_PROTECTION=true
""")
        
        logger.info("✅ Production environment template created")
    
    def _create_validation_scripts(self):
        """Create validation scripts."""
        logger.info("✅ Creating validation scripts...")
        
        # Copy the comprehensive test suite
        test_suite_source = Path("terrafusion_comprehensive_test_suite.py")
        if test_suite_source.exists():
            shutil.copy2(test_suite_source, self.package_path / "terrafusion_deployment_validator.py")
            logger.info("✅ Deployment validator created")
        else:
            logger.warning("⚠️ Test suite not found for deployment validation")
    
    def _create_deployment_manifest(self):
        """Create deployment manifest."""
        logger.info("📋 Creating deployment manifest...")
        
        manifest = {
            "package_name": self.package_name,
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "description": "TerraFusion Platform Production Deployment Package",
            "components": {
                "api_gateway": "Flask-based API Gateway with RBAC and security",
                "sync_service": "FastAPI-based PACS integration service",
                "gis_export": "District-aware GIS export functionality",
                "ai_engines": "NarratorAI and ExemptionSeer AI analysis",
                "authentication": "Duo MFA and RBAC security system",
                "monitoring": "Prometheus and Grafana monitoring",
                "backup": "Automated backup and recovery system"
            },
            "requirements": {
                "database": "PostgreSQL 12+ with county data",
                "security": "Duo Security account for MFA",
                "pacs": "County PACS API credentials",
                "infrastructure": "Docker and Docker Compose"
            },
            "deployment_steps": [
                "Configure .env file with county credentials",
                "Run deployment script (deploy_windows.bat or deploy_linux.sh)",
                "Validate deployment with terrafusion_deployment_validator.py",
                "Access platform at http://localhost:5000"
            ]
        }
        
        manifest_file = self.package_path / "deployment_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info("✅ Deployment manifest created")
    
    def create_installation_package(self) -> Path:
        """
        Create compressed installation package.
        
        Returns:
            Path: Path to the compressed package
        """
        logger.info("📦 Creating compressed installation package...")
        
        package_file = self.deployment_dir / f"{self.package_name}.tar.gz"
        
        # Create compressed archive
        subprocess.run([
            "tar", "-czf", str(package_file), 
            "-C", str(self.deployment_dir),
            self.package_name
        ], check=True)
        
        # Get package size
        size_mb = package_file.stat().st_size / (1024 * 1024)
        
        logger.info(f"✅ Installation package created: {package_file}")
        logger.info(f"📦 Package size: {size_mb:.2f} MB")
        
        return package_file

def main():
    """Create production deployment package."""
    packager = TerraFusionDeploymentPackager()
    
    # Create deployment package
    package_path = packager.create_deployment_package()
    
    # Create compressed installation package
    installation_package = packager.create_installation_package()
    
    print("\n" + "=" * 60)
    print("🎉 TerraFusion Production Deployment Package Complete!")
    print("=" * 60)
    print(f"📁 Package directory: {package_path}")
    print(f"📦 Installation package: {installation_package}")
    print("\n📋 Next Steps:")
    print("1. Transfer the installation package to your production server")
    print("2. Extract the package and configure .env with your county credentials")
    print("3. Run the deployment script for your platform")
    print("4. Validate the deployment with the included test suite")
    print("\n🔐 Required Credentials:")
    print("- County database connection details")
    print("- Duo Security MFA credentials") 
    print("- PACS API authentication keys")
    print("=" * 60)

if __name__ == "__main__":
    main()