use crate::error::{Error, Result};
use crate::models::gis_export::{CountyConfiguration, ExportLimits, LayerAttribute, LayerDefinition};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::RwLock;
use once_cell::sync::Lazy;

// Global cache of county configurations for performance
static COUNTY_CONFIGS: Lazy<RwLock<HashMap<String, CountyConfiguration>>> = 
    Lazy::new(|| RwLock::new(HashMap::new()));

/// Load county configuration from database or file system
pub async fn load_county_configuration(county_id: &str) -> Result<CountyConfiguration> {
    // Check if config is already in memory cache
    {
        let configs = COUNTY_CONFIGS.read().unwrap();
        if let Some(config) = configs.get(county_id) {
            return Ok(config.clone());
        }
    }
    
    // In real implementation, load from database
    // For now, return a hard-coded example based on county_id
    let config = match county_id {
        "county-001" => CountyConfiguration {
            county_id: "county-001".to_string(),
            county_name: "Example County".to_string(),
            supported_formats: vec!["geojson".to_string(), "shapefile".to_string(), "kml".to_string()],
            default_parameters: json!({
                "coordinate_system": "EPSG:4326",
                "include_metadata": true,
                "compress_output": true
            }),
            available_layers: vec![
                LayerDefinition {
                    id: "parcels".to_string(),
                    name: "Parcels".to_string(),
                    description: Some("Property parcel boundaries".to_string()),
                    geometry_type: "polygon".to_string(),
                    attributes: vec![
                        LayerAttribute {
                            name: "parcel_id".to_string(),
                            description: Some("Unique parcel identifier".to_string()),
                            data_type: "string".to_string(),
                            is_nullable: false,
                        },
                        LayerAttribute {
                            name: "address".to_string(),
                            description: Some("Property address".to_string()),
                            data_type: "string".to_string(),
                            is_nullable: true,
                        },
                        LayerAttribute {
                            name: "area_sqm".to_string(),
                            description: Some("Area in square meters".to_string()),
                            data_type: "float".to_string(),
                            is_nullable: true,
                        },
                    ],
                    default_style: Some(json!({
                        "fill_color": "#CCCCCC",
                        "stroke_color": "#666666",
                        "stroke_width": 1
                    })),
                },
                LayerDefinition {
                    id: "roads".to_string(),
                    name: "Roads".to_string(),
                    description: Some("Road network".to_string()),
                    geometry_type: "line".to_string(),
                    attributes: vec![
                        LayerAttribute {
                            name: "road_id".to_string(),
                            description: Some("Unique road identifier".to_string()),
                            data_type: "string".to_string(),
                            is_nullable: false,
                        },
                        LayerAttribute {
                            name: "name".to_string(),
                            description: Some("Road name".to_string()),
                            data_type: "string".to_string(),
                            is_nullable: true,
                        },
                        LayerAttribute {
                            name: "type".to_string(),
                            description: Some("Road type".to_string()),
                            data_type: "string".to_string(),
                            is_nullable: true,
                        },
                    ],
                    default_style: Some(json!({
                        "stroke_color": "#333333",
                        "stroke_width": 2
                    })),
                },
            ],
            export_limits: ExportLimits {
                max_features: 50000,
                max_area_sq_km: 100.0,
                max_layers: 5,
            },
        },
        _ => {
            // Default generic configuration for unknown counties
            CountyConfiguration {
                county_id: county_id.to_string(),
                county_name: format!("County {}", county_id),
                supported_formats: vec!["geojson".to_string()],
                default_parameters: json!({
                    "coordinate_system": "EPSG:4326",
                    "include_metadata": true
                }),
                available_layers: vec![
                    LayerDefinition {
                        id: "parcels".to_string(),
                        name: "Parcels".to_string(),
                        description: Some("Property parcel boundaries".to_string()),
                        geometry_type: "polygon".to_string(),
                        attributes: vec![
                            LayerAttribute {
                                name: "id".to_string(),
                                description: Some("Identifier".to_string()),
                                data_type: "string".to_string(),
                                is_nullable: false,
                            },
                        ],
                        default_style: None,
                    },
                ],
                export_limits: ExportLimits {
                    max_features: 10000,
                    max_area_sq_km: 50.0,
                    max_layers: 3,
                },
            }
        }
    };
    
    // Cache the configuration
    {
        let mut configs = COUNTY_CONFIGS.write().unwrap();
        configs.insert(county_id.to_string(), config.clone());
    }
    
    Ok(config)
}

/// Apply county-specific parameters to export request
pub fn apply_county_defaults(parameters: &mut Value, county_config: &CountyConfiguration) {
    if let Some(params_obj) = parameters.as_object_mut() {
        if let Some(default_params) = county_config.default_parameters.as_object() {
            // Apply defaults for any missing parameters
            for (key, value) in default_params {
                if !params_obj.contains_key(key) {
                    params_obj.insert(key.clone(), value.clone());
                }
            }
        }
    }
}

/// Validate export request against county limits
pub fn validate_against_county_limits(
    layers: &[String],
    area_of_interest_sq_km: f64,
    estimated_features: i32,
    county_config: &CountyConfiguration,
) -> Result<()> {
    // Check number of layers
    if layers.len() as i32 > county_config.export_limits.max_layers {
        return Err(Error::InvalidInput(format!(
            "Export exceeds maximum number of layers ({})",
            county_config.export_limits.max_layers
        )));
    }
    
    // Check area size
    if area_of_interest_sq_km > county_config.export_limits.max_area_sq_km {
        return Err(Error::InvalidInput(format!(
            "Export area exceeds maximum size ({} sq km)",
            county_config.export_limits.max_area_sq_km
        )));
    }
    
    // Check estimated features
    if estimated_features > county_config.export_limits.max_features {
        return Err(Error::InvalidInput(format!(
            "Export exceeds maximum number of features ({})",
            county_config.export_limits.max_features
        )));
    }
    
    Ok(())
}