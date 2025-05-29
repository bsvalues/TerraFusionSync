"""
TerraFusion Historical AI Enrichment Module

Phase II Implementation: Historical AI Enrichment for ExemptionSeer
- Ingest 2013-2024 exemption data
- Normalize PILT and subcategory codes
- Label with inferred exemption types
- Train ExemptionSeer for temporal prediction and pattern anomaly detection
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExemptionRecord:
    """Structured exemption record for AI training"""
    parcel_id: str
    assessment_year: int
    exemption_type: str
    exemption_code: str
    exemption_amount: float
    property_description: str
    owner_name: str
    pilt_category: str
    subcategory_code: str
    approval_date: datetime
    expiration_date: Optional[datetime]
    confidence_score: float = 0.0

class HistoricalDataProcessor:
    """
    Historical exemption data processor for AI enrichment.
    Handles data ingestion, normalization, and preparation for ML training.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize the historical data processor.
        
        Args:
            database_url: Database connection string
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        self.engine = create_engine(self.database_url) if self.database_url else None
        self.Session = sessionmaker(bind=self.engine) if self.engine else None
        
        # Historical data storage
        self.historical_data_path = Path("data/historical_exemptions")
        self.historical_data_path.mkdir(parents=True, exist_ok=True)
        
        # Exemption normalization mappings
        self.exemption_mappings = {
            "senior": ["senior_citizen", "senior_exemption", "elderly"],
            "veteran": ["veteran", "military", "disabled_veteran"],
            "disability": ["disabled", "disability", "handicapped"],
            "non_profit": ["nonprofit", "charity", "religious", "church"],
            "agricultural": ["farm", "agriculture", "timber", "forest"],
            "industrial": ["manufacturing", "industrial"],
            "low_income": ["low_income", "poverty", "hardship"]
        }
        
        # Subcategory code standardization
        self.subcategory_mappings = {
            # Senior exemptions
            "SEN": "senior_citizen",
            "ELD": "elderly",
            "SR": "senior_citizen",
            # Veteran exemptions
            "VET": "veteran",
            "MIL": "military",
            "DVA": "disabled_veteran",
            # Disability exemptions
            "DIS": "disability",
            "HAN": "handicapped",
            # Non-profit exemptions
            "NPR": "non_profit",
            "REL": "religious",
            "CHR": "church",
            # Agricultural exemptions
            "AGR": "agricultural",
            "FAR": "farm",
            "TIM": "timber"
        }

    def ingest_historical_data(self, data_source: str) -> List[ExemptionRecord]:
        """
        Ingest historical exemption data from various sources.
        
        Args:
            data_source: Path to historical data file or database table
            
        Returns:
            List of processed exemption records
        """
        logger.info(f"Ingesting historical data from: {data_source}")
        
        exemption_records = []
        
        try:
            if data_source.endswith('.csv'):
                df = pd.read_csv(data_source)
                exemption_records = self._process_csv_data(df)
            elif data_source.endswith('.xlsx'):
                df = pd.read_excel(data_source)
                exemption_records = self._process_excel_data(df)
            elif data_source.startswith('table:'):
                table_name = data_source.replace('table:', '')
                exemption_records = self._process_database_table(table_name)
            else:
                logger.error(f"Unsupported data source format: {data_source}")
                
        except Exception as e:
            logger.error(f"Error ingesting data from {data_source}: {str(e)}")
            
        logger.info(f"Ingested {len(exemption_records)} exemption records")
        return exemption_records

    def _process_csv_data(self, df: pd.DataFrame) -> List[ExemptionRecord]:
        """Process CSV data into exemption records"""
        records = []
        
        for _, row in df.iterrows():
            try:
                record = ExemptionRecord(
                    parcel_id=str(row.get('parcel_id', '')),
                    assessment_year=int(row.get('assessment_year', 0)),
                    exemption_type=self._normalize_exemption_type(str(row.get('exemption_type', ''))),
                    exemption_code=str(row.get('exemption_code', '')),
                    exemption_amount=float(row.get('exemption_amount', 0.0)),
                    property_description=str(row.get('property_description', '')),
                    owner_name=str(row.get('owner_name', '')),
                    pilt_category=self._normalize_pilt_category(str(row.get('pilt_category', ''))),
                    subcategory_code=self._normalize_subcategory(str(row.get('subcategory_code', ''))),
                    approval_date=pd.to_datetime(row.get('approval_date')),
                    expiration_date=pd.to_datetime(row.get('expiration_date')) if row.get('expiration_date') else None
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Error processing row: {str(e)}")
                continue
                
        return records

    def _process_database_table(self, table_name: str) -> List[ExemptionRecord]:
        """Process database table into exemption records"""
        if not self.Session:
            logger.error("Database connection not available")
            return []
            
        records = []
        session = self.Session()
        
        try:
            query = text(f"""
                SELECT 
                    parcel_id,
                    assessment_year,
                    exemption_type,
                    exemption_code,
                    exemption_amount,
                    property_description,
                    owner_name,
                    pilt_category,
                    subcategory_code,
                    approval_date,
                    expiration_date
                FROM {table_name}
                WHERE assessment_year BETWEEN 2013 AND 2024
                ORDER BY assessment_year, parcel_id
            """)
            
            result = session.execute(query)
            
            for row in result:
                try:
                    record = ExemptionRecord(
                        parcel_id=str(row.parcel_id),
                        assessment_year=int(row.assessment_year),
                        exemption_type=self._normalize_exemption_type(str(row.exemption_type)),
                        exemption_code=str(row.exemption_code),
                        exemption_amount=float(row.exemption_amount or 0.0),
                        property_description=str(row.property_description or ''),
                        owner_name=str(row.owner_name or ''),
                        pilt_category=self._normalize_pilt_category(str(row.pilt_category or '')),
                        subcategory_code=self._normalize_subcategory(str(row.subcategory_code or '')),
                        approval_date=row.approval_date,
                        expiration_date=row.expiration_date
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error processing database row: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
        finally:
            session.close()
            
        return records

    def _normalize_exemption_type(self, exemption_type: str) -> str:
        """Normalize exemption type to standard categories"""
        exemption_type = exemption_type.lower().strip()
        
        for standard_type, variations in self.exemption_mappings.items():
            if any(variation in exemption_type for variation in variations):
                return standard_type
                
        return exemption_type

    def _normalize_exemption_category(self, exemption_category: str) -> str:
        """Normalize exemption category codes"""
        return self._normalize_exemption_type(exemption_category)

    def _normalize_subcategory(self, subcategory_code: str) -> str:
        """Normalize subcategory codes to standard format"""
        subcategory_code = subcategory_code.upper().strip()
        return self.subcategory_mappings.get(subcategory_code, subcategory_code.lower())

    def create_temporal_features(self, records: List[ExemptionRecord]) -> pd.DataFrame:
        """
        Create temporal features for machine learning training.
        
        Args:
            records: List of exemption records
            
        Returns:
            DataFrame with temporal features
        """
        logger.info("Creating temporal features for ML training")
        
        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'parcel_id': record.parcel_id,
                'assessment_year': record.assessment_year,
                'exemption_type': record.exemption_type,
                'exemption_code': record.exemption_code,
                'exemption_amount': record.exemption_amount,
                'property_description': record.property_description,
                'owner_name': record.owner_name,
                'pilt_category': record.pilt_category,
                'subcategory_code': record.subcategory_code,
                'approval_date': record.approval_date,
                'expiration_date': record.expiration_date
            })
            
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning("No data available for feature creation")
            return df
            
        # Create temporal features
        df['year_diff'] = df['assessment_year'] - df['assessment_year'].min()
        df['approval_month'] = pd.to_datetime(df['approval_date']).dt.month
        df['approval_quarter'] = pd.to_datetime(df['approval_date']).dt.quarter
        
        # Historical trend features
        df['exemption_amount_log'] = np.log1p(df['exemption_amount'])
        
        # Parcel-level features
        parcel_stats = df.groupby('parcel_id').agg({
            'exemption_amount': ['count', 'mean', 'std'],
            'assessment_year': ['min', 'max']
        }).round(2)
        
        parcel_stats.columns = ['exemption_count', 'exemption_avg', 'exemption_std', 'first_year', 'last_year']
        parcel_stats['exemption_years'] = parcel_stats['last_year'] - parcel_stats['first_year'] + 1
        parcel_stats['exemption_frequency'] = parcel_stats['exemption_count'] / parcel_stats['exemption_years']
        
        # Merge back to main dataframe
        df = df.merge(parcel_stats, left_on='parcel_id', right_index=True, how='left')
        
        # Type-level features
        type_trends = df.groupby(['exemption_type', 'assessment_year'])['exemption_amount'].agg(['mean', 'count']).reset_index()
        type_trends['type_trend'] = type_trends.groupby('exemption_type')['mean'].pct_change()
        
        df = df.merge(type_trends[['exemption_type', 'assessment_year', 'type_trend']], 
                     on=['exemption_type', 'assessment_year'], how='left')
        
        return df

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies in historical exemption patterns.
        
        Args:
            df: DataFrame with exemption data and features
            
        Returns:
            DataFrame with anomaly scores
        """
        logger.info("Detecting anomalies in exemption patterns")
        
        if df.empty:
            return df
            
        # Calculate z-scores for exemption amounts
        df['amount_zscore'] = abs((df['exemption_amount'] - df['exemption_amount'].mean()) / df['exemption_amount'].std())
        
        # Frequency-based anomalies
        df['frequency_zscore'] = abs((df['exemption_frequency'] - df['exemption_frequency'].mean()) / df['exemption_frequency'].std())
        
        # Combined anomaly score
        df['anomaly_score'] = (df['amount_zscore'] + df['frequency_zscore']) / 2
        
        # Mark high-anomaly records
        anomaly_threshold = df['anomaly_score'].quantile(0.95)
        df['is_anomaly'] = df['anomaly_score'] > anomaly_threshold
        
        logger.info(f"Detected {df['is_anomaly'].sum()} anomalous records")
        
        return df

    def save_processed_data(self, df: pd.DataFrame, filename: str = None):
        """
        Save processed data for AI training.
        
        Args:
            df: Processed DataFrame
            filename: Output filename
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"historical_exemptions_processed_{timestamp}.csv"
            
        output_path = self.historical_data_path / filename
        df.to_csv(output_path, index=False)
        
        logger.info(f"Processed data saved to: {output_path}")
        
        # Save metadata
        metadata = {
            "processed_date": datetime.now().isoformat(),
            "record_count": len(df),
            "year_range": f"{df['assessment_year'].min()}-{df['assessment_year'].max()}",
            "exemption_types": df['exemption_type'].unique().tolist(),
            "anomaly_count": int(df['is_anomaly'].sum()) if 'is_anomaly' in df.columns else 0
        }
        
        metadata_path = self.historical_data_path / f"{filename.replace('.csv', '_metadata.json')}"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

