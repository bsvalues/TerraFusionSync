"""
Transformer component for the SyncService.

This module is responsible for transforming data from source format to target format
according to field mapping rules, and enriching data with AI capabilities.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from openai import AsyncOpenAI

from syncservice.config import get_settings
from syncservice.models.base import AuditEvent
from syncservice.models.cama import (CAMAOwnerSchema, CAMAPropertySchema,
                                   CAMAStructureSchema, CAMAValueSchema)
from syncservice.models.pacs import (PACSOwnerSchema, PACSPropertySchema,
                                    PACSStructureSchema,
                                    PACSValueHistorySchema)
from syncservice.utils.event_bus import publish_event

logger = logging.getLogger(__name__)


class Transformer:
    """Transforms data between source and target systems using field mappings."""

    def __init__(self):
        """Initialize the Transformer component."""
        self.field_mapping = self._load_field_mapping()
        
        # Initialize OpenAI client if API key is available
        settings = get_settings()
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    def _load_field_mapping(self) -> Dict:
        """
        Load field mapping configuration from YAML file.
        
        Returns:
            Dictionary containing field mapping rules.
        """
        settings = get_settings()
        try:
            with open(settings.field_mapping_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load field mapping: {str(e)}")
            # Use default mapping if file not found
            return {
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
                },
                "owner": {
                    "OwnerID": "source_id",
                    "PropertyID": "property_id", 
                    "OwnerName": "owner_name",
                    "OwnerType": "owner_type",
                    "OwnershipPercentage": "ownership_percentage",
                    "StartDate": "start_date",
                    "EndDate": "end_date",
                    "LastModified": "source_last_modified"
                },
                "value": {
                    "ValueID": "source_id",
                    "PropertyID": "property_id",
                    "TaxYear": "tax_year",
                    "AssessedValue": "assessed_value",
                    "MarketValue": "market_value",
                    "LandValue": "land_value",
                    "ImprovementValue": "improvement_value",
                    "LastModified": "source_last_modified"
                },
                "structure": {
                    "StructureID": "source_id",
                    "PropertyID": "property_id",
                    "StructureType": "structure_type",
                    "SquareFootage": "square_footage",
                    "Condition": "condition",
                    "YearBuilt": "year_built",
                    "Bedrooms": "bedrooms",
                    "Bathrooms": "bathrooms",
                    "LastModified": "source_last_modified"
                }
            }

    async def transform_property(
        self, 
        pacs_property: Dict
    ) -> CAMAPropertySchema:
        """
        Transform a PACS property to CAMA format.
        
        Args:
            pacs_property: Property data from PACS
            
        Returns:
            Transformed CAMA property object
        """
        # Create a property object from PACS data using field mapping
        property_data = {}
        
        # Get field mapping for property
        field_map = self.field_mapping.get("property", {})
        
        # Map fields according to configuration
        for source_field, target_field in field_map.items():
            if source_field in pacs_property:
                property_data[target_field] = pacs_property[source_field]
        
        # Generate additional data with AI enrichment
        additional_data = await self._enrich_property_data(pacs_property)
        if additional_data:
            property_data["additional_data"] = additional_data
        
        # Get or generate geo coordinates
        geo_coordinates = await self._generate_geo_coordinates(pacs_property)
        if geo_coordinates:
            property_data["geo_coordinates"] = geo_coordinates
        
        # Create a valid CAMA property object
        cama_property = CAMAPropertySchema(
            id=str(uuid.uuid4()),  # New UUID for CAMA
            **property_data
        )
        
        # Log transformation event
        await publish_event(
            "property_transformed",
            {
                "source_id": pacs_property.get("PropertyID"),
                "target_id": cama_property.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return cama_property

    async def transform_owner(
        self, 
        pacs_owner: Dict,
        property_id_map: Dict[str, str]
    ) -> CAMAOwnerSchema:
        """
        Transform a PACS owner to CAMA format.
        
        Args:
            pacs_owner: Owner data from PACS
            property_id_map: Mapping from source property IDs to target property IDs
            
        Returns:
            Transformed CAMA owner object
        """
        # Create an owner object from PACS data using field mapping
        owner_data = {}
        
        # Get field mapping for owner
        field_map = self.field_mapping.get("owner", {})
        
        # Map fields according to configuration
        for source_field, target_field in field_map.items():
            if source_field in pacs_owner:
                # Special handling for property_id references
                if source_field == "PropertyID" and target_field == "property_id":
                    # Look up the corresponding CAMA property ID
                    source_property_id = pacs_owner["PropertyID"]
                    if source_property_id in property_id_map:
                        owner_data[target_field] = property_id_map[source_property_id]
                    else:
                        logger.warning(f"No target property ID found for source ID: {source_property_id}")
                else:
                    owner_data[target_field] = pacs_owner[source_field]
        
        # Add contact information with AI enrichment
        contact_info = await self._generate_contact_information(pacs_owner)
        if contact_info:
            owner_data["contact_information"] = contact_info
        
        # Create a valid CAMA owner object
        cama_owner = CAMAOwnerSchema(
            id=str(uuid.uuid4()),  # New UUID for CAMA
            **owner_data
        )
        
        # Log transformation event
        await publish_event(
            "owner_transformed",
            {
                "source_id": pacs_owner.get("OwnerID"),
                "target_id": cama_owner.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return cama_owner

    async def transform_value(
        self, 
        pacs_value: Dict,
        property_id_map: Dict[str, str]
    ) -> CAMAValueSchema:
        """
        Transform a PACS value history to CAMA value format.
        
        Args:
            pacs_value: Value history data from PACS
            property_id_map: Mapping from source property IDs to target property IDs
            
        Returns:
            Transformed CAMA value object
        """
        # Create a value object from PACS data using field mapping
        value_data = {}
        
        # Get field mapping for value
        field_map = self.field_mapping.get("value", {})
        
        # Map fields according to configuration
        for source_field, target_field in field_map.items():
            if source_field in pacs_value:
                # Special handling for property_id references
                if source_field == "PropertyID" and target_field == "property_id":
                    # Look up the corresponding CAMA property ID
                    source_property_id = pacs_value["PropertyID"]
                    if source_property_id in property_id_map:
                        value_data[target_field] = property_id_map[source_property_id]
                    else:
                        logger.warning(f"No target property ID found for source ID: {source_property_id}")
                else:
                    value_data[target_field] = pacs_value[source_field]
        
        # Add valuation method with AI enrichment
        valuation_method = await self._determine_valuation_method(pacs_value)
        if valuation_method:
            value_data["valuation_method"] = valuation_method
        
        # Create a valid CAMA value object
        cama_value = CAMAValueSchema(
            id=str(uuid.uuid4()),  # New UUID for CAMA
            **value_data
        )
        
        # Log transformation event
        await publish_event(
            "value_transformed",
            {
                "source_id": pacs_value.get("ValueID"),
                "target_id": cama_value.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return cama_value

    async def transform_structure(
        self, 
        pacs_structure: Dict,
        property_id_map: Dict[str, str]
    ) -> CAMAStructureSchema:
        """
        Transform a PACS structure to CAMA format.
        
        Args:
            pacs_structure: Structure data from PACS
            property_id_map: Mapping from source property IDs to target property IDs
            
        Returns:
            Transformed CAMA structure object
        """
        # Create a structure object from PACS data using field mapping
        structure_data = {}
        
        # Get field mapping for structure
        field_map = self.field_mapping.get("structure", {})
        
        # Map fields according to configuration
        for source_field, target_field in field_map.items():
            if source_field in pacs_structure:
                # Special handling for property_id references
                if source_field == "PropertyID" and target_field == "property_id":
                    # Look up the corresponding CAMA property ID
                    source_property_id = pacs_structure["PropertyID"]
                    if source_property_id in property_id_map:
                        structure_data[target_field] = property_id_map[source_property_id]
                    else:
                        logger.warning(f"No target property ID found for source ID: {source_property_id}")
                else:
                    structure_data[target_field] = pacs_structure[source_field]
        
        # Add construction details with AI enrichment
        construction_details = await self._generate_construction_details(pacs_structure)
        if construction_details:
            structure_data["construction_details"] = construction_details
        
        # Add amenities with AI enrichment
        amenities = await self._generate_amenities(pacs_structure)
        if amenities:
            structure_data["amenities"] = amenities
        
        # Create a valid CAMA structure object
        cama_structure = CAMAStructureSchema(
            id=str(uuid.uuid4()),  # New UUID for CAMA
            **structure_data
        )
        
        # Log transformation event
        await publish_event(
            "structure_transformed",
            {
                "source_id": pacs_structure.get("StructureID"),
                "target_id": cama_structure.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return cama_structure

    async def _enrich_property_data(self, pacs_property: Dict) -> Optional[Dict]:
        """
        Use AI to enrich property data with additional insights.
        
        Args:
            pacs_property: Property data from PACS
            
        Returns:
            Dictionary with enriched data or None if enrichment failed
        """
        if not self.openai_client:
            return None
        
        try:
            # Extract key property details for the AI to work with
            property_summary = {
                "parcel": pacs_property.get("ParcelNumber"),
                "address": pacs_property.get("Address"),
                "city": pacs_property.get("City"),
                "state": pacs_property.get("State"),
                "acreage": pacs_property.get("Acreage"),
                "year_built": pacs_property.get("YearBuilt"),
            }
            
            prompt = f"""
            Based on the following property details:
            {json.dumps(property_summary)}
            
            Please provide a JSON object with the following additional information:
            1. property_class: Residential, Commercial, Agricultural, etc.
            2. neighborhood_quality: rating from 1-5
            3. estimated_weather_risk: Low, Medium, High
            4. urban_rural_classification: Urban, Suburban, Rural
            5. estimated_school_district_quality: rating from 1-5
            
            Return ONLY valid JSON without explanation.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            
            # Extract and parse JSON response
            result_text = response.choices[0].message.content.strip()
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"AI enrichment failed for property: {str(e)}")
            return None

    async def _generate_geo_coordinates(self, pacs_property: Dict) -> Optional[Dict]:
        """
        Generate geocoordinates for a property based on its address.
        
        Args:
            pacs_property: Property data from PACS
            
        Returns:
            Dictionary with latitude and longitude or None if generation failed
        """
        if not self.openai_client:
            return None
        
        # Ensure we have an address to work with
        address = pacs_property.get("Address")
        city = pacs_property.get("City")
        state = pacs_property.get("State")
        
        if not (address and city and state):
            return None
            
        try:
            # Combine address components
            full_address = f"{address}, {city}, {state}"
            
            prompt = f"""
            For the address:
            {full_address}
            
            Please provide a JSON object with estimated latitude and longitude.
            Include only the JSON like this:
            {{
                "latitude": 37.8267,
                "longitude": -122.4233
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1,
            )
            
            # Extract and parse JSON response
            result_text = response.choices[0].message.content.strip()
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Geo coordinates generation failed: {str(e)}")
            return None

    async def _generate_contact_information(self, pacs_owner: Dict) -> Optional[Dict]:
        """
        Generate contact information for an owner.
        
        Args:
            pacs_owner: Owner data from PACS
            
        Returns:
            Dictionary with contact details or None if generation failed
        """
        # For demonstration, return placeholder contact info
        # In production, this would integrate with a contact database
        return {
            "contact_method": "mail",
            "mailing_address": "Same as property",
            "contact_preference": "written"
        }

    async def _determine_valuation_method(self, pacs_value: Dict) -> Optional[str]:
        """
        Determine the valuation method used for a property value.
        
        Args:
            pacs_value: Value history data from PACS
            
        Returns:
            String describing the valuation method or None if determination failed
        """
        # Simple logic to determine valuation method
        market_value = pacs_value.get("MarketValue", 0)
        assessed_value = pacs_value.get("AssessedValue", 0)
        
        if market_value > 1000000:
            return "income_approach"
        elif assessed_value == market_value:
            return "market_approach"
        else:
            return "cost_approach"

    async def _generate_construction_details(self, pacs_structure: Dict) -> Optional[Dict]:
        """
        Generate construction details for a structure.
        
        Args:
            pacs_structure: Structure data from PACS
            
        Returns:
            Dictionary with construction details or None if generation failed
        """
        # Based on structure type and condition, determine construction details
        structure_type = pacs_structure.get("StructureType", "")
        condition = pacs_structure.get("Condition", "")
        year_built = pacs_structure.get("YearBuilt", 0)
        
        # Default mapping for residential structures
        if "residential" in structure_type.lower():
            return {
                "foundation_type": "concrete_slab" if year_built > 1970 else "basement",
                "roof_material": "asphalt_shingle",
                "exterior_wall": "vinyl_siding" if year_built > 1980 else "brick",
                "quality_grade": "B" if condition == "Good" else "C"
            }
        
        # Default mapping for commercial structures
        elif "commercial" in structure_type.lower():
            return {
                "foundation_type": "concrete_slab",
                "roof_material": "membrane",
                "exterior_wall": "concrete_block" if year_built > 1970 else "brick",
                "quality_grade": "A" if condition == "Excellent" else "B"
            }
        
        return None

    async def _generate_amenities(self, pacs_structure: Dict) -> Optional[Dict]:
        """
        Generate amenities for a structure.
        
        Args:
            pacs_structure: Structure data from PACS
            
        Returns:
            Dictionary with amenities or None if generation failed
        """
        # Based on structure type and characteristics, determine amenities
        structure_type = pacs_structure.get("StructureType", "")
        bedrooms = pacs_structure.get("Bedrooms", 0)
        bathrooms = pacs_structure.get("Bathrooms", 0)
        
        # Default mapping for residential structures
        if "residential" in structure_type.lower():
            return {
                "has_garage": True if bedrooms > 2 else False,
                "has_fireplace": True if bedrooms > 3 else False,
                "has_pool": False,
                "has_central_air": True,
                "has_basement": True if "basement" in structure_type.lower() else False
            }
        
        # Default mapping for commercial structures
        elif "commercial" in structure_type.lower():
            return {
                "has_elevator": True if "multi_story" in structure_type.lower() else False,
                "has_loading_dock": True if "warehouse" in structure_type.lower() else False,
                "security_system": True,
                "sprinkler_system": True
            }
        
        return None

    async def batch_transform_records(
        self, 
        records: Dict[str, List[Dict]]
    ) -> Dict[str, List]:
        """
        Transform a batch of records from source to target format.
        
        Args:
            records: Dictionary containing records by entity type
            
        Returns:
            Dictionary with transformed records by entity type
        """
        logger.info(f"Starting batch transformation of records")
        
        # Transform properties first to build ID mapping
        properties = []
        property_id_map = {}  # Map source IDs to target IDs
        
        # Process properties
        for pacs_property in records.get("properties", []):
            try:
                cama_property = await self.transform_property(pacs_property)
                properties.append(cama_property)
                
                # Map source ID to target ID
                property_id_map[pacs_property["PropertyID"]] = cama_property.id
            except Exception as e:
                logger.error(f"Error transforming property {pacs_property.get('PropertyID')}: {str(e)}")
        
        # Process owners using property ID mapping
        owners = []
        for pacs_owner in records.get("owners", []):
            try:
                cama_owner = await self.transform_owner(pacs_owner, property_id_map)
                owners.append(cama_owner)
            except Exception as e:
                logger.error(f"Error transforming owner {pacs_owner.get('OwnerID')}: {str(e)}")
        
        # Process values using property ID mapping
        values = []
        for pacs_value in records.get("values", []):
            try:
                cama_value = await self.transform_value(pacs_value, property_id_map)
                values.append(cama_value)
            except Exception as e:
                logger.error(f"Error transforming value {pacs_value.get('ValueID')}: {str(e)}")
        
        # Process structures using property ID mapping
        structures = []
        for pacs_structure in records.get("structures", []):
            try:
                cama_structure = await self.transform_structure(pacs_structure, property_id_map)
                structures.append(cama_structure)
            except Exception as e:
                logger.error(f"Error transforming structure {pacs_structure.get('StructureID')}: {str(e)}")
        
        # Also process any related records
        related = records.get("related", {})
        
        # Process related properties
        for pacs_property in related.get("properties", []):
            if pacs_property["PropertyID"] not in property_id_map:
                try:
                    cama_property = await self.transform_property(pacs_property)
                    properties.append(cama_property)
                    
                    # Map source ID to target ID
                    property_id_map[pacs_property["PropertyID"]] = cama_property.id
                except Exception as e:
                    logger.error(f"Error transforming related property {pacs_property.get('PropertyID')}: {str(e)}")
        
        # Process related owners, values, and structures
        for pacs_owner in related.get("owners", []):
            try:
                if pacs_owner["PropertyID"] in property_id_map:
                    cama_owner = await self.transform_owner(pacs_owner, property_id_map)
                    owners.append(cama_owner)
            except Exception as e:
                logger.error(f"Error transforming related owner {pacs_owner.get('OwnerID')}: {str(e)}")
                
        for pacs_value in related.get("values", []):
            try:
                if pacs_value["PropertyID"] in property_id_map:
                    cama_value = await self.transform_value(pacs_value, property_id_map)
                    values.append(cama_value)
            except Exception as e:
                logger.error(f"Error transforming related value {pacs_value.get('ValueID')}: {str(e)}")
                
        for pacs_structure in related.get("structures", []):
            try:
                if pacs_structure["PropertyID"] in property_id_map:
                    cama_structure = await self.transform_structure(pacs_structure, property_id_map)
                    structures.append(cama_structure)
            except Exception as e:
                logger.error(f"Error transforming related structure {pacs_structure.get('StructureID')}: {str(e)}")
        
        # Publish summary event
        await publish_event(
            "batch_transformation_completed",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "record_count": {
                    "properties": len(properties),
                    "owners": len(owners),
                    "values": len(values),
                    "structures": len(structures),
                }
            }
        )
        
        return {
            "properties": properties,
            "owners": owners,
            "values": values,
            "structures": structures,
            "property_id_map": property_id_map
        }
