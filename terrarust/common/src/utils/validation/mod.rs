use crate::error::{Error, Result};
use serde_json::Value;
use std::collections::HashMap;

pub struct ValidationResult {
    pub is_valid: bool,
    pub errors: Vec<ValidationError>,
    pub warnings: Vec<ValidationWarning>,
}

pub struct ValidationError {
    pub field: String,
    pub message: String,
    pub code: Option<String>,
    pub details: Option<Value>,
}

pub struct ValidationWarning {
    pub field: String,
    pub message: String,
    pub code: Option<String>,
    pub details: Option<Value>,
}

impl ValidationResult {
    pub fn new() -> Self {
        Self {
            is_valid: true,
            errors: Vec::new(),
            warnings: Vec::new(),
        }
    }
    
    pub fn add_error(&mut self, field: &str, message: &str, code: Option<&str>, details: Option<Value>) {
        self.is_valid = false;
        self.errors.push(ValidationError {
            field: field.to_string(),
            message: message.to_string(),
            code: code.map(|s| s.to_string()),
            details,
        });
    }
    
    pub fn add_warning(&mut self, field: &str, message: &str, code: Option<&str>, details: Option<Value>) {
        self.warnings.push(ValidationWarning {
            field: field.to_string(),
            message: message.to_string(),
            code: code.map(|s| s.to_string()),
            details,
        });
    }
    
    pub fn has_errors(&self) -> bool {
        !self.errors.is_empty()
    }
    
    pub fn has_warnings(&self) -> bool {
        !self.warnings.is_empty()
    }
}

pub fn validate_sync_pair_config(
    source_system: &str,
    target_system: &str,
    source_config: &Value,
    target_config: &Value,
    field_mappings: &Value,
) -> ValidationResult {
    let mut result = ValidationResult::new();
    
    // Validate source system
    if source_system.is_empty() {
        result.add_error("source_system", "Source system cannot be empty", Some("EMPTY_SOURCE"), None);
    }
    
    // Validate target system
    if target_system.is_empty() {
        result.add_error("target_system", "Target system cannot be empty", Some("EMPTY_TARGET"), None);
    }
    
    // Validate source configuration
    if !source_config.is_object() {
        result.add_error("source_config", "Source configuration must be an object", Some("INVALID_SOURCE_CONFIG"), None);
    }
    
    // Validate target configuration
    if !target_config.is_object() {
        result.add_error("target_config", "Target configuration must be an object", Some("INVALID_TARGET_CONFIG"), None);
    }
    
    // Validate field mappings
    if !field_mappings.is_array() {
        result.add_error("field_mappings", "Field mappings must be an array", Some("INVALID_FIELD_MAPPINGS"), None);
    } else if let Some(mappings) = field_mappings.as_array() {
        if mappings.is_empty() {
            result.add_error("field_mappings", "Field mappings cannot be empty", Some("EMPTY_FIELD_MAPPINGS"), None);
        } else {
            // Check each field mapping
            for (i, mapping) in mappings.iter().enumerate() {
                if !mapping.is_object() {
                    result.add_error(
                        &format!("field_mappings[{}]", i),
                        "Field mapping must be an object",
                        Some("INVALID_MAPPING"),
                        None,
                    );
                    continue;
                }
                
                // Check required fields in mapping
                let mapping_obj = mapping.as_object().unwrap();
                if !mapping_obj.contains_key("source_field") {
                    result.add_error(
                        &format!("field_mappings[{}].source_field", i),
                        "Source field is required",
                        Some("MISSING_SOURCE_FIELD"),
                        None,
                    );
                }
                
                if !mapping_obj.contains_key("target_field") {
                    result.add_error(
                        &format!("field_mappings[{}].target_field", i),
                        "Target field is required",
                        Some("MISSING_TARGET_FIELD"),
                        None,
                    );
                }
            }
        }
    }
    
    result
}

pub fn validate_gis_export_request(
    county_id: &str,
    export_format: &str,
    layers: &Value,
    parameters: &Value,
    county_config: &Value,
) -> ValidationResult {
    let mut result = ValidationResult::new();
    
    // Validate county ID
    if county_id.is_empty() {
        result.add_error("county_id", "County ID cannot be empty", Some("EMPTY_COUNTY"), None);
    }
    
    // Validate export format
    let valid_formats = vec!["geojson", "shapefile", "kml"];
    if !valid_formats.contains(&export_format) {
        result.add_error(
            "export_format",
            &format!("Invalid export format. Valid formats are: {}", valid_formats.join(", ")),
            Some("INVALID_FORMAT"),
            None,
        );
    }
    
    // Validate layers
    if !layers.is_array() {
        result.add_error("layers", "Layers must be an array", Some("INVALID_LAYERS"), None);
    } else if let Some(layers_arr) = layers.as_array() {
        if layers_arr.is_empty() {
            result.add_error("layers", "At least one layer must be specified", Some("EMPTY_LAYERS"), None);
        }
    }
    
    // Validate parameters
    if !parameters.is_object() {
        result.add_error("parameters", "Parameters must be an object", Some("INVALID_PARAMETERS"), None);
    }
    
    // Check against county configuration if available
    if county_config.is_object() {
        if let Some(config) = county_config.as_object() {
            // Check if export format is supported by county
            if let Some(supported_formats) = config.get("supported_formats") {
                if let Some(formats_arr) = supported_formats.as_array() {
                    let supported_format_strings: Vec<String> = formats_arr
                        .iter()
                        .filter_map(|v| v.as_str().map(|s| s.to_string()))
                        .collect();
                    
                    if !supported_format_strings.contains(&export_format.to_string()) {
                        result.add_error(
                            "export_format",
                            &format!(
                                "Export format '{}' is not supported by county. Supported formats: {}",
                                export_format,
                                supported_format_strings.join(", ")
                            ),
                            Some("UNSUPPORTED_FORMAT"),
                            None,
                        );
                    }
                }
            }
            
            // Check layers against county config
            if let Some(layers_arr) = layers.as_array() {
                if let Some(available_layers) = config.get("available_layers") {
                    if let Some(available_arr) = available_layers.as_array() {
                        let available_layer_ids: Vec<String> = available_arr
                            .iter()
                            .filter_map(|v| {
                                if let Some(obj) = v.as_object() {
                                    obj.get("id").and_then(|id| id.as_str().map(|s| s.to_string()))
                                } else {
                                    None
                                }
                            })
                            .collect();
                        
                        for (i, layer) in layers_arr.iter().enumerate() {
                            if let Some(layer_id) = layer.as_str() {
                                if !available_layer_ids.contains(&layer_id.to_string()) {
                                    result.add_error(
                                        &format!("layers[{}]", i),
                                        &format!("Layer '{}' is not available for this county", layer_id),
                                        Some("UNAVAILABLE_LAYER"),
                                        None,
                                    );
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    result
}