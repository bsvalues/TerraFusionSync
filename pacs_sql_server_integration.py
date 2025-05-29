"""
PACS SQL Server Integration

Direct integration with jcharrispacs SQL Server for live county data synchronization.
Implements secure connection management and data extraction from PACS system.
"""

import os
import logging
import pyodbc
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PACSIntegration:
    """
    PACS SQL Server integration for TerraFusion Platform.
    
    Connects to jcharrispacs server for live county data extraction.
    """
    
    def __init__(self):
        """Initialize PACS integration with connection parameters."""
        self.server = "jcharrispacs"
        self.database = "pacs_training"
        self.username = None  # Will use Windows Authentication or SQL Auth
        self.password = None
        self.connection_string = None
        self.engine = None
        
        # Core PACS tables to sync
        self.pacs_tables = {
            "parcels": "SELECT ParcelID, ParcelNumber, LegalDescription, OwnerName, SitusAddress FROM Parcels",
            "assessments": "SELECT ParcelID, AssessmentYear, LandValue, ImprovementValue, TotalValue FROM Assessments",
            "exemptions": "SELECT ParcelID, ExemptionType, ExemptionAmount, ExemptionYear, ApprovalStatus FROM Exemptions",
            "owners": "SELECT OwnerID, OwnerName, MailingAddress, City, State, ZipCode FROM Owners",
            "properties": "SELECT PropertyID, ParcelID, PropertyType, YearBuilt, SquareFootage FROM Properties"
        }
    
    def setup_connection(self, use_windows_auth: bool = True, username: str = None, password: str = None):
        """
        Setup connection to PACS SQL Server.
        
        Args:
            use_windows_auth: Use Windows Authentication if True, SQL Auth if False
            username: SQL Server username (if not using Windows auth)
            password: SQL Server password (if not using Windows auth)
        """
        try:
            if use_windows_auth:
                # Windows Authentication (Integrated Security)
                connection_string = f"""
                    DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.server};
                    DATABASE={self.database};
                    Trusted_Connection=yes;
                    TrustServerCertificate=yes;
                """
                logger.info(f"Configuring Windows Authentication for {self.server}")
            else:
                # SQL Server Authentication
                if not username or not password:
                    logger.error("SQL Authentication requires username and password")
                    return False
                
                self.username = username
                self.password = password
                
                connection_string = f"""
                    DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.server};
                    DATABASE={self.database};
                    UID={username};
                    PWD={password};
                    TrustServerCertificate=yes;
                """
                logger.info(f"Configuring SQL Authentication for {self.server} with user {username}")
            
            self.connection_string = connection_string
            
            # Create SQLAlchemy engine for pandas integration
            if use_windows_auth:
                engine_string = f"mssql+pyodbc://@{self.server}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
            else:
                engine_string = f"mssql+pyodbc://{quote_plus(username)}:{quote_plus(password)}@{self.server}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
            
            self.engine = create_engine(engine_string)
            logger.info("✅ PACS connection configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup PACS connection: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to PACS SQL Server.
        
        Returns:
            bool: True if connection successful
        """
        logger.info("Testing PACS SQL Server connection...")
        
        try:
            # Test with pyodbc first
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT @@VERSION as SQLServerVersion")
            version = cursor.fetchone()
            
            if version:
                logger.info(f"✅ PACS connection successful")
                logger.info(f"SQL Server Version: {version[0][:50]}...")
                
                # Test database access
                cursor.execute(f"SELECT DB_NAME() as CurrentDatabase")
                db_result = cursor.fetchone()
                logger.info(f"Connected to database: {db_result[0]}")
                
                # List available tables
                cursor.execute("""
                    SELECT TABLE_SCHEMA, TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
                
                tables = cursor.fetchall()
                logger.info(f"Found {len(tables)} tables in PACS database")
                
                # Log first 10 tables
                for i, (schema, table) in enumerate(tables[:10]):
                    logger.info(f"  {schema}.{table}")
                
                if len(tables) > 10:
                    logger.info(f"  ... and {len(tables) - 10} more tables")
                
                conn.close()
                return True
            else:
                logger.error("❌ No response from PACS server")
                return False
                
        except pyodbc.Error as e:
            logger.error(f"❌ PACS connection failed: {e}")
            logger.error("Please verify:")
            logger.error("- SQL Server is accessible from this network")
            logger.error("- Database name and server are correct")
            logger.error("- Authentication credentials are valid")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error testing PACS connection: {e}")
            return False
    
    def extract_pacs_data(self, table_query: str, table_name: str) -> Optional[pd.DataFrame]:
        """
        Extract data from PACS using SQL query.
        
        Args:
            table_query: SQL query to execute
            table_name: Name of the table being queried
            
        Returns:
            DataFrame with results or None if failed
        """
        logger.info(f"Extracting data from PACS table: {table_name}")
        
        try:
            if not self.engine:
                logger.error("PACS connection not configured")
                return None
            
            # Execute query and return DataFrame
            df = pd.read_sql_query(table_query, self.engine)
            
            logger.info(f"✅ Extracted {len(df)} records from {table_name}")
            
            # Log column info
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to extract data from {table_name}: {e}")
            return None
    
    def sync_all_pacs_data(self) -> Dict[str, pd.DataFrame]:
        """
        Extract all configured PACS data tables.
        
        Returns:
            Dictionary mapping table names to DataFrames
        """
        logger.info("🚀 Starting full PACS data synchronization")
        
        results = {}
        
        for table_name, query in self.pacs_tables.items():
            df = self.extract_pacs_data(query, table_name)
            if df is not None:
                results[table_name] = df
            else:
                logger.warning(f"⚠️ Failed to sync {table_name}")
        
        logger.info(f"📊 PACS sync complete: {len(results)}/{len(self.pacs_tables)} tables successfully extracted")
        
        return results
    
    def get_exemption_data(self, year: int = None) -> Optional[pd.DataFrame]:
        """
        Get exemption data for AI analysis.
        
        Args:
            year: Specific year to filter (optional)
            
        Returns:
            DataFrame with exemption records
        """
        logger.info(f"Extracting exemption data for AI analysis...")
        
        base_query = """
            SELECT 
                e.ParcelID,
                e.ExemptionType,
                e.ExemptionAmount,
                e.ExemptionYear,
                e.ApprovalStatus,
                e.ApplicationDate,
                e.ApprovalDate,
                p.ParcelNumber,
                p.OwnerName,
                p.SitusAddress,
                a.TotalValue as AssessedValue
            FROM Exemptions e
            LEFT JOIN Parcels p ON e.ParcelID = p.ParcelID
            LEFT JOIN Assessments a ON e.ParcelID = a.ParcelID AND e.ExemptionYear = a.AssessmentYear
        """
        
        if year:
            query = base_query + f" WHERE e.ExemptionYear = {year}"
        else:
            query = base_query + " WHERE e.ExemptionYear >= 2020"  # Last 5 years
        
        query += " ORDER BY e.ExemptionYear DESC, e.ApplicationDate DESC"
        
        return self.extract_pacs_data(query, "exemptions_detailed")
    
    def validate_pacs_schema(self) -> bool:
        """
        Validate that required PACS tables and columns exist.
        
        Returns:
            bool: True if schema is compatible
        """
        logger.info("Validating PACS database schema...")
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Check for core tables
            required_tables = ["Parcels", "Assessments", "Exemptions"]
            missing_tables = []
            
            for table in required_tables:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                
                if cursor.fetchone()[0] == 0:
                    missing_tables.append(table)
            
            if missing_tables:
                logger.error(f"❌ Missing required PACS tables: {missing_tables}")
                conn.close()
                return False
            
            logger.info("✅ PACS schema validation successful")
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
            return False

def test_pacs_integration():
    """Test function for PACS integration."""
    pacs = PACSIntegration()
    
    # Try Windows Authentication first
    logger.info("Testing Windows Authentication...")
    if pacs.setup_connection(use_windows_auth=True):
        if pacs.test_connection():
            logger.info("✅ Windows Authentication successful")
            return pacs
    
    # If Windows auth fails, prompt for SQL credentials
    logger.info("Windows Authentication failed, SQL Authentication required")
    logger.info("Please provide SQL Server credentials:")
    
    username = input("Username (or set PACS_USERNAME environment variable): ") or os.environ.get("PACS_USERNAME")
    password = input("Password (or set PACS_PASSWORD environment variable): ") or os.environ.get("PACS_PASSWORD")
    
    if username and password:
        if pacs.setup_connection(use_windows_auth=False, username=username, password=password):
            if pacs.test_connection():
                logger.info("✅ SQL Authentication successful")
                return pacs
    
    logger.error("❌ Unable to establish PACS connection")
    return None

if __name__ == "__main__":
    # Test PACS integration
    pacs = test_pacs_integration()
    
    if pacs:
        # Validate schema
        if pacs.validate_pacs_schema():
            # Extract sample data
            exemptions = pacs.get_exemption_data(2024)
            if exemptions is not None:
                print(f"\n📊 Sample exemption data for 2024:")
                print(exemptions.head())
                print(f"\nTotal exemption records: {len(exemptions)}")
        else:
            logger.error("PACS schema validation failed")
    else:
        logger.error("PACS integration test failed")