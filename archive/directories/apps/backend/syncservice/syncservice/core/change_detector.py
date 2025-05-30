"""
Change Detector module for the SyncService.

This module is responsible for detecting changes in source systems that need to be
synchronized to target systems.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple

from ..interfaces.system_adapter import SourceSystemAdapter
from ..models.base import SourceRecord, EntityType

logger = logging.getLogger(__name__)


class ChangeDetector:
    """
    Component responsible for detecting changes in source systems.
    
    This component detects records that have been created, updated, or deleted
    in the source system since the last synchronization.
    """
    
    def __init__(self, source_adapter: SourceSystemAdapter):
        """
        Initialize the ChangeDetector.
        
        Args:
            source_adapter: Adapter for the source system
        """
        self.source_adapter = source_adapter
    
    async def get_changed_records(
        self,
        entity_type: str,
        since: datetime,
        batch_size: int = 100,
        offset: int = 0
    ) -> Tuple[List[SourceRecord], int]:
        """
        Get records that have changed since a specific time.
        
        Args:
            entity_type: Type of entity to check
            since: Only retrieve records modified since this time
            batch_size: Number of records to retrieve in this batch
            offset: Starting offset for pagination
            
        Returns:
            Tuple containing list of changed records and total count
        """
        logger.info(f"Detecting changes for {entity_type} since {since}")
        
        try:
            # Connect to the source system if not already connected
            if not await self.source_adapter.connect():
                raise ConnectionError(f"Failed to connect to source system")
            
            # Get changed records
            records, total = await self.source_adapter.get_records(
                entity_type=entity_type,
                modified_since=since,
                batch_size=batch_size,
                offset=offset
            )
            
            logger.info(f"Detected {len(records)} changed {entity_type} records "
                        f"(total: {total})")
            
            return records, total
            
        except Exception as e:
            logger.error(f"Error detecting changes for {entity_type}: {str(e)}")
            raise
    
    async def perform_full_change_detection(
        self,
        entity_types: List[str],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Perform a full change detection for multiple entity types.
        
        This method will count all records of the specified entity types in the
        source system, regardless of when they were last modified.
        
        Args:
            entity_types: List of entity types to detect changes for
            batch_size: Batch size for retrieving records
            
        Returns:
            Dictionary mapping entity types to their record counts
        """
        logger.info(f"Performing full change detection for {entity_types}")
        
        try:
            # Connect to the source system if not already connected
            if not await self.source_adapter.connect():
                raise ConnectionError(f"Failed to connect to source system")
            
            # Get record counts for each entity type
            result = {}
            for entity_type in entity_types:
                count = await self.source_adapter.get_record_count(entity_type)
                result[entity_type] = count
                logger.info(f"Detected {count} total {entity_type} records")
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing full change detection: {str(e)}")
            raise
    
    async def get_related_data(
        self,
        primary_entity_type: str,
        primary_ids: Set[str],
        related_entity_types: List[str]
    ) -> Dict[str, List[SourceRecord]]:
        """
        Get related data for a set of primary entity IDs.
        
        This method retrieves related records for entities that are related to the
        primary entities identified by the provided IDs.
        
        Args:
            primary_entity_type: Type of the primary entity
            primary_ids: Set of primary entity IDs
            related_entity_types: List of related entity types to retrieve
            
        Returns:
            Dictionary mapping entity types to lists of records
        """
        logger.info(f"Getting related data for {len(primary_ids)} {primary_entity_type} "
                    f"records, related types: {related_entity_types}")
        
        if not primary_ids:
            logger.info("No primary IDs provided, returning empty result")
            return {entity_type: [] for entity_type in related_entity_types}
        
        try:
            # Connect to the source system if not already connected
            if not await self.source_adapter.connect():
                raise ConnectionError(f"Failed to connect to source system")
            
            # Get related records for each primary ID and entity type
            result = {entity_type: [] for entity_type in related_entity_types}
            
            for primary_id in primary_ids:
                for related_entity_type in related_entity_types:
                    related_records = await self.source_adapter.get_related_records(
                        entity_type=related_entity_type,
                        parent_entity_type=primary_entity_type,
                        parent_id=primary_id
                    )
                    
                    result[related_entity_type].extend(related_records)
            
            # Log the results
            for entity_type, records in result.items():
                logger.info(f"Retrieved {len(records)} related {entity_type} records")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting related data: {str(e)}")
            raise