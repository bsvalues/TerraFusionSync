use chrono::{DateTime, Utc};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Identifiable)]
#[diesel(table_name = crate::schema::gis_exports)]
pub struct GisExport {
    pub id: Uuid,
    pub county_id: String,
    pub export_format: String, // geojson, shapefile, kml
    pub status: String, // pending, in_progress, completed, failed, cancelled
    pub area_of_interest: Option<serde_json::Value>, // GeoJSON polygon
    pub layers: serde_json::Value, // Array of layer identifiers
    pub parameters: serde_json::Value, // Export-specific parameters
    pub result_url: Option<String>, // URL to download the export result
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Insertable)]
#[diesel(table_name = crate::schema::gis_exports)]
pub struct NewGisExport {
    pub county_id: String,
    pub export_format: String,
    pub status: String,
    pub area_of_interest: Option<serde_json::Value>,
    pub layers: serde_json::Value,
    pub parameters: serde_json::Value,
    pub created_by: String,
}

impl NewGisExport {
    pub fn new(
        county_id: String,
        export_format: String,
        area_of_interest: Option<serde_json::Value>,
        layers: serde_json::Value,
        parameters: serde_json::Value,
        created_by: String,
    ) -> Self {
        Self {
            county_id,
            export_format,
            status: "pending".to_string(),
            area_of_interest,
            layers,
            parameters,
            created_by,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, AsChangeset)]
#[diesel(table_name = crate::schema::gis_exports)]
pub struct GisExportUpdate {
    pub status: Option<String>,
    pub result_url: Option<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub updated_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisExportResult {
    pub export_id: Uuid,
    pub status: String,
    pub result_url: Option<String>,
    pub layers_processed: i32,
    pub features_exported: i32,
    pub file_size_bytes: Option<i64>,
    pub duration_seconds: f64,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CountyConfiguration {
    pub county_id: String,
    pub county_name: String,
    pub supported_formats: Vec<String>,
    pub default_parameters: serde_json::Value,
    pub available_layers: Vec<LayerDefinition>,
    pub export_limits: ExportLimits,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayerDefinition {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub geometry_type: String, // point, line, polygon
    pub attributes: Vec<LayerAttribute>,
    pub default_style: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayerAttribute {
    pub name: String,
    pub description: Option<String>,
    pub data_type: String,
    pub is_nullable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportLimits {
    pub max_features: i32,
    pub max_area_sq_km: f64,
    pub max_layers: i32,
}