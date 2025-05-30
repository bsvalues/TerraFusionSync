"""
Test script for the TerraFusion SyncService validation functionality.

This script tests the validation framework by:
1. Creating validation schemas for PACS and CAMA data
2. Validating sample data against those schemas
3. Printing the validation results

Usage:
    python test_validation.py
"""

import json
import logging
from apps.backend.validation import (
    validate, ValidationResult, PACSImageSchema, CAMAPropertySchema
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pacs_validation():
    """Test validation of PACS image data."""
    logger.info("Testing PACS image validation")
    
    # Sample valid PACS data
    valid_pacs_data = {
        "image_id": "IMG123456",
        "study_id": "STD789012",
        "patient_id": "PAT345678",
        "image_type": "DICOM",
        "modality": "CT",
        "acquisition_date": "2024-04-25",
        "accession_number": "ACC123456789"
    }
    
    # Sample invalid PACS data (missing required fields, invalid enum value)
    invalid_pacs_data = {
        "image_id": "IMG123456",
        # missing study_id
        "patient_id": "PAT345678",
        "image_type": "DICOM",
        "modality": "INVALID_MODALITY",  # Invalid enum value
        "acquisition_date": "2024-04-25",
        "accession_number": "acc123"  # Invalid format (pattern)
    }
    
    # Validate the valid data
    valid_result = validate(valid_pacs_data, "pacs_image")
    print("\n=== Valid PACS Image Validation Results ===")
    print(valid_result.format_as_text())
    
    # Validate the invalid data
    invalid_result = validate(invalid_pacs_data, "pacs_image")
    print("\n=== Invalid PACS Image Validation Results ===")
    print(invalid_result.format_as_text())
    
    return valid_result, invalid_result

def test_cama_validation():
    """Test validation of CAMA property data."""
    logger.info("Testing CAMA property validation")
    
    # Sample valid CAMA data
    valid_cama_data = {
        "property_id": "PROP123456",
        "parcel_id": "PARC789012",
        "property_type": "Single Family Residence",
        "property_class": "RESIDENTIAL",
        "assessed_value": 350000.00,
        "assessment_date": "2024-01-15",
        "tax_district": "AB12"
    }
    
    # Sample invalid CAMA data (negative value, invalid date)
    invalid_cama_data = {
        "property_id": "PROP123456",
        "parcel_id": "PARC789012",
        "property_type": "Single Family Residence",
        "property_class": "RESIDENTIAL",
        "assessed_value": -5000.00,  # Negative value
        "assessment_date": "01/15/2024",  # Wrong date format
        "tax_district": "AB123"  # Invalid format
    }
    
    # Validate the valid data
    valid_result = validate(valid_cama_data, "cama_property")
    print("\n=== Valid CAMA Property Validation Results ===")
    print(valid_result.format_as_text())
    
    # Validate the invalid data
    invalid_result = validate(invalid_cama_data, "cama_property")
    print("\n=== Invalid CAMA Property Validation Results ===")
    print(invalid_result.format_as_text())
    
    return valid_result, invalid_result

if __name__ == "__main__":
    print("TerraFusion SyncService Validation Framework Test")
    print("================================================\n")
    
    # Test PACS validation
    pacs_valid, pacs_invalid = test_pacs_validation()
    
    # Test CAMA validation
    cama_valid, cama_invalid = test_cama_validation()
    
    # Summary
    print("\n=== Validation Test Summary ===")
    print(f"PACS Valid: {pacs_valid.valid}")
    print(f"PACS Invalid: {pacs_invalid.valid}")
    print(f"CAMA Valid: {cama_valid.valid}")
    print(f"CAMA Invalid: {cama_invalid.valid}")