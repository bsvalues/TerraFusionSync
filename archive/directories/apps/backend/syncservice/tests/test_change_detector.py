"""
Tests for the Change Detector component.

This module contains tests to verify the functionality of the Change Detector component.
"""

import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from syncservice.components.change_detector import ChangeDetector


@pytest.mark.asyncio
async def test_get_changed_records():
    """Test getting changed records since a specific time."""
    # Mock the source session and database functions
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Sample property data
    property1 = MagicMock()
    property1.__dict__ = {
        "PropertyID": "123",
        "ParcelNumber": "AB-123",
        "Address": "123 Main St",
        "LastModified": datetime.datetime.utcnow()
    }
    
    mock_result.scalars.return_value.all.return_value = [property1]
    
    mock_session.execute.return_value = mock_result
    
    # Setup change detector with mocked session
    detector = ChangeDetector()
    detector.source_session = mock_session
    
    # Mock the publish event function
    with patch('syncservice.components.change_detector.publish_event', AsyncMock(return_value=True)):
        # Call the function
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        result = await detector.get_changed_records(since=since, limit=10)
        
        # Verify the result
        assert "properties" in result
        assert len(result["properties"]) == 1
        assert result["properties"][0]["PropertyID"] == "123"
        
        # Verify the query was called with the right parameters
        mock_session.execute.assert_called()


@pytest.mark.asyncio
async def test_perform_full_change_detection():
    """Test performing a full change detection."""
    # Mock the source session and database functions
    mock_session = AsyncMock()
    
    # Setup change detector with mocked session
    detector = ChangeDetector()
    detector.source_session = mock_session
    
    # Mock the count query results
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 100
    mock_session.execute.return_value = mock_count_result
    
    # Mock the publish event function
    with patch('syncservice.components.change_detector.publish_event', AsyncMock(return_value=True)):
        # Call the function
        result = await detector.perform_full_change_detection()
        
        # Verify the result
        assert "properties" in result
        assert result["properties"] == 100
        
        # Verify the count queries were called
        assert mock_session.execute.call_count == 4  # One for each entity type


@pytest.mark.asyncio
async def test_get_related_data():
    """Test getting related data for a set of property IDs."""
    # Mock the source session and database functions
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Sample property data
    property1 = MagicMock()
    property1.__dict__ = {
        "PropertyID": "123",
        "ParcelNumber": "AB-123",
        "Address": "123 Main St",
        "LastModified": datetime.datetime.utcnow()
    }
    
    # Sample owner data
    owner1 = MagicMock()
    owner1.__dict__ = {
        "OwnerID": "O123",
        "PropertyID": "123",
        "OwnerName": "John Doe",
        "LastModified": datetime.datetime.utcnow()
    }
    
    mock_result.scalars.return_value.all.side_effect = [
        [property1],  # First call for properties
        [owner1],     # Second call for owners
        [],           # Third call for values (empty)
        []            # Fourth call for structures (empty)
    ]
    
    mock_session.execute.return_value = mock_result
    
    # Setup change detector with mocked session
    detector = ChangeDetector()
    detector.source_session = mock_session
    
    # Call the function
    property_ids = {"123"}
    result = await detector._get_related_data(property_ids)
    
    # Verify the result
    assert "properties" in result
    assert len(result["properties"]) == 1
    assert result["properties"][0]["PropertyID"] == "123"
    
    assert "owners" in result
    assert len(result["owners"]) == 1
    assert result["owners"][0]["OwnerID"] == "O123"
    
    # Verify empty results
    assert "values" in result
    assert len(result["values"]) == 0
    
    assert "structures" in result
    assert len(result["structures"]) == 0


@pytest.mark.asyncio
async def test_empty_property_ids():
    """Test handling empty property ID set when getting related data."""
    # Setup change detector
    detector = ChangeDetector()
    
    # Call the function with empty set
    result = await detector._get_related_data(set())
    
    # Verify the result is empty but has all keys
    assert "properties" in result
    assert len(result["properties"]) == 0
    
    assert "owners" in result
    assert len(result["owners"]) == 0
    
    assert "values" in result
    assert len(result["values"]) == 0
    
    assert "structures" in result
    assert len(result["structures"]) == 0