class ExemptionSeerTrainer:
    """
    Enhanced ExemptionSeer AI trainer for temporal prediction and anomaly detection.
    """
    
    def __init__(self, model_path: str = "models/exemption_seer"):
        """Initialize the trainer"""
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for machine learning training.
        
        Args:
            df: Processed exemption data
            
        Returns:
            Feature matrix and target vector
        """
        logger.info("Preparing training data for ExemptionSeer")
        
        # Select numerical features
        feature_cols = [
            'assessment_year', 'exemption_amount_log', 'approval_month', 'approval_quarter',
            'exemption_count', 'exemption_avg', 'exemption_std', 'exemption_years',
            'exemption_frequency', 'type_trend'
        ]
        
        # Handle missing values
        X = df[feature_cols].fillna(0).values
        
        # Target: predict if exemption will be approved (binary classification)
        y = np.ones(len(df))  # All historical records were approved
        
        return X, y
        
    def train_temporal_model(self, X: np.ndarray, y: np.ndarray):
        """
        Train temporal prediction model.
        
        Args:
            X: Feature matrix
            y: Target vector
        """
        logger.info("Training temporal prediction model")
        
        # This would integrate with actual ML libraries
        # For now, we'll create a model structure
        model_config = {
            "model_type": "temporal_exemption_predictor",
            "features": X.shape[1],
            "training_date": datetime.now().isoformat(),
            "training_samples": len(X)
        }
        
        # Save model configuration
        config_path = self.model_path / "temporal_model_config.json"
        with open(config_path, 'w') as f:
            json.dump(model_config, f, indent=2)
            
        logger.info(f"Temporal model configuration saved to: {config_path}")

def main():
    """Main execution function for historical AI enrichment"""
    logger.info("Starting Historical AI Enrichment - Phase II Implementation")
    
    # Initialize processor
    processor = HistoricalDataProcessor()
    
    # Example usage - would be replaced with actual data sources
    exemption_data_sources = [
        "data/benton_exemptions_2013_2024.csv",
        "table:historical_exemptions"
    ]
    
    all_records = []
    
    # Process each data source
    for source in exemption_data_sources:
        try:
            records = processor.ingest_historical_data(source)
            all_records.extend(records)
        except Exception as e:
            logger.error(f"Failed to process {source}: {str(e)}")
            continue
    
    if not all_records:
        logger.error("No historical data could be processed")
        return
    
    # Create temporal features
    df = processor.create_temporal_features(all_records)
    
    # Detect anomalies
    df = processor.detect_anomalies(df)
    
    # Save processed data
    processor.save_processed_data(df)
    
    # Train enhanced ExemptionSeer
    trainer = ExemptionSeerTrainer()
    X, y = trainer.prepare_training_data(df)
    trainer.train_temporal_model(X, y)
    
    logger.info("Historical AI Enrichment Phase II - Complete")
    
    return {
        "status": "success",
        "records_processed": len(all_records),
        "anomalies_detected": int(df['is_anomaly'].sum()) if 'is_anomaly' in df.columns else 0,
        "years_covered": f"{df['assessment_year'].min()}-{df['assessment_year'].max()}" if not df.empty else "N/A"
    }

if __name__ == "__main__":
    result = main()
    print(f"Historical AI Enrichment Result: {result}")