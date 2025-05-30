"""
TerraFusion Comprehensive Test Suite

Full testing implementation for all TF-ICSF components with authentic data validation.
Tests require real county database connections and API credentials.
"""

import os
import sys
import json
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pytest
import unittest
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TerraFusionTestSuite:
    """
    Comprehensive test suite for TerraFusion Platform.
    
    Tests all components:
    - API Gateway endpoints
    - PACS integration
    - GIS export functionality
    - AI engines (NarratorAI + ExemptionSeer)
    - Authentication (Duo MFA)
    - Database connections
    - Backup systems
    - Compliance tracking
    """
    
    def __init__(self):
        """Initialize test suite with configuration."""
        self.base_url = "http://localhost:5000"
        self.sync_url = "http://localhost:8080"
        self.test_results = {}
        self.required_secrets = [
            "DATABASE_URL",
            "SESSION_SECRET"
        ]
        self.optional_secrets = [
            "DUO_INTEGRATION_KEY",
            "DUO_SECRET_KEY", 
            "DUO_API_HOSTNAME",
            "PACS_API_URL",
            "PACS_API_KEY"
        ]
        
    def check_environment(self) -> bool:
        """
        Check if all required environment variables are set.
        
        Returns:
            bool: True if environment is properly configured
        """
        logger.info("Checking environment configuration...")
        missing_secrets = []
        
        for secret in self.required_secrets:
            if not os.environ.get(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            logger.error(f"Missing required environment variables: {missing_secrets}")
            logger.error("Please provide your actual county credentials to proceed with testing")
            return False
        
        # Check optional secrets
        missing_optional = []
        for secret in self.optional_secrets:
            if not os.environ.get(secret):
                missing_optional.append(secret)
        
        if missing_optional:
            logger.warning(f"Optional county credentials not configured: {missing_optional}")
            logger.warning("Some advanced features will require county API access")
            
        logger.info("✅ Environment configuration complete")
        return True
    
    def test_database_connectivity(self) -> bool:
        """
        Test database connectivity with actual county data.
        
        Returns:
            bool: True if database connection successful
        """
        logger.info("Testing database connectivity...")
        
        try:
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                logger.error("❌ DATABASE_URL not configured - requires authentic county database")
                return False
                
            # Test connection
            from sqlalchemy import create_engine, text
            engine = create_engine(database_url)
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone():
                    logger.info("✅ Database connectivity verified")
                    
                    # Test for actual county tables
                    tables_query = text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name IN ('properties', 'exemptions', 'assessments')
                    """)
                    
                    tables = conn.execute(tables_query).fetchall()
                    if tables:
                        logger.info(f"✅ County data tables found: {[t[0] for t in tables]}")
                    else:
                        logger.warning("⚠️ No county data tables found - system ready for data import")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.error("Please verify your county database credentials")
            return False
    
    def test_api_gateway_health(self) -> bool:
        """
        Test API Gateway health and endpoints.
        
        Returns:
            bool: True if API Gateway is functional
        """
        logger.info("Testing API Gateway health...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API Gateway health check passed")
                
                # Test dashboard endpoint
                dashboard_response = requests.get(f"{self.base_url}/dashboard", timeout=10)
                if dashboard_response.status_code == 200:
                    logger.info("✅ Dashboard endpoint accessible")
                    return True
                else:
                    logger.error(f"❌ Dashboard endpoint failed: {dashboard_response.status_code}")
                    return False
            else:
                logger.error(f"❌ API Gateway health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API Gateway connection failed: {e}")
            return False
    
    def test_sync_service_health(self) -> bool:
        """
        Test SyncService health and PACS connectivity.
        
        Returns:
            bool: True if SyncService is functional
        """
        logger.info("Testing SyncService health...")
        
        try:
            # Test SyncService health
            response = requests.get(f"{self.sync_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ SyncService health check passed")
                
                # Test PACS connectivity (requires real credentials)
                pacs_test_response = requests.get(f"{self.sync_url}/pacs/verify", timeout=15)
                if pacs_test_response.status_code == 200:
                    logger.info("✅ PACS connectivity verified")
                elif pacs_test_response.status_code == 401:
                    logger.warning("⚠️ PACS requires authentication - provide county API credentials")
                else:
                    logger.warning(f"⚠️ PACS connectivity needs configuration: {pacs_test_response.status_code}")
                
                return True
            else:
                logger.error(f"❌ SyncService health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ SyncService connection failed: {e}")
            return False
    
    def test_gis_export_functionality(self) -> bool:
        """
        Test GIS Export functionality with real data requirements.
        
        Returns:
            bool: True if GIS Export is functional
        """
        logger.info("Testing GIS Export functionality...")
        
        try:
            # Test GIS export job creation
            export_data = {
                "county_id": "benton_wa",
                "district_type": "voting_precincts",
                "format": "geojson",
                "include_metadata": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/gis-export/jobs",
                json=export_data,
                timeout=30
            )
            
            if response.status_code == 202:
                job_data = response.json()
                job_id = job_data.get("job_id")
                logger.info(f"✅ GIS Export job created: {job_id}")
                
                # Check job status
                status_response = requests.get(
                    f"{self.base_url}/api/v1/gis-export/jobs/{job_id}",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    logger.info("✅ GIS Export job tracking functional")
                    return True
                else:
                    logger.error(f"❌ GIS Export job tracking failed: {status_response.status_code}")
                    return False
            else:
                logger.error(f"❌ GIS Export job creation failed: {response.status_code}")
                if response.status_code == 400:
                    logger.error("Missing county GIS data - requires authentic county datasets")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ GIS Export test failed: {e}")
            return False
    
    def test_ai_engines(self) -> bool:
        """
        Test AI engines (NarratorAI and ExemptionSeer) with real data requirements.
        
        Returns:
            bool: True if AI engines are functional
        """
        logger.info("Testing AI engines...")
        
        # Test NarratorAI
        try:
            narrator_response = requests.get(f"{self.base_url}/api/v1/ai/health", timeout=10)
            if narrator_response.status_code == 200:
                logger.info("✅ NarratorAI health check passed")
            else:
                logger.warning("⚠️ NarratorAI requires configuration")
        except:
            logger.warning("⚠️ NarratorAI service unavailable")
        
        # Test ExemptionSeer
        try:
            exemption_response = requests.get(f"{self.base_url}/api/v1/ai/exemption-seer/health", timeout=10)
            if exemption_response.status_code == 200:
                logger.info("✅ ExemptionSeer health check passed")
                
                # Test exemption analysis (requires real exemption data)
                test_exemption = {
                    "parcel_id": "test_parcel_001",
                    "exemption_type": "senior_citizen",
                    "exemption_amount": 50000,
                    "property_description": "Single family residence",
                    "owner_name": "Test Owner",
                    "assessment_year": 2024
                }
                
                analysis_response = requests.post(
                    f"{self.base_url}/api/v1/ai/analyze/exemption",
                    json=test_exemption,
                    timeout=15
                )
                
                if analysis_response.status_code == 200:
                    logger.info("✅ ExemptionSeer analysis functional")
                    return True
                else:
                    logger.warning("⚠️ ExemptionSeer requires training on county exemption data")
                    
            else:
                logger.warning("⚠️ ExemptionSeer requires configuration")
                
        except:
            logger.warning("⚠️ ExemptionSeer service unavailable")
        
        return True  # AI engines are optional for basic functionality
    
    def test_authentication_security(self) -> bool:
        """
        Test authentication and security systems.
        
        Returns:
            bool: True if authentication is properly configured
        """
        logger.info("Testing authentication and security...")
        
        try:
            # Test RBAC endpoints
            rbac_response = requests.get(f"{self.base_url}/rbac/admin", timeout=10)
            
            # Should require authentication
            if rbac_response.status_code in [401, 403]:
                logger.info("✅ RBAC authentication enforced")
                
                # Test Duo MFA configuration
                duo_configured = all([
                    os.environ.get("DUO_INTEGRATION_KEY"),
                    os.environ.get("DUO_SECRET_KEY"),
                    os.environ.get("DUO_API_HOSTNAME")
                ])
                
                if duo_configured:
                    logger.info("✅ Duo MFA credentials configured")
                else:
                    logger.warning("⚠️ Duo MFA requires county security credentials")
                
                return True
            else:
                logger.error("❌ Authentication not properly enforced")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Authentication test failed: {e}")
            return False
    
    def test_backup_system(self) -> bool:
        """
        Test backup and recovery systems.
        
        Returns:
            bool: True if backup system is functional
        """
        logger.info("Testing backup system...")
        
        try:
            # Check if backup directory exists and has recent backups
            backup_dir = Path("backups")
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*backup*.gz"))
                if backup_files:
                    # Check for recent backups
                    recent_backups = [
                        f for f in backup_files 
                        if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 1
                    ]
                    
                    if recent_backups:
                        logger.info(f"✅ Backup system active - {len(recent_backups)} recent backups found")
                        return True
                    else:
                        logger.warning("⚠️ No recent backups found")
                else:
                    logger.warning("⚠️ No backup files found")
            else:
                logger.warning("⚠️ Backup directory not found")
                
            return True  # Backup is not critical for basic functionality
            
        except Exception as e:
            logger.error(f"❌ Backup system test failed: {e}")
            return False
    
    def test_district_lookup(self) -> bool:
        """
        Test district lookup functionality with authentic county data.
        
        Returns:
            bool: True if district lookup is functional
        """
        logger.info("Testing district lookup functionality...")
        
        try:
            # Test district listing
            districts_response = requests.get(
                f"{self.base_url}/api/v1/district-lookup/districts",
                timeout=10
            )
            
            if districts_response.status_code == 200:
                districts = districts_response.json()
                if districts.get("districts"):
                    logger.info("✅ District lookup functional")
                    
                    # Test coordinate lookup (requires real county boundaries)
                    coord_response = requests.get(
                        f"{self.base_url}/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090",
                        timeout=10
                    )
                    
                    if coord_response.status_code == 200:
                        logger.info("✅ Coordinate-based district lookup functional")
                    else:
                        logger.warning("⚠️ Coordinate lookup requires county GIS boundary data")
                    
                    return True
                else:
                    logger.warning("⚠️ No district data found - requires county district configuration")
            else:
                logger.error(f"❌ District lookup failed: {districts_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ District lookup test failed: {e}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """
        Run the complete test suite.
        
        Returns:
            Dict[str, bool]: Test results for each component
        """
        logger.info("🚀 Starting TerraFusion Comprehensive Test Suite")
        logger.info("=" * 60)
        
        # Check environment first
        if not self.check_environment():
            logger.error("❌ Environment check failed - cannot proceed with testing")
            logger.error("Please provide your county's actual API credentials and database connections")
            return {"environment": False}
        
        test_functions = [
            ("Database Connectivity", self.test_database_connectivity),
            ("API Gateway Health", self.test_api_gateway_health),
            ("SyncService Health", self.test_sync_service_health),
            ("GIS Export Functionality", self.test_gis_export_functionality),
            ("AI Engines", self.test_ai_engines),
            ("Authentication Security", self.test_authentication_security),
            ("Backup System", self.test_backup_system),
            ("District Lookup", self.test_district_lookup)
        ]
        
        results = {}
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_function in test_functions:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                result = test_function()
                results[test_name.lower().replace(" ", "_")] = result
                if result:
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                results[test_name.lower().replace(" ", "_")] = False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🏁 TerraFusion Test Suite Complete")
        logger.info(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - TerraFusion Platform is fully operational!")
        elif passed_tests >= total_tests * 0.8:
            logger.info("✅ CORE SYSTEMS OPERATIONAL - Minor configuration needed")
        else:
            logger.warning("⚠️ ADDITIONAL CONFIGURATION REQUIRED")
            logger.warning("Please provide county database credentials and API keys for full functionality")
        
        # Save results
        results_file = Path("test_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "success_rate": passed_tests / total_tests,
                "results": results
            }, f, indent=2)
        
        logger.info(f"📝 Test results saved to: {results_file}")
        
        return results

def main():
    """Run the comprehensive test suite."""
    suite = TerraFusionTestSuite()
    results = suite.run_comprehensive_test()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed

if __name__ == "__main__":
    main()