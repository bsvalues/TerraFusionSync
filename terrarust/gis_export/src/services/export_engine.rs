use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::{RwLock, Semaphore};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use terrafusion_common::{Result, Error, database::DbPool};
use terrafusion_common::models::geo::*;
use crate::config::Config;
use super::format_handlers::FormatHandler;
use super::file_manager::FileManager;

/// Core GIS export engine for TerraFusion platform
#[derive(Clone)]
pub struct ExportEngine {
    db_pool: DbPool,
    config: Config,
    running_exports: Arc<RwLock<HashMap<Uuid, ExportJobHandle>>>,
    semaphore: Arc<Semaphore>,
    format_handlers: Arc<HashMap<GisExportFormat, Box<dyn FormatHandler>>>,
    file_manager: Arc<FileManager>,
}

/// Handle for a running export job
#[derive(Debug)]
pub struct ExportJobHandle {
    pub export_id: Uuid,
    pub county_id: String,
    pub export_format: GisExportFormat,
    pub status: GisExportStatus,
    pub start_time: DateTime<Utc>,
    pub progress_percent: u32,
}

impl ExportEngine {
    /// Create a new export engine
    pub fn new(db_pool: DbPool, config: &Config) -> Self {
        let max_concurrent = std::env::var("MAX_CONCURRENT_EXPORTS")
            .unwrap_or_else(|_| "3".to_string())
            .parse::<usize>()
            .unwrap_or(3);
        
        // Create file manager
        let file_manager = Arc::new(FileManager::new(config.clone()));
        
        // Initialize format handlers
        let mut format_handlers: HashMap<GisExportFormat, Box<dyn FormatHandler>> = HashMap::new();
        format_handlers.insert(GisExportFormat::Shapefile, Box::new(format_handlers::ShapefileHandler::new()));
        format_handlers.insert(GisExportFormat::GeoJson, Box::new(format_handlers::GeoJsonHandler::new()));
        format_handlers.insert(GisExportFormat::Kml, Box::new(format_handlers::KmlHandler::new()));
        format_handlers.insert(GisExportFormat::Csv, Box::new(format_handlers::CsvHandler::new()));
        format_handlers.insert(GisExportFormat::Gpkg, Box::new(format_handlers::GpkgHandler::new()));
        
        Self {
            db_pool,
            config: config.clone(),
            running_exports: Arc::new(RwLock::new(HashMap::new())),
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
            format_handlers: Arc::new(format_handlers),
            file_manager,
        }
    }
    
    /// Start a GIS export operation
    pub async fn start_export(
        &self,
        request: CreateGisExportRequest,
        created_by: String,
    ) -> Result<Uuid> {
        // Acquire semaphore permit to limit concurrent operations
        let _permit = self.semaphore.acquire().await
            .map_err(|_| Error::Internal("Failed to acquire export semaphore".to_string()))?;
        
        // Validate the request
        self.validate_export_request(&request).await?;
        
        // Create new export record
        let export_id = Uuid::new_v4();
        let export = GisExport {
            base: terrafusion_common::models::BaseModel {
                id: export_id,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            },
            county_id: request.county_id.clone(),
            export_format: request.export_format,
            status: GisExportStatus::Pending,
            layers: request.layers.clone(),
            area_of_interest: request.area_of_interest.clone(),
            parameters: request.parameters.clone(),
            created_by,
            started_at: None,
            completed_at: None,
            result_url: None,
            error_message: None,
            file_size_bytes: None,
        };
        
        // Save export to database
        self.create_gis_export(&export).await?;
        
        // Create export handle
        let handle = ExportJobHandle {
            export_id,
            county_id: request.county_id.clone(),
            export_format: request.export_format,
            status: GisExportStatus::Running,
            start_time: Utc::now(),
            progress_percent: 0,
        };
        
        // Add to running exports
        {
            let mut running = self.running_exports.write().await;
            running.insert(export_id, handle);
        }
        
        // Start the export process in background
        let engine = self.clone();
        tokio::spawn(async move {
            let result = engine.execute_export(export_id, request).await;
            
            // Update export status based on result
            match result {
                Ok(result_info) => {
                    let _ = engine.complete_export(export_id, result_info).await;
                }
                Err(e) => {
                    let _ = engine.fail_export(export_id, e.to_string()).await;
                }
            }
            
            // Remove from running exports
            {
                let mut running = engine.running_exports.write().await;
                running.remove(&export_id);
            }
        });
        
        Ok(export_id)
    }
    
