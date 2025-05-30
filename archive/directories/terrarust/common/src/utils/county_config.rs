use std::collections::HashMap;
use std::fs::File;
use std::io::Read;
use std::path::Path;

use crate::error::{Error, Result};
use crate::models::gis_export::{CountyConfiguration, LayerDefinition, RateLimits};

// Cache for county configurations to avoid repeated file reads
static mut CONFIG_CACHE: Option<HashMap<String, CountyConfiguration>> = None;

/// Load a county configuration from file or cache
pub async fn load_county_configuration(county_id: &str) -> Result<CountyConfiguration> {
    // Check cache first
    unsafe {
        if let Some(cache) = &CONFIG_CACHE {
            if let Some(config) = cache.get(county_id) {
                return Ok(config.clone());
            }
        }
    }
    
    // Otherwise load from file and cache it
    let config_path = format!("county_configs/{}/config.json", county_id);
    let config = load_config_from_file(config_path)?;
    
    // Cache the result
    unsafe {
        if CONFIG_CACHE.is_none() {
            CONFIG_CACHE = Some(HashMap::new());
        }
        
        if let Some(cache) = &mut CONFIG_CACHE {
            cache.insert(county_id.to_string(), config.clone());
        }
    }
    
    Ok(config)
}

/// Load configuration from a file
fn load_config_from_file<P: AsRef<Path>>(path: P) -> Result<CountyConfiguration> {
    let mut file = File::open(&path)
        .map_err(|e| Error::NotFound(format!("County config file not found: {}: {}", path.as_ref().display(), e)))?;
    
    let mut content = String::new();
    file.read_to_string(&mut content)
        .map_err(|e| Error::Internal(format!("Failed to read county config file: {}", e)))?;
    
    let config: CountyConfiguration = serde_json::from_str(&content)
        .map_err(|e| Error::Internal(format!("Failed to parse county config file: {}", e)))?;
    
    Ok(config)
}

/// Apply county-specific default parameters to an export request
pub fn apply_county_defaults(params: &mut serde_json::Value, county_config: &CountyConfiguration) {
    if let (Some(default_params), Some(request_params)) = (county_config.default_parameters.as_object(), params.as_object_mut()) {
        for (key, value) in default_params {
            if !request_params.contains_key(key) {
                request_params.insert(key.clone(), value.clone());
            }
        }
    }
}

/// Generate a default county configuration for testing
pub fn generate_default_config(county_id: &str) -> CountyConfiguration {
    let parcels_layer = LayerDefinition {
        id: "parcels".to_string(),
        name: "Parcels".to_string(),
        description: "Property parcels with ownership and assessment data".to_string(),
        layer_type: "polygon".to_string(),
        default_parameters: serde_json::json!({
            "include_ownership": true,
            "include_assessment": true
        }),
        required_permissions: vec!["read:parcels".to_string()],
        metadata: serde_json::json!({
            "source": "County Assessor's Office",
            "update_frequency": "daily"
        }),
    };
    
    let roads_layer = LayerDefinition {
        id: "roads".to_string(),
        name: "Roads".to_string(),
        description: "Road centerlines with classification and naming".to_string(),
        layer_type: "linestring".to_string(),
        default_parameters: serde_json::json!({
            "include_classification": true
        }),
        required_permissions: vec!["read:roads".to_string()],
        metadata: serde_json::json!({
            "source": "County GIS Department",
            "update_frequency": "monthly"
        }),
    };
    
    let buildings_layer = LayerDefinition {
        id: "buildings".to_string(),
        name: "Buildings".to_string(),
        description: "Building footprints with attributes".to_string(),
        layer_type: "polygon".to_string(),
        default_parameters: serde_json::json!({
            "include_height": true,
            "include_year_built": true
        }),
        required_permissions: vec!["read:buildings".to_string()],
        metadata: serde_json::json!({
            "source": "County Planning Department",
            "update_frequency": "quarterly"
        }),
    };
    
    let rate_limits = RateLimits {
        max_concurrent_exports: 5,
        max_exports_per_day: 50,
        max_exports_per_user: 10,
        max_area_square_miles: 100.0,
    };
    
    CountyConfiguration {
        county_id: county_id.to_string(),
        county_name: format!("{} County", county_id),
        available_export_formats: vec![
            "geojson".to_string(),
            "shapefile".to_string(),
            "kml".to_string(),
        ],
        default_export_format: "geojson".to_string(),
        available_layers: vec![parcels_layer, roads_layer, buildings_layer],
        rate_limits,
        default_parameters: serde_json::json!({
            "coordinate_system": "EPSG:4326",
            "include_metadata": true
        }),
        authentication_required: true,
    }
}