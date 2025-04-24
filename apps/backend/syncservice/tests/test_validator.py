"""
Tests for the Validator component.

This module contains tests to verify the functionality of the Validator component.
"""

import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from syncservice.components.validator import Validator
from syncservice.models.cama import (CAMAOwnerSchema, CAMAPropertySchema,
                                    CAMAStructureSchema, CAMAValueSchema)


@pytest.mark.asyncio
async def test_validate_property_valid():
    """Test validation of a valid property."""
    # Setup valid property data
    property_data = CAMAPropertySchema(
        id="test-id",
        source_id="P123",
        parcel_number="AB-123",
        address="123 Main St",
        city="Anytown",
        state="ST",
        zip_code="12345",
        legal_description="Lot 1, Block A",
        acreage=1.5,
        year_built=2000,
        source_last_modified=datetime.datetime.utcnow(),
        is_active=True,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    # Setup validator
    validator = Validator()
    
    # Mock the publish event function
    with patch('syncservice.components.validator.publish_event', AsyncMock(return_value=True)):
        # Validate the property
        is_valid, errors = await validator.validate_property(property_data)
        
        # Verify the result
        assert is_valid is True
        assert errors is None


@pytest.mark.asyncio
async def test_validate_property_invalid():
    """Test validation of an invalid property."""
    # Setup invalid property data
    property_data = CAMAPropertySchema(
        id="test-id",
        source_id="P123",
        parcel_number="",  # Empty parcel number should be invalid
        address="123",     # Address too short
        city="Anytown",
        state="STATE",     # State should be 2 letters
        zip_code="12345",
        legal_description="Lot 1, Block A",
        acreage=-1.0,      # Negative acreage should be invalid
        year_built=3000,   # Future year should be invalid
        source_last_modified=datetime.datetime.utcnow(),
        is_active=True,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    # Setup validator
    validator = Validator()
    
    # Mock the publish event function
    with patch('syncservice.components.validator.publish_event', AsyncMock(return_value=True)):
        # Validate the property
        is_valid, errors = await validator.validate_property(property_data)
        
        # Verify the result
        assert is_valid is False
        assert errors is not None
        assert len(errors) > 0
        
        # Check specific errors
        assert any("Parcel number is required" in error for error in errors)
        assert any("Address must be at least 5 characters" in error for error in errors)
        assert any("State must be a 2-letter code" in error for error in errors)
        assert any("Acreage must be greater than 0" in error for error in errors)
        assert any("Year built must be between" in error for error in errors)


@pytest.mark.asyncio
async def test_validate_owner():
    """Test validation of an owner."""
    # Setup owner data
    owner_data = CAMAOwnerSchema(
        id="test-id",
        source_id="O123",
        property_id="P123",
        owner_name="John Doe",
        owner_type="Individual",
        ownership_percentage=100.0,
        start_date=datetime.datetime(2020, 1, 1),
        end_date=datetime.datetime(2025, 1, 1),
        source_last_modified=datetime.datetime.utcnow(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    # Setup validator
    validator = Validator()
    
    # Mock the publish event function
    with patch('syncservice.components.validator.publish_event', AsyncMock(return_value=True)):
        # Validate with property exists
        is_valid, errors = await validator.validate_owner(owner_data, True)
        
        # Verify the result
        assert is_valid is True
        assert errors is None
        
        # Validate with property doesn't exist
        is_valid, errors = await validator.validate_owner(owner_data, False)
        
        # Verify the result
        assert is_valid is False
        assert errors is not None
        assert any("Referenced property" in error for error in errors)


@pytest.mark.asyncio
async def test_batch_validate_records():
    """Test batch validation of records."""
    # Setup test data
    property1 = CAMAPropertySchema(
        id="P1",
        source_id="PS1",
        parcel_number="AB-123",
        address="123 Main St",
        city="Anytown",
        state="ST",
        zip_code="12345",
        source_last_modified=datetime.datetime.utcnow(),
        is_active=True,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    property2 = CAMAPropertySchema(
        id="P2",
        source_id="PS2",
        parcel_number="",  # Invalid: empty parcel number
        address="123",     # Invalid: address too short
        city="Anytown",
        state="ST",
        zip_code="12345",
        source_last_modified=datetime.datetime.utcnow(),
        is_active=True,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    owner1 = CAMAOwnerSchema(
        id="O1",
        source_id="OS1",
        property_id="P1",  # Valid property reference
        owner_name="John Doe",
        source_last_modified=datetime.datetime.utcnow(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    owner2 = CAMAOwnerSchema(
        id="O2",
        source_id="OS2",
        property_id="P99",  # Invalid property reference
        owner_name="Jane Smith",
        source_last_modified=datetime.datetime.utcnow(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    # Transformed records to validate
    transformed_records = {
        "properties": [property1, property2],
        "owners": [owner1, owner2],
        "values": [],
        "structures": []
    }
    
    # Setup validator
    validator = Validator()
    
    # Mock the validate methods to use real implementation for properties but simplified for others
    original_validate_property = validator.validate_property
    validator.validate_property = original_validate_property
    validator.validate_owner = AsyncMock(side_effect=[
        (True, None),       # owner1 is valid
        (False, ["Referenced property does not exist"])  # owner2 is invalid
    ])
    validator.validate_value = AsyncMock(return_value=(True, None))
    validator.validate_structure = AsyncMock(return_value=(True, None))
    
    # Mock the publish event function
    with patch('syncservice.components.validator.publish_event', AsyncMock(return_value=True)):
        # Validate the records
        result = await validator.batch_validate_records(transformed_records)
        
        # Verify the result
        assert "valid" in result
        assert "invalid" in result
        assert "stats" in result
        
        # Check valid properties
        assert len(result["valid"]["properties"]) == 1
        assert result["valid"]["properties"][0].id == "P1"
        
        # Check invalid properties
        assert len(result["invalid"]["properties"]) == 1
        assert result["invalid"]["properties"][0][0].id == "P2"
        
        # Check valid owners
        assert len(result["valid"]["owners"]) == 1
        assert result["valid"]["owners"][0].id == "O1"
        
        # Check invalid owners
        assert len(result["invalid"]["owners"]) == 1
        assert result["invalid"]["owners"][0][0].id == "O2"
        
        # Check stats
        assert result["stats"]["total_records"] == 4
        assert result["stats"]["valid_records"] == 2
        assert result["stats"]["invalid_records"] == 2