    /// Execute the actual export operation
    async fn execute_export(
        &self,
        export_id: Uuid,
        request: CreateGisExportRequest,
    ) -> Result<ExportResult> {
        log::info!("Starting GIS export {} for county {}", export_id, request.county_id);
        
        // Update status to running
        self.update_export_status(export_id, GisExportStatus::Running).await?;
        self.update_export_progress(export_id, 10).await;
        
        // Get county configuration
        let county_config = self.get_county_config(&request.county_id).await?;
        self.update_export_progress(export_id, 20).await;
        
        // Validate format is supported by county
        if !county_config.supported_formats.contains(&request.export_format) {
            return Err(Error::Validation(format!(
                "Export format {:?} not supported by county {}",
                request.export_format, request.county_id
            )));
        }
        
        // Extract layer data
        log::info!("Extracting data for {} layers", request.layers.len());
        let layer_data = self.extract_layer_data(&request.layers, &request.county_id, &request.area_of_interest).await?;
        self.update_export_progress(export_id, 60).await;
        
        // Get format handler
        let format_handler = self.format_handlers.get(&request.export_format)
            .ok_or_else(|| Error::Internal(format!("No handler for format: {:?}", request.export_format)))?;
        
        // Generate export file
        log::info!("Generating export file in format: {:?}", request.export_format);
        let export_path = self.file_manager.generate_export_path(export_id, request.export_format)?;
        
        format_handler.generate_export(
            &layer_data,
            &export_path,
            &request.parameters,
            &county_config,
        ).await?;
        
        self.update_export_progress(export_id, 90).await;
        
        // Get file size
        let file_size = std::fs::metadata(&export_path)
            .map_err(|e| Error::Internal(format!("Failed to get file size: {}", e)))?
            .len();
        
        // Generate download URL
        let result_url = self.file_manager.generate_download_url(export_id, request.export_format)?;
        
        self.update_export_progress(export_id, 100).await;
        
        log::info!("GIS export {} completed successfully, file size: {} bytes", export_id, file_size);
        
        Ok(ExportResult {
            result_url,
            file_size_bytes: file_size,
        })
    }
    
    /// Cancel a running export
    pub async fn cancel_export(&self, export_id: Uuid) -> Result<()> {
        // Check if export is running
        {
            let running = self.running_exports.read().await;
            if !running.contains_key(&export_id) {
                return Err(Error::NotFound("Export not found or not running".to_string()));
            }
        }
        
        // Update status to canceled
        self.update_export_status(export_id, GisExportStatus::Canceled).await?;
        
        // Clean up any temporary files
        let _ = self.file_manager.cleanup_export_files(export_id).await;
        
        // Remove from running exports
        {
            let mut running = self.running_exports.write().await;
            running.remove(&export_id);
        }
        
        log::info!("GIS export {} canceled", export_id);
        
        Ok(())
    }
    
    /// Get status of an export
    pub async fn get_export_status(&self, export_id: Uuid) -> Result<GisExportStatusResponse> {
        let running = self.running_exports.read().await;
        
        if let Some(handle) = running.get(&export_id) {
            Ok(GisExportStatusResponse {
                id: handle.export_id,
                status: handle.status,
                progress_percent: Some(handle.progress_percent as i32),
                message: None,
                started_at: Some(handle.start_time),
                completed_at: None,
                result_url: None,
                error_message: None,
            })
        } else {
            // Check database for completed exports
            self.get_export_from_db(export_id).await
        }
    }
    
    /// Validate export request
    async fn validate_export_request(&self, request: &CreateGisExportRequest) -> Result<()> {
        if request.layers.is_empty() {
            return Err(Error::Validation("At least one layer must be specified".to_string()));
        }
        
        // Validate area of interest if provided
        if let Some(aoi) = &request.area_of_interest {
            // Basic GeoJSON validation
            if !aoi.is_object() {
                return Err(Error::Validation("Area of interest must be a valid GeoJSON geometry".to_string()));
            }
        }
        
        Ok(())
    }
    
