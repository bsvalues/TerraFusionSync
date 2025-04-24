"""
Change Detector component for the SyncService.

This module is responsible for detecting changes in the source system
and identifying records that need to be synchronized.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from syncservice.models.pacs import (PACSOwner, PACSProperty, PACSStructure,
                                    PACSValueHistory)
from syncservice.utils.database import get_source_session
from syncservice.utils.event_bus import publish_event

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detects changes in the source system for data synchronization."""

    def __init__(self):
        """Initialize the ChangeDetector component."""
        self.source_session = None

    async def get_changed_records(
        self, 
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve records that have changed since the specified time.
        
        Args:
            since: Timestamp to check for changes since. If None, defaults to 24 hours ago.
            limit: Maximum number of records to return per entity type.
            
        Returns:
            Dictionary containing changed records by entity type.
        """
        if not since:
            since = datetime.utcnow() - timedelta(hours=24)
            
        logger.info(f"Detecting changes since {since}")
        
        try:
            self.source_session = await get_source_session()
            
            # Collect changed records for each entity type
            changed_properties = await self._get_changed_properties(since, limit)
            changed_owners = await self._get_changed_owners(since, limit)
            changed_values = await self._get_changed_values(since, limit)
            changed_structures = await self._get_changed_structures(since, limit)
            
            # Calculate affected property IDs for related entities
            property_ids = set()
            property_ids.update([p["PropertyID"] for p in changed_properties])
            property_ids.update([o["PropertyID"] for o in changed_owners])
            property_ids.update([v["PropertyID"] for v in changed_values])
            property_ids.update([s["PropertyID"] for s in changed_structures])
            
            # Get all related data for the affected properties
            related_data = await self._get_related_data(property_ids)
            
            # Publish change detection event
            await publish_event(
                "change_detected",
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "record_count": {
                        "properties": len(changed_properties),
                        "owners": len(changed_owners),
                        "values": len(changed_values),
                        "structures": len(changed_structures),
                        "related_properties": len(related_data["properties"]),
                    }
                }
            )
            
            return {
                "properties": changed_properties,
                "owners": changed_owners,
                "values": changed_values,
                "structures": changed_structures,
                "related": related_data
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while detecting changes: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in change detection: {str(e)}")
            raise
    
    async def _get_changed_properties(
        self, 
        since: datetime,
        limit: int
    ) -> List[Dict]:
        """Get property records modified since the given timestamp."""
        query = (
            sa.select(PACSProperty)
            .where(PACSProperty.LastModified >= since)
            .order_by(PACSProperty.LastModified.desc())
            .limit(limit)
        )
        
        result = await self.source_session.execute(query)
        properties = result.scalars().all()
        
        return [prop.__dict__ for prop in properties]
    
    async def _get_changed_owners(
        self, 
        since: datetime,
        limit: int
    ) -> List[Dict]:
        """Get owner records modified since the given timestamp."""
        query = (
            sa.select(PACSOwner)
            .where(PACSOwner.LastModified >= since)
            .order_by(PACSOwner.LastModified.desc())
            .limit(limit)
        )
        
        result = await self.source_session.execute(query)
        owners = result.scalars().all()
        
        return [owner.__dict__ for owner in owners]
    
    async def _get_changed_values(
        self, 
        since: datetime,
        limit: int
    ) -> List[Dict]:
        """Get value history records modified since the given timestamp."""
        query = (
            sa.select(PACSValueHistory)
            .where(PACSValueHistory.LastModified >= since)
            .order_by(PACSValueHistory.LastModified.desc())
            .limit(limit)
        )
        
        result = await self.source_session.execute(query)
        values = result.scalars().all()
        
        return [value.__dict__ for value in values]
    
    async def _get_changed_structures(
        self, 
        since: datetime,
        limit: int
    ) -> List[Dict]:
        """Get structure records modified since the given timestamp."""
        query = (
            sa.select(PACSStructure)
            .where(PACSStructure.LastModified >= since)
            .order_by(PACSStructure.LastModified.desc())
            .limit(limit)
        )
        
        result = await self.source_session.execute(query)
        structures = result.scalars().all()
        
        return [structure.__dict__ for structure in structures]
    
    async def _get_related_data(
        self, 
        property_ids: Set[str]
    ) -> Dict[str, List[Dict]]:
        """
        Get all related data for a set of property IDs.
        
        This ensures we have complete records for all affected properties.
        """
        if not property_ids:
            return {
                "properties": [],
                "owners": [],
                "values": [],
                "structures": []
            }
        
        # Get all properties
        property_query = (
            sa.select(PACSProperty)
            .where(PACSProperty.PropertyID.in_(property_ids))
        )
        property_result = await self.source_session.execute(property_query)
        properties = property_result.scalars().all()
        property_dicts = [prop.__dict__ for prop in properties]
        
        # Get all owners for these properties
        owner_query = (
            sa.select(PACSOwner)
            .where(PACSOwner.PropertyID.in_(property_ids))
        )
        owner_result = await self.source_session.execute(owner_query)
        owners = owner_result.scalars().all()
        owner_dicts = [owner.__dict__ for owner in owners]
        
        # Get all value histories for these properties
        value_query = (
            sa.select(PACSValueHistory)
            .where(PACSValueHistory.PropertyID.in_(property_ids))
        )
        value_result = await self.source_session.execute(value_query)
        values = value_result.scalars().all()
        value_dicts = [value.__dict__ for value in values]
        
        # Get all structures for these properties
        structure_query = (
            sa.select(PACSStructure)
            .where(PACSStructure.PropertyID.in_(property_ids))
        )
        structure_result = await self.source_session.execute(structure_query)
        structures = structure_result.scalars().all()
        structure_dicts = [structure.__dict__ for structure in structures]
        
        return {
            "properties": property_dicts,
            "owners": owner_dicts,
            "values": value_dicts,
            "structures": structure_dicts
        }
    
    async def perform_full_change_detection(self) -> Dict[str, int]:
        """
        Perform a full change detection on all records in the source system.
        
        Returns:
            Dictionary with counts of records of each type.
        """
        logger.info("Starting full change detection")
        
        try:
            self.source_session = await get_source_session()
            
            # Count all records
            property_count = await self._count_all_properties()
            owner_count = await self._count_all_owners()
            value_count = await self._count_all_values()
            structure_count = await self._count_all_structures()
            
            # Publish event
            await publish_event(
                "full_change_detected",
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "record_count": {
                        "properties": property_count,
                        "owners": owner_count,
                        "values": value_count,
                        "structures": structure_count,
                    }
                }
            )
            
            return {
                "properties": property_count,
                "owners": owner_count,
                "values": value_count,
                "structures": structure_count,
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during full change detection: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in full change detection: {str(e)}")
            raise
    
    async def _count_all_properties(self) -> int:
        """Count all property records in the source system."""
        query = sa.select(sa.func.count()).select_from(PACSProperty)
        result = await self.source_session.execute(query)
        return result.scalar()
    
    async def _count_all_owners(self) -> int:
        """Count all owner records in the source system."""
        query = sa.select(sa.func.count()).select_from(PACSOwner)
        result = await self.source_session.execute(query)
        return result.scalar()
    
    async def _count_all_values(self) -> int:
        """Count all value history records in the source system."""
        query = sa.select(sa.func.count()).select_from(PACSValueHistory)
        result = await self.source_session.execute(query)
        return result.scalar()
    
    async def _count_all_structures(self) -> int:
        """Count all structure records in the source system."""
        query = sa.select(sa.func.count()).select_from(PACSStructure)
        result = await self.source_session.execute(query)
        return result.scalar()
