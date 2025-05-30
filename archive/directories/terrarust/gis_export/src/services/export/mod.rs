use common::error::{Error, Result};
use common::database::Database;
use common::telemetry::TelemetryService;
use common::models::gis_export::{GisExport, CountyConfiguration, LayerDefinition};
use common::utils::county_config;
use geojson::{Feature, FeatureCollection, Geometry};
use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::Instant;
use tokio::sync::RwLock;
use uuid::Uuid;
use chrono::Utc;
use std::time::Duration;
use prometheus::Histogram;

/// The GisExportService handles the creation and processing of GIS export jobs
#[derive(Clone)]
pub struct GisExportService {
    database: Database,
    telemetry: Arc<TelemetryService>,
    active_exports: Arc<RwLock<HashSet<Uuid>>>,
    cancellation_requests: Arc<RwLock<HashSet<Uuid>>>,
}

impl GisExportService {
    pub fn new(database: Database, telemetry: Arc<TelemetryService>) -> Self {
        Self {
            database,
            telemetry,
            active_exports: Arc::new(RwLock::new(HashSet::new())),
            cancellation_requests: Arc::new(RwLock::new(HashSet::new())),
        }
    }
    
    /// Create a new GIS export job
    pub async fn create_export(
        &self,
        county_id: String,
        export_format: String,
        area_of_interest: Option<serde_json::Value>,
        layers: Vec<String>,
        parameters: serde_json::Value,
        created_by: String,
    ) -> Result<GisExport> {
        // Validate export format
        let valid_formats = vec!["geojson", "shapefile", "kml"];
        if !valid_formats.contains(&export_format.as_str()) {
            return Err(Error::InvalidInput(format!(
                "Invalid export format: {}. Valid formats are: {}",
                export_format,
                valid_formats.join(", ")
            )));
        }
        
        // Validate layers
        if layers.is_empty() {
            return Err(Error::InvalidInput("At least one layer must be specified".to_string()));
        }
        
        // Get county configuration
        let county_config = county_config::load_county_configuration(&county_id).await?;
        
        // Validate that all layers exist in county configuration
        let available_layer_ids: Vec<String> = county_config.available_layers
            .iter()
            .map(|layer| layer.id.clone())
            .collect();
            
        for layer_id in &layers {
            if !available_layer_ids.contains(layer_id) {
                return Err(Error::InvalidInput(format!(
                    "Layer '{}' is not available for county {}",
                    layer_id,
                    county_id
                )));
            }
        }
        
        // Convert layers to JSON array
        let layers_json = serde_json::to_value(&layers)?;
        
        // Apply county-specific parameter defaults
        let mut parameters_value = parameters.clone();
        county_config::apply_county_defaults(&mut parameters_value, &county_config);
        
        // Create the export record
        let export = GisExport {
            id: Uuid::new_v4(),
            county_id,
            export_format,
            status: "pending".to_string(),
            area_of_interest,
            layers: layers_json,
            parameters: parameters_value,
            result_url: None,
            started_at: None,
            completed_at: None,
            error_message: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            created_by,
        };
        
        // In a real implementation, we would save this to the database
        // and then trigger the actual export process
        
        // Increment export counter in metrics
        self.telemetry.gis_exports_total.inc();
        
        // Return the export record
        Ok(export)
    }
    
    /// Execute a GIS export job
    pub async fn execute_export(&self, export_id: Uuid) -> Result<String> {
        // Update export status to in_progress
        // In a real implementation, this would update the database
        
        // Track metrics
        self.telemetry.gis_exports_in_progress.inc();
        
        // Add to active exports
        {
            let mut active_exports = self.active_exports.write().await;
            active_exports.insert(export_id);
        }
        
        // Start timer for metrics
        let timer = self.telemetry.gis_export_duration.start_timer();
        
        // Simulate export process
        let result = async {
            // Simulate some processing time
            tokio::time::sleep(Duration::from_secs(2)).await;
            
            // Check if export was cancelled
            if self.is_export_cancelled(export_id).await {
                return Err(Error::GisProcessing("Export was cancelled".to_string()));
            }
            
            // Generate a result URL
            let result_url = format!("https://storage.example.com/exports/{}.zip", export_id);
            
            Ok(result_url)
        }.await;
        
        // Stop timer
        timer.observe_duration();
        
        // Remove from active exports
        {
            let mut active_exports = self.active_exports.write().await;
            active_exports.remove(&export_id);
        }
        
        // Remove from cancellation requests if present
        {
            let mut cancellation_reqs = self.cancellation_requests.write().await;
            cancellation_reqs.remove(&export_id);
        }
        
        // Decrement in-progress counter
        self.telemetry.gis_exports_in_progress.dec();
        
        // Return result
        result
    }
    
