"""
Tests for the Transformer component.

This module contains tests to verify the functionality of the Transformer component.
"""

import asyncio
import datetime
import json
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from syncservice.components.transformer import Transformer


@pytest.mark.asyncio
async def test_load_field_mapping():
    """Test loading field mapping configuration."""
    # Create temporary field mapping file
    test_mapping = {
        "property": {
            "PropertyID": "source_id",
            "TestField": "test_field"
        }
    }
    
    with patch('syncservice.components.transformer.open', MagicMock()) as mock_open:
        # Setup mock file content
        mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(test_mapping)
        
        # Setup transformer
        transformer = Transformer()
        
        # Verify the field mapping was loaded
        assert "property" in transformer.field_mapping
        assert transformer.field_mapping["property"]["TestField"] == "test_field"


@pytest.mark.asyncio
async def test_transform_property():
    """Test transforming a property from PACS to CAMA format."""
    # Setup test property data
    pacs_property = {
        "PropertyID": "123",
        "ParcelNumber": "AB-123",
        "Address": "123 Main St",
        "City": "Anytown",
        "State": "ST",
        "ZipCode": "12345",
        "LegalDescription": "Lot 1, Block A",
        "Acreage": 1.5,
        "YearBuilt": 2000,
        "LastModified": datetime.datetime.utcnow(),
        "IsActive": True
    }
    
    # Setup transformer with mock field mapping
    transformer = Transformer()
    transformer.field_mapping = {
        "property": {
            "PropertyID": "source_id",
            "ParcelNumber": "parcel_number",
            "Address": "address",
            "City": "city",
            "State": "state",
            "ZipCode": "zip_code",
            "LegalDescription": "legal_description",
            "Acreage": "acreage",
            "YearBuilt": "year_built",
            "LastModified": "source_last_modified",
            "IsActive": "is_active"
        }
    }
    
    # Mock OpenAI client
    transformer.openai_client = None
    
    # Mock the AI enrichment functions
    transformer._enrich_property_data = AsyncMock(return_value={
        "property_class": "Residential"
    })
    transformer._generate_geo_coordinates = AsyncMock(return_value={
        "latitude": 37.12345,
        "longitude": -122.54321
    })
    
    # Mock the publish event function
    with patch('syncservice.components.transformer.publish_event', AsyncMock(return_value=True)):
        # Transform the property
        cama_property = await transformer.transform_property(pacs_property)
        
        # Verify the result
        assert cama_property.source_id == "123"
        assert cama_property.parcel_number == "AB-123"
        assert cama_property.address == "123 Main St"
        assert cama_property.city == "Anytown"
        assert cama_property.state == "ST"
        assert cama_property.zip_code == "12345"
        assert cama_property.legal_description == "Lot 1, Block A"
        assert cama_property.acreage == 1.5
        assert cama_property.year_built == 2000
        assert cama_property.is_active is True
        
        # Verify enriched data
        assert cama_property.additional_data["property_class"] == "Residential"
        assert cama_property.geo_coordinates["latitude"] == 37.12345
        assert cama_property.geo_coordinates["longitude"] == -122.54321


@pytest.mark.asyncio
async def test_transform_owner():
    """Test transforming an owner from PACS to CAMA format."""
    # Setup test owner data
    pacs_owner = {
        "OwnerID": "O123",
        "PropertyID": "P123",
        "OwnerName": "John Doe",
        "OwnerType": "Individual",
        "OwnershipPercentage": 100.0,
        "StartDate": datetime.datetime(2020, 1, 1),
        "EndDate": None,
        "LastModified": datetime.datetime.utcnow()
    }
    
    # Property ID mapping
    property_id_map = {
        "P123": "new-uuid-for-property"
    }
    
    # Setup transformer with mock field mapping
    transformer = Transformer()
    transformer.field_mapping = {
        "owner": {
            "OwnerID": "source_id",
            "PropertyID": "property_id",
            "OwnerName": "owner_name",
            "OwnerType": "owner_type",
            "OwnershipPercentage": "ownership_percentage",
            "StartDate": "start_date",
            "EndDate": "end_date",
            "LastModified": "source_last_modified"
        }
    }
    
    # Mock the generate contact information function
    transformer._generate_contact_information = AsyncMock(return_value={
        "email": "john.doe@example.com",
        "phone": "555-123-4567"
    })
    
    # Mock the publish event function
    with patch('syncservice.components.transformer.publish_event', AsyncMock(return_value=True)):
        # Transform the owner
        cama_owner = await transformer.transform_owner(pacs_owner, property_id_map)
        
        # Verify the result
        assert cama_owner.source_id == "O123"
        assert cama_owner.property_id == "new-uuid-for-property"
        assert cama_owner.owner_name == "John Doe"
        assert cama_owner.owner_type == "Individual"
        assert cama_owner.ownership_percentage == 100.0
        assert cama_owner.start_date == datetime.datetime(2020, 1, 1)
        assert cama_owner.end_date is None
        
        # Verify contact information
        assert cama_owner.contact_information["email"] == "john.doe@example.com"
        assert cama_owner.contact_information["phone"] == "555-123-4567"


@pytest.mark.asyncio
async def test_batch_transform_records():
    """Test batch transformation of records."""
    # Setup test data
    records = {
        "properties": [
            {
                "PropertyID": "P123",
                "ParcelNumber": "AB-123",
                "Address": "123 Main St",
                "LastModified": datetime.datetime.utcnow(),
                "IsActive": True
            }
        ],
        "owners": [
            {
                "OwnerID": "O123",
                "PropertyID": "P123",
                "OwnerName": "John Doe",
                "LastModified": datetime.datetime.utcnow()
            }
        ],
        "values": [],
        "structures": []
    }
    
    # Setup transformer
    transformer = Transformer()
    
    # Mock the transform methods
    transformer.transform_property = AsyncMock(return_value=MagicMock(id="new-property-id", source_id="P123"))
    transformer.transform_owner = AsyncMock(return_value=MagicMock(id="new-owner-id", source_id="O123"))
    transformer.transform_value = AsyncMock(return_value=MagicMock())
    transformer.transform_structure = AsyncMock(return_value=MagicMock())
    
    # Mock the publish event function
    with patch('syncservice.components.transformer.publish_event', AsyncMock(return_value=True)):
        # Transform the records
        result = await transformer.batch_transform_records(records)
        
        # Verify the result
        assert "properties" in result
        assert len(result["properties"]) == 1
        
        assert "owners" in result
        assert len(result["owners"]) == 1
        
        assert "values" in result
        assert len(result["values"]) == 0
        
        assert "structures" in result
        assert len(result["structures"]) == 0
        
        # Verify property ID mapping
        assert "property_id_map" in result
        assert result["property_id_map"]["P123"] == "new-property-id"
