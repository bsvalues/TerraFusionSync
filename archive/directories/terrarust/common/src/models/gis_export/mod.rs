use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisExport {
    pub id: Uuid,
    pub county_id: String,
    pub export_format: String,
    pub status: String,
    pub area_of_interest: Option<serde_json::Value>,
    pub layers: serde_json::Value,
    pub parameters: serde_json::Value,
    pub result_url: Option<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayerDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub layer_type: String,
    pub default_parameters: serde_json::Value,
    pub required_permissions: Vec<String>,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CountyConfiguration {
    pub county_id: String,
    pub county_name: String,
    pub available_export_formats: Vec<String>,
    pub default_export_format: String,
    pub available_layers: Vec<LayerDefinition>,
    pub rate_limits: RateLimits,
    pub default_parameters: serde_json::Value,
    pub authentication_required: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimits {
    pub max_concurrent_exports: u32,
    pub max_exports_per_day: u32,
    pub max_exports_per_user: u32,
    pub max_area_square_miles: f64,
}

impl CountyConfiguration {
    pub fn is_format_supported(&self, format: &str) -> bool {
        self.available_export_formats
            .iter()
            .any(|f| f.to_lowercase() == format.to_lowercase())
    }
    
    pub fn is_layer_available(&self, layer_id: &str) -> bool {
        self.available_layers
            .iter()
            .any(|l| l.id == layer_id)
    }
    
    pub fn get_layer(&self, layer_id: &str) -> Option<&LayerDefinition> {
        self.available_layers
            .iter()
            .find(|l| l.id == layer_id)
    }
}