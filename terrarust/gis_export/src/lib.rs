use actix_web::{web, App, HttpServer, HttpResponse, Result, middleware::Logger};
use serde::{Deserialize, Serialize};
use sqlx::{PgPool, Row};
use std::collections::HashMap;
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::path::PathBuf;
use tokio::fs;

pub mod models;
pub mod service;
pub mod handlers;
pub mod formats;

pub use service::GisExportService;
pub use models::*;

/// Supported export formats
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum ExportFormat {
    Shapefile,
    Geojson,
    Kml,
    Geopackage,
    Csv,
}

impl ExportFormat {
    pub fn as_str(&self) -> &'static str {
        match self {
            ExportFormat::Shapefile => "shapefile",
            ExportFormat::Geojson => "geojson", 
            ExportFormat::Kml => "kml",
            ExportFormat::Geopackage => "geopackage",
            ExportFormat::Csv => "csv",
        }
    }

    pub fn file_extension(&self) -> &'static str {
        match self {
            ExportFormat::Shapefile => "zip", // Shapefiles delivered as ZIP
            ExportFormat::Geojson => "geojson",
            ExportFormat::Kml => "kml", 
            ExportFormat::Geopackage => "gpkg",
            ExportFormat::Csv => "csv",
        }
    }
}

impl std::str::FromStr for ExportFormat {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "shapefile" => Ok(ExportFormat::Shapefile),
            "geojson" => Ok(ExportFormat::Geojson),
            "kml" => Ok(ExportFormat::Kml),
            "geopackage" => Ok(ExportFormat::Geopackage),
            "csv" => Ok(ExportFormat::Csv),
            _ => Err(format!("Unsupported export format: {}", s))
        }
    }
}

/// Configuration for the GIS Export service
#[derive(Debug, Clone)]
pub struct GisExportConfig {
    pub storage_path: PathBuf,
    pub database_url: String,
    pub max_concurrent_jobs: usize,
    pub job_timeout_seconds: u64,
}

impl Default for GisExportConfig {
    fn default() -> Self {
        Self {
            storage_path: PathBuf::from("exports"),
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgresql://localhost/terrafusion".to_string()),
            max_concurrent_jobs: 10,
            job_timeout_seconds: 3600, // 1 hour
        }
    }
}

/// Initialize the GIS Export service with configuration
pub async fn init_service(config: GisExportConfig) -> Result<GisExportService, Box<dyn std::error::Error>> {
    // Create storage directory
    fs::create_dir_all(&config.storage_path).await?;
    
    // Initialize database connection pool
    let pool = PgPool::connect(&config.database_url).await?;
    
    // Create service instance
    let service = GisExportService::new(config, pool).await?;
    
    log::info!("GIS Export service initialized successfully");
    Ok(service)
}

/// Health check for the GIS Export service
pub async fn health_check() -> Result<HttpResponse, actix_web::Error> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "service": "TerraFusion GIS Export (Rust)",
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": Utc::now().to_rfc3339(),
        "supported_formats": [
            "shapefile",
            "geojson", 
            "kml",
            "geopackage",
            "csv"
        ]
    })))
}