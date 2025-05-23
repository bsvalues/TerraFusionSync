use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use super::BaseModel;

/// GIS Export job
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisExport {
    #[serde(flatten)]
    pub base: BaseModel,
    pub county_id: String,
    pub export_format: GisExportFormat,
    pub status: GisExportStatus,
    pub layers: Vec<String>,
    pub area_of_interest: Option<serde_json::Value>, // GeoJSON geometry
    pub parameters: serde_json::Value,
    pub created_by: String,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub result_url: Option<String>,
    pub error_message: Option<String>,
    pub file_size_bytes: Option<i64>,
}

/// GIS Export format
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum GisExportFormat {
    Shapefile,
    GeoJson,
    Kml,
    Csv,
    Gpkg,
    Geotiff,
    FileGdb,
}

impl AsRef<str> for GisExportFormat {
    fn as_ref(&self) -> &str {
        match self {
            Self::Shapefile => "SHAPEFILE",
            Self::GeoJson => "GEOJSON",
            Self::Kml => "KML",
            Self::Csv => "CSV",
            Self::Gpkg => "GPKG",
            Self::Geotiff => "GEOTIFF",
            Self::FileGdb => "FILEGDB",
        }
    }
}

/// GIS Export status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum GisExportStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Canceled,
}

impl Default for GisExportStatus {
    fn default() -> Self {
        Self::Pending
    }
}

/// GIS Layer definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisLayer {
    pub id: String,
    pub name: String,
    pub description: String,
    pub geometry_type: GeometryType,
    pub attributes: Vec<GisAttribute>,
    pub is_enabled: bool,
    pub county_id: String,
    pub source_table: Option<String>,
    pub source_query: Option<String>,
    pub style: Option<serde_json::Value>,
}

/// GIS Layer attribute
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisAttribute {
    pub name: String,
    pub description: Option<String>,
    pub data_type: AttributeDataType,
    pub is_required: bool,
    pub is_exportable: bool,
    pub default_value: Option<serde_json::Value>,
}

/// Geometry type for GIS layers
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum GeometryType {
    Point,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
}

/// Attribute data type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum AttributeDataType {
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Json,
}

/// County configuration for GIS exports
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CountyGisConfig {
    pub county_id: String,
    pub name: String,
    pub supported_formats: Vec<GisExportFormat>,
    pub default_projection: String, // EPSG:XXXX
    pub available_projections: Vec<String>,
    pub max_export_area_sq_km: Option<f64>,
    pub max_export_features: Option<i32>,
    pub default_parameters: serde_json::Value,
}

/// GIS Export creation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateGisExportRequest {
    pub county_id: String,
    pub export_format: GisExportFormat,
    pub layers: Vec<String>,
    pub area_of_interest: Option<serde_json::Value>, // GeoJSON geometry
    pub parameters: serde_json::Value,
}

/// GIS Export job status response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GisExportStatusResponse {
    pub id: Uuid,
    pub status: GisExportStatus,
    pub progress_percent: Option<i32>,
    pub message: Option<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub result_url: Option<String>,
    pub error_message: Option<String>,
}

/// Coordinate system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoordinateSystem {
    pub code: String, // e.g., "EPSG:4326"
    pub name: String,
    pub wkt: String,  // Well-known text representation
    pub is_geographic: bool,
    pub area_of_use: Option<String>,
}

/// Bounding box
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min_x: f64,
    pub min_y: f64,
    pub max_x: f64,
    pub max_y: f64,
}

impl BoundingBox {
    pub fn width(&self) -> f64 {
        self.max_x - self.min_x
    }
    
    pub fn height(&self) -> f64 {
        self.max_y - self.min_y
    }
    
    pub fn center_x(&self) -> f64 {
        (self.min_x + self.max_x) / 2.0
    }
    
    pub fn center_y(&self) -> f64 {
        (self.min_y + self.max_y) / 2.0
    }
    
    pub fn contains_point(&self, x: f64, y: f64) -> bool {
        x >= self.min_x && x <= self.max_x && y >= self.min_y && y <= self.max_y
    }
    
    pub fn overlaps(&self, other: &BoundingBox) -> bool {
        self.min_x <= other.max_x && self.max_x >= other.min_x &&
        self.min_y <= other.max_y && self.max_y >= other.min_y
    }
}