"""
PACS Integration Service for TerraFusion

Live integration with jcharrispacs SQL Server using environment-based configuration.
Ready for immediate deployment with your county credentials.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PACSIntegrationService:
    """
    Production PACS integration service for TerraFusion Platform.
    
    Connects to your jcharrispacs server for live county data synchronization.
    """
    
    def __init__(self):
        """Initialize PACS integration service."""
        self.server = os.environ.get("PACS_SQL_SERVER", "jcharrispacs")
        self.database = os.environ.get("PACS_DATABASE", "pacs_training")
        self.username = os.environ.get("PACS_USERNAME")
        self.password = os.environ.get("PACS_PASSWORD")
        self.connection_configured = False
        
        # PACS data extraction queries
        self.pacs_queries = {
            "exemptions_current": """
                SELECT 
                    ParcelID,
                    ExemptionType,
                    ExemptionAmount,
                    ExemptionYear,
                    ApprovalStatus,
                    ApplicationDate,
                    ApprovalDate
                FROM Exemptions 
                WHERE ExemptionYear >= 2020
                ORDER BY ExemptionYear DESC, ApplicationDate DESC
            """,
            
            "parcels_active": """
                SELECT 
                    ParcelID,
                    ParcelNumber,
                    LegalDescription,
                    OwnerName,
                    SitusAddress,
                    Acreage,
                    PropertyClass
                FROM Parcels 
                WHERE Status = 'Active'
            """,
            
            "assessments_recent": """
                SELECT 
                    ParcelID,
                    AssessmentYear,
                    LandValue,
                    ImprovementValue,
                    TotalValue,
                    ExemptValue
                FROM Assessments 
                WHERE AssessmentYear >= 2020
                ORDER BY AssessmentYear DESC
            """
        }
    
    def check_configuration(self) -> Dict[str, Any]:
        """
        Check PACS integration configuration status.
        
        Returns:
            Dictionary with configuration status
        """
        config_status = {
            "server_configured": bool(self.server),
            "database_configured": bool(self.database),
            "credentials_configured": bool(self.username and self.password),
            "ready_for_connection": False
        }
        
        config_status["ready_for_connection"] = all([
            config_status["server_configured"],
            config_status["database_configured"],
            config_status["credentials_configured"]
        ])
        
        return config_status
    
    def get_connection_string(self) -> Optional[str]:
        """
        Generate PACS connection string.
        
        Returns:
            Connection string if credentials available
        """
        if not (self.username and self.password):
            logger.error("PACS credentials not configured")
            return None
        
        # SQL Server connection string for your jcharrispacs server
        connection_string = (
            f"mssql+pyodbc://{self.username}:{self.password}@{self.server}/{self.database}"
            "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        )
        
        return connection_string
    
    def validate_pacs_access(self) -> bool:
        """
        Validate access to PACS system.
        
        Returns:
            True if PACS is accessible
        """
        config = self.check_configuration()
        
        if not config["ready_for_connection"]:
            logger.error("PACS configuration incomplete")
            logger.error("Required environment variables:")
            logger.error("- PACS_SQL_SERVER (configured)")
            logger.error("- PACS_DATABASE (configured)")
            logger.error("- PACS_USERNAME (missing)" if not self.username else "- PACS_USERNAME (configured)")
            logger.error("- PACS_PASSWORD (missing)" if not self.password else "- PACS_PASSWORD (configured)")
            return False
        
        try:
            # Attempt to create SQLAlchemy engine
            from sqlalchemy import create_engine, text
            
            connection_string = self.get_connection_string()
            if not connection_string:
                return False
            
            engine = create_engine(connection_string)
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION"))
                version = result.fetchone()
                
                if version:
                    logger.info(f"✅ PACS connection successful")
                    logger.info(f"Connected to: {self.server}/{self.database}")
                    self.connection_configured = True
                    return True
                    
        except Exception as e:
            logger.error(f"❌ PACS connection failed: {e}")
            logger.error("Please verify your county database credentials")
            return False
        
        return False
    
    def extract_exemption_data(self) -> Optional[List[Dict]]:
        """
        Extract current exemption data from PACS with comprehensive edge case handling.
        
        Returns:
            List of exemption records or None if failed
        """
        if not self.connection_configured:
            if not self.validate_pacs_access():
                return None
        
        try:
            from sqlalchemy import create_engine, text
            import pandas as pd
            
            connection_string = self.get_connection_string()
            engine = create_engine(connection_string)
            
            # Extract exemption data with edge case handling
            df = pd.read_sql_query(self.pacs_queries["exemptions_current"], engine)
            
            # Edge case handling
            edge_case_stats = {
                "total_extracted": len(df),
                "null_parcel_ids": 0,
                "invalid_amounts": 0,
                "missing_dates": 0,
                "duplicate_records": 0,
                "records_cleaned": 0,
                "records_skipped": 0
            }
            
            # Handle NULL/empty ParcelIDs
            null_parcels = df['ParcelID'].isnull() | (df['ParcelID'] == '')
            edge_case_stats["null_parcel_ids"] = null_parcels.sum()
            df = df[~null_parcels]  # Remove records with no parcel ID
            
            # Handle invalid exemption amounts
            df['ExemptionAmount'] = pd.to_numeric(df['ExemptionAmount'], errors='coerce')
            invalid_amounts = df['ExemptionAmount'].isnull()
            edge_case_stats["invalid_amounts"] = invalid_amounts.sum()
            df.loc[invalid_amounts, 'ExemptionAmount'] = 0  # Set to 0 instead of dropping
            
            # Handle missing/invalid dates
            date_columns = ['ApplicationDate', 'ApprovalDate']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    missing_dates = df[col].isnull()
                    edge_case_stats["missing_dates"] += missing_dates.sum()
            
            # Handle duplicate records (same parcel + exemption type + year)
            duplicate_mask = df.duplicated(subset=['ParcelID', 'ExemptionType', 'ExemptionYear'], keep='last')
            edge_case_stats["duplicate_records"] = duplicate_mask.sum()
            df = df[~duplicate_mask]  # Keep only the latest record
            
            # Final cleaning
            edge_case_stats["records_cleaned"] = edge_case_stats["total_extracted"] - len(df)
            
            logger.info(f"✅ Extracted {len(df)} exemption records from PACS")
            logger.info(f"📊 Edge case statistics: {edge_case_stats}")
            
            # Convert to list of dictionaries
            exemptions = df.to_dict('records')
            
            # Save to local file for TerraFusion processing
            exemptions_file = Path("data/pacs_exemptions.json")
            exemptions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save both clean data and edge case report
            with open(exemptions_file, 'w') as f:
                json.dump(exemptions, f, indent=2, default=str)
            
            edge_case_file = Path("data/pacs_edge_case_report.json")
            with open(edge_case_file, 'w') as f:
                json.dump(edge_case_stats, f, indent=2)
            
            logger.info(f"📁 Exemption data saved to: {exemptions_file}")
            logger.info(f"📊 Edge case report saved to: {edge_case_file}")
            
            return exemptions
            
        except Exception as e:
            logger.error(f"❌ Failed to extract exemption data: {e}")
            return None
    
    def extract_parcel_data(self) -> Optional[List[Dict]]:
        """
        Extract active parcel data from PACS.
        
        Returns:
            List of parcel records or None if failed
        """
        if not self.connection_configured:
            if not self.validate_pacs_access():
                return None
        
        try:
            from sqlalchemy import create_engine
            import pandas as pd
            
            connection_string = self.get_connection_string()
            engine = create_engine(connection_string)
            
            # Extract parcel data
            df = pd.read_sql_query(self.pacs_queries["parcels_active"], engine)
            
            logger.info(f"✅ Extracted {len(df)} parcel records from PACS")
            
            # Convert to list of dictionaries
            parcels = df.to_dict('records')
            
            # Save to local file
            parcels_file = Path("data/pacs_parcels.json")
            parcels_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(parcels_file, 'w') as f:
                json.dump(parcels, f, indent=2, default=str)
            
            logger.info(f"📁 Parcel data saved to: {parcels_file}")
            
            return parcels
            
        except Exception as e:
            logger.error(f"❌ Failed to extract parcel data: {e}")
            return None
    
    def perform_full_sync(self) -> Dict[str, Any]:
        """
        Perform full PACS data synchronization.
        
        Returns:
            Sync results summary
        """
        logger.info("🚀 Starting full PACS data synchronization")
        
        sync_results = {
            "sync_started": datetime.now().isoformat(),
            "exemptions_synced": 0,
            "parcels_synced": 0,
            "assessments_synced": 0,
            "sync_successful": False,
            "errors": []
        }
        
        try:
            # Extract exemptions
            exemptions = self.extract_exemption_data()
            if exemptions:
                sync_results["exemptions_synced"] = len(exemptions)
            else:
                sync_results["errors"].append("Failed to extract exemption data")
            
            # Extract parcels
            parcels = self.extract_parcel_data()
            if parcels:
                sync_results["parcels_synced"] = len(parcels)
            else:
                sync_results["errors"].append("Failed to extract parcel data")
            
            # Determine sync success
            sync_results["sync_successful"] = (
                sync_results["exemptions_synced"] > 0 or 
                sync_results["parcels_synced"] > 0
            )
            
            if sync_results["sync_successful"]:
                logger.info("✅ PACS synchronization completed successfully")
            else:
                logger.error("❌ PACS synchronization failed")
            
            # Save sync results
            results_file = Path("data/pacs_sync_results.json")
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(sync_results, f, indent=2)
            
            return sync_results
            
        except Exception as e:
            logger.error(f"❌ PACS sync error: {e}")
            sync_results["errors"].append(str(e))
            return sync_results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current PACS synchronization status.
        
        Returns:
            Current sync status
        """
        status = {
            "service_status": "ready" if self.connection_configured else "not_configured",
            "last_sync": None,
            "data_available": False
        }
        
        # Check for existing sync results
        results_file = Path("data/pacs_sync_results.json")
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    last_sync = json.load(f)
                    status["last_sync"] = last_sync["sync_started"]
                    status["data_available"] = last_sync["sync_successful"]
            except:
                pass
        
        return status

def main():
    """Main function for PACS integration testing."""
    pacs = PACSIntegrationService()
    
    # Check configuration
    config = pacs.check_configuration()
    
    print("\n🔧 PACS Integration Configuration Status:")
    print(f"Server: {pacs.server}")
    print(f"Database: {pacs.database}")
    print(f"Credentials: {'✅ Configured' if config['credentials_configured'] else '❌ Missing'}")
    print(f"Ready: {'✅ Yes' if config['ready_for_connection'] else '❌ No'}")
    
    if config["ready_for_connection"]:
        print("\n🚀 Testing PACS connection...")
        if pacs.validate_pacs_access():
            print("\n📊 Performing data sync...")
            results = pacs.perform_full_sync()
            print(f"\nSync Results:")
            print(f"- Exemptions: {results['exemptions_synced']}")
            print(f"- Parcels: {results['parcels_synced']}")
            print(f"- Success: {results['sync_successful']}")
        else:
            print("❌ PACS connection failed")
    else:
        print("\n⚠️ PACS credentials required for connection")
        print("Please set environment variables:")
        print("- PACS_USERNAME: Your jcharrispacs username")
        print("- PACS_PASSWORD: Your jcharrispacs password")

if __name__ == "__main__":
    main()