    /// Request cancellation of an active export
    pub async fn cancel_export(&self, export_id: Uuid) -> Result<()> {
        // Check if export is active
        let is_active = {
            let active_exports = self.active_exports.read().await;
            active_exports.contains(&export_id)
        };
        
        if !is_active {
            return Err(Error::InvalidInput(format!(
                "Export {} is not active and cannot be cancelled",
                export_id
            )));
        }
        
        // Add to cancellation requests
        {
            let mut cancellation_reqs = self.cancellation_requests.write().await;
            cancellation_reqs.insert(export_id);
        }
        
        log::info!("Requested cancellation of export {}", export_id);
        
        Ok(())
    }
    
    /// Check if an export has been requested to be cancelled
    async fn is_export_cancelled(&self, export_id: Uuid) -> bool {
        let cancellation_reqs = self.cancellation_requests.read().await;
        cancellation_reqs.contains(&export_id)
    }
    
    /// Get county-specific configuration including available layers and export formats
    pub async fn get_county_configuration(&self, county_id: &str) -> Result<CountyConfiguration> {
        county_config::load_county_configuration(county_id).await
    }
    
    /// Get a list of layers available for a specific county
    pub async fn get_county_layers(&self, county_id: &str) -> Result<Vec<LayerDefinition>> {
        let config = county_config::load_county_configuration(county_id).await?;
        Ok(config.available_layers)
    }
    
    /// Generate a GeoJSON FeatureCollection from source data for a given layer
    fn generate_geojson(&self, layer_id: &str, county_id: &str) -> Result<FeatureCollection> {
        // In a real implementation, this would fetch data from a geodatabase or API
        // For this demo, we'll generate some example features
        
        let mut features = Vec::new();
        
        match layer_id {
            "parcels" => {
                // Generate some example parcel polygons
                for i in 1..5 {
                    // Create a simple polygon
                    let coords = vec![
                        vec![
                            vec![-74.0 + (i as f64) * 0.01, 40.7],
                            vec![-74.0 + (i as f64) * 0.01, 40.71],
                            vec![-73.99 + (i as f64) * 0.01, 40.71],
                            vec![-73.99 + (i as f64) * 0.01, 40.7],
                            vec![-74.0 + (i as f64) * 0.01, 40.7],
                        ]
                    ];
                    
                    let geometry = Geometry::new(geojson::Value::Polygon(coords));
                    
                    // Create properties
                    let mut properties = serde_json::Map::new();
                    properties.insert("parcel_id".to_string(), serde_json::Value::String(format!("P{:04}", i)));
                    properties.insert("address".to_string(), serde_json::Value::String(format!("{} Main St", i * 100)));
                    properties.insert("area_sqm".to_string(), serde_json::Value::Number((1000 * i).into()));
                    
                    // Create feature
                    let feature = Feature {
                        bbox: None,
                        geometry: Some(geometry),
                        id: None,
                        properties: Some(properties),
                        foreign_members: None,
                    };
                    
                    features.push(feature);
                }
            },
            "roads" => {
                // Generate some example road linestrings
                for i in 1..4 {
                    // Create a simple linestring
                    let coords = vec![
                        vec![-74.0, 40.7 + (i as f64) * 0.01],
                        vec![-73.95, 40.7 + (i as f64) * 0.01],
                    ];
                    
                    let geometry = Geometry::new(geojson::Value::LineString(coords));
                    
                    // Create properties
                    let mut properties = serde_json::Map::new();
                    properties.insert("road_id".to_string(), serde_json::Value::String(format!("R{:04}", i)));
                    properties.insert("name".to_string(), serde_json::Value::String(format!("{} Avenue", i)));
                    properties.insert("type".to_string(), serde_json::Value::String("residential".to_string()));
                    
                    // Create feature
                    let feature = Feature {
                        bbox: None,
                        geometry: Some(geometry),
                        id: None,
                        properties: Some(properties),
                        foreign_members: None,
                    };
                    
                    features.push(feature);
                }
            },
            _ => {
                return Err(Error::NotFound(format!("Layer not found: {}", layer_id)));
            }
        }
        
        // Create the feature collection
        let fc = FeatureCollection {
            bbox: None,
            features,
            foreign_members: None,
        };
        
        Ok(fc)
    }
    
    /// Convert GeoJSON to another format (Shapefile, KML, etc.)
    fn convert_format(&self, geojson: &FeatureCollection, format: &str) -> Result<Vec<u8>> {
        // In a real implementation, this would use a library like GDAL to convert formats
        // For this demo, we'll just return the GeoJSON as bytes
        
        match format {
            "geojson" => {
                let json_string = serde_json::to_string(geojson)?;
                Ok(json_string.into_bytes())
            },
            "shapefile" | "kml" => {
                // In a real implementation, we would convert to the requested format
                // For this demo, we'll just return a placeholder
                Ok(format!("This would be a {} file", format).into_bytes())
            },
            _ => {
                Err(Error::InvalidInput(format!("Unsupported format: {}", format)))
            }
        }
    }
}