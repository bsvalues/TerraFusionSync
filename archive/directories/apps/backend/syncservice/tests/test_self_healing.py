"""
Tests for the Self-Healing Orchestrator component.

This module contains tests to verify the functionality of the Self-Healing Orchestrator.
"""

import asyncio
import datetime
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from syncservice.components.self_healing import SelfHealingOrchestrator
from syncservice.models.base import ConflictRecord


@pytest.mark.asyncio
async def test_detect_conflicts():
    """Test detection of conflicts between source and target data."""
    # Setup orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Mock the execute_target_query function
    with patch('syncservice.components.self_healing.execute_target_query', AsyncMock()) as mock_query:
        # Setup mock response for first property (has conflict)
        mock_query.side_effect = [
            # First property exists in target with different address
            [{"id": "existing-id", "address": "456 Different St", "city": "Othertown"}],
            # No owners in target
            [],
            # No values in target
            [],
            # No structures in target
            []
        ]
        
        # Setup test transformed records
        transformed_records = {
            "properties": [
                MagicMock(
                    id="new-id",
                    source_id="P123",
                    address="123 Main St",
                    city="Anytown"
                )
            ],
            "owners": [],
            "values": [],
            "structures": []
        }
        
        # Detect conflicts
        conflicts = await orchestrator.detect_conflicts(transformed_records)
        
        # Verify conflicts
        assert len(conflicts) == 2  # One for address, one for city
        
        # Check address conflict
        address_conflict = next(c for c in conflicts if c.field_name == "address")
        assert address_conflict.record_id == "existing-id"
        assert address_conflict.source_value == "123 Main St"
        assert address_conflict.target_value == "456 Different St"
        
        # Check city conflict
        city_conflict = next(c for c in conflicts if c.field_name == "city")
        assert city_conflict.record_id == "existing-id"
        assert city_conflict.source_value == "Anytown"
        assert city_conflict.target_value == "Othertown"


@pytest.mark.asyncio
async def test_resolve_conflicts():
    """Test resolution of conflicts using resolution strategies."""
    # Setup orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Mock the _determine_resolution_strategy method
    orchestrator._determine_resolution_strategy = AsyncMock(side_effect=[
        "source_wins",
        "target_wins"
    ])
    
    # Setup test conflicts
    conflicts = [
        ConflictRecord(
            record_id="record1",
            field_name="address",
            source_value="123 Main St",
            target_value="456 Different St"
        ),
        ConflictRecord(
            record_id="record1",
            field_name="market_value",
            source_value=100000,
            target_value=150000
        )
    ]
    
    # Mock the publish event function
    with patch('syncservice.components.self_healing.publish_event', AsyncMock(return_value=True)):
        # Resolve conflicts
        resolved_conflicts = await orchestrator.resolve_conflicts(conflicts)
        
        # Verify resolutions
        assert len(resolved_conflicts) == 2
        
        # Check first conflict resolution
        assert resolved_conflicts[0].resolution_strategy == "source_wins"
        
        # Check second conflict resolution
        assert resolved_conflicts[1].resolution_strategy == "target_wins"
        
        # Verify conflict records were added to the orchestrator
        assert len(orchestrator.conflicts) == 2


@pytest.mark.asyncio
async def test_determine_resolution_strategy():
    """Test determination of resolution strategy for different fields."""
    # Setup orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Test address field (should be source_wins)
    address_conflict = ConflictRecord(
        record_id="record1",
        field_name="address",
        source_value="123 Main St",
        target_value="456 Different St"
    )
    strategy = await orchestrator._determine_resolution_strategy(address_conflict)
    assert strategy == "source_wins"
    
    # Test market_value field (should be target_wins)
    value_conflict = ConflictRecord(
        record_id="record1",
        field_name="market_value",
        source_value=100000,
        target_value=150000
    )
    strategy = await orchestrator._determine_resolution_strategy(value_conflict)
    assert strategy == "target_wins"
    
    # Test year_built field (should be merge)
    year_conflict = ConflictRecord(
        record_id="record1",
        field_name="year_built",
        source_value=2000,
        target_value=2010
    )
    strategy = await orchestrator._determine_resolution_strategy(year_conflict)
    assert strategy == "merge"


@pytest.mark.asyncio
async def test_apply_conflict_resolutions():
    """Test applying conflict resolutions to transformed records."""
    # Setup orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Setup test property with conflicts
    property1 = MagicMock(
        id="property1",
        address="123 Main St",
        year_built=2000
    )
    
    # Setup transformed records
    records = {
        "properties": [property1],
        "owners": [],
        "values": [],
        "structures": []
    }
    
    # Setup resolved conflicts
    resolved_conflicts = [
        ConflictRecord(
            record_id="property1",
            field_name="address",
            source_value="123 Main St",
            target_value="456 Different St",
            resolution_strategy="target_wins"
        ),
        ConflictRecord(
            record_id="property1",
            field_name="year_built",
            source_value=2000,
            target_value=2010,
            resolution_strategy="merge"
        )
    ]
    
    # Apply conflict resolutions
    await orchestrator.apply_conflict_resolutions(records, resolved_conflicts)
    
    # Verify changes to property
    assert property1.address == "456 Different St"  # target_wins
    assert property1.year_built == 2005  # merge (average of 2000 and 2010)


@pytest.mark.asyncio
async def test_heal_invalid_records():
    """Test healing of invalid records."""
    # Setup orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Mock the _apply_healing_strategies method
    orchestrator._apply_healing_strategies = AsyncMock(side_effect=[
        True,   # First property can be healed
        False   # Second property cannot be healed
    ])
    
    # Mock the _get_healing_actions method
    orchestrator._get_healing_actions = AsyncMock(return_value=[
        "Cleaned parcel number"
    ])
    
    # Setup invalid records
    property1 = MagicMock(id="property1", source_id="source1")
    property2 = MagicMock(id="property2", source_id="source2")
    
    invalid_records = {
        "properties": [
            (property1, ["Parcel number must contain only letters, numbers, and dashes"]),
            (property2, ["Year built must be between 1700 and 2023"])
        ],
        "owners": [],
        "values": [],
        "structures": []
    }
    
    # Mock the publish event function
    with patch('syncservice.components.self_healing.publish_event', AsyncMock(return_value=True)):
        # Heal invalid records
        result = await orchestrator.heal_invalid_records(invalid_records)
        
        # Verify results
        assert result["healed_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["healed_properties"]) == 1
        assert result["healed_properties"][0] == property1
        
        # Verify audit records were created
        assert len(orchestrator.audit_records) == 2  # One success, one failure