    /// Extract data for the specified layers
    async fn extract_layer_data(
        &self,
        layers: &[String],
        county_id: &str,
        area_of_interest: &Option<serde_json::Value>,
    ) -> Result<Vec<LayerData>> {
        let mut layer_data = Vec::new();
        
        for layer_id in layers {
            log::debug!("Extracting data for layer: {}", layer_id);
            
            // Get layer configuration
            let layer_config = self.get_layer_config(layer_id, county_id).await?;
            
            // Extract features from the data source
            let features = self.extract_layer_features(&layer_config, area_of_interest).await?;
            
            layer_data.push(LayerData {
                layer_config,
                features,
            });
        }
        
        Ok(layer_data)
    }
    
    /// Extract features for a specific layer
    async fn extract_layer_features(
        &self,
        layer_config: &GisLayer,
        area_of_interest: &Option<serde_json::Value>,
    ) -> Result<Vec<Feature>> {
        // This would implement the actual data extraction logic
        // For now, return empty features
        log::debug!("Extracting features for layer: {}", layer_config.name);
        Ok(Vec::new())
    }
    
    // Database helper methods
    async fn create_gis_export(&self, export: &GisExport) -> Result<()> {
        // Implement database insert for GIS export
        Ok(())
    }
    
    async fn update_export_status(&self, export_id: Uuid, status: GisExportStatus) -> Result<()> {
        // Implement database update for export status
        Ok(())
    }
    
    async fn update_export_progress(&self, export_id: Uuid, progress: u32) {
        let mut running = self.running_exports.write().await;
        if let Some(handle) = running.get_mut(&export_id) {
            handle.progress_percent = progress;
        }
    }
    
    async fn complete_export(&self, export_id: Uuid, result: ExportResult) -> Result<()> {
        // Implement database update for completed export
        Ok(())
    }
    
    async fn fail_export(&self, export_id: Uuid, error: String) -> Result<()> {
        // Implement database update for failed export
        Ok(())
    }
    
    async fn get_export_from_db(&self, export_id: Uuid) -> Result<GisExportStatusResponse> {
        // Implement database query for export
        Err(Error::NotFound("Export not found".to_string()))
    }
    
    async fn get_county_config(&self, county_id: &str) -> Result<CountyGisConfig> {
        // Implement database query for county configuration
        // For now, return a default configuration
        Ok(CountyGisConfig {
            county_id: county_id.to_string(),
            name: format!("County {}", county_id),
            supported_formats: vec![
                GisExportFormat::Shapefile,
                GisExportFormat::GeoJson,
                GisExportFormat::Kml,
                GisExportFormat::Csv,
            ],
            default_projection: "EPSG:4326".to_string(),
            available_projections: vec!["EPSG:4326".to_string(), "EPSG:3857".to_string()],
            max_export_area_sq_km: Some(1000.0),
            max_export_features: Some(10000),
            default_parameters: serde_json::json!({}),
        })
    }
    
    async fn get_layer_config(&self, layer_id: &str, county_id: &str) -> Result<GisLayer> {
        // Implement database query for layer configuration
        // For now, return a default layer
        Ok(GisLayer {
            id: layer_id.to_string(),
            name: format!("Layer {}", layer_id),
            description: format!("Description for layer {}", layer_id),
            geometry_type: GeometryType::Polygon,
            attributes: Vec::new(),
            is_enabled: true,
            county_id: county_id.to_string(),
            source_table: Some(format!("table_{}", layer_id)),
            source_query: None,
            style: None,
        })
    }
}

/// Result of a successful export
#[derive(Debug)]
pub struct ExportResult {
    pub result_url: String,
    pub file_size_bytes: u64,
}

/// Layer data extracted for export
#[derive(Debug)]
pub struct LayerData {
    pub layer_config: GisLayer,
    pub features: Vec<Feature>,
}

/// GeoJSON Feature for export
#[derive(Debug)]
pub struct Feature {
    pub geometry: serde_json::Value,
    pub properties: serde_json::Value,
}