use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;
use std::time::Instant;

/// Health check response model
#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub components: ComponentsStatus,
    pub version: String,
    pub uptime_seconds: u64,
}

/// Status of individual components
#[derive(Debug, Serialize, Deserialize)]
pub struct ComponentsStatus {
    pub api_gateway: String,
    pub database: String,
    pub sync_service: String,
    pub gis_export: String,
}

/// Status API response model
#[derive(Debug, Serialize, Deserialize)]
pub struct StatusResponse {
    pub status: String,
    pub api_version: String,
    pub components: Vec<ComponentStatus>,
    pub environment: String,
    pub uptime_seconds: u64,
}

/// Individual component status
#[derive(Debug, Serialize, Deserialize)]
pub struct ComponentStatus {
    pub name: String,
    pub status: String,
    pub version: Option<String>,
    pub last_check: String,
}

/// Health check endpoint
pub async fn health_check(state: web::Data<AppState>) -> impl Responder {
    // Check database connection
    let db_status = match state.database.get_connection() {
        Ok(_) => "up",
        Err(_) => "down",
    };
    
    // Check SyncService health
    let sync_service_status = match state.services.sync_service.health_check().await {
        Ok(true) => "up",
        Ok(false) => "degraded",
        Err(_) => "down",
    };
    
    // Check GIS Export service health
    let gis_export_status = match state.services.gis_export.health_check().await {
        Ok(true) => "up",
        Ok(false) => "degraded",
        Err(_) => "down",
    };
    
    // Determine overall status
    let status = if db_status == "up" && sync_service_status == "up" && gis_export_status == "up" {
        "healthy"
    } else if db_status == "down" || sync_service_status == "down" || gis_export_status == "down" {
        "unhealthy"
    } else {
        "degraded"
    };
    
    // Get uptime
    let uptime_seconds = state.telemetry.uptime_seconds();
    
    HttpResponse::Ok().json(HealthResponse {
        status: status.to_string(),
        components: ComponentsStatus {
            api_gateway: "up".to_string(),
            database: db_status.to_string(),
            sync_service: sync_service_status.to_string(),
            gis_export: gis_export_status.to_string(),
        },
        version: env!("CARGO_PKG_VERSION").to_string(),
        uptime_seconds,
    })
}

/// Status API endpoint with more detailed information
pub async fn status(state: web::Data<AppState>) -> impl Responder {
    // Check database connection
    let db_status = match state.database.get_connection() {
        Ok(_) => "up",
        Err(_) => "down",
    };
    
    // Check SyncService health
    let sync_service_status = match state.services.sync_service.health_check().await {
        Ok(true) => "up",
        Ok(false) => "degraded",
        Err(_) => "down",
    };
    
    // Check GIS Export service health
    let gis_export_status = match state.services.gis_export.health_check().await {
        Ok(true) => "up",
        Ok(false) => "degraded",
        Err(_) => "down",
    };
    
    // Determine overall status
    let status = if db_status == "up" && sync_service_status == "up" && gis_export_status == "up" {
        "healthy"
    } else if db_status == "down" || sync_service_status == "down" || gis_export_status == "down" {
        "unhealthy"
    } else {
        "degraded"
    };
    
    // Get current time for last check
    let current_time = chrono::Utc::now().to_rfc3339();
    
    // Get uptime
    let uptime_seconds = state.telemetry.uptime_seconds();
    
    // Create component status list
    let components = vec![
        ComponentStatus {
            name: "API Gateway".to_string(),
            status: "up".to_string(),
            version: Some(env!("CARGO_PKG_VERSION").to_string()),
            last_check: current_time.clone(),
        },
        ComponentStatus {
            name: "Database".to_string(),
            status: db_status.to_string(),
            version: None,
            last_check: current_time.clone(),
        },
        ComponentStatus {
            name: "Sync Service".to_string(),
            status: sync_service_status.to_string(),
            version: None,
            last_check: current_time.clone(),
        },
        ComponentStatus {
            name: "GIS Export Service".to_string(),
            status: gis_export_status.to_string(),
            version: None,
            last_check: current_time,
        },
    ];
    
    // Determine environment
    let environment = std::env::var("APP_ENV").unwrap_or_else(|_| "development".to_string());
    
    HttpResponse::Ok().json(StatusResponse {
        status: status.to_string(),
        api_version: env!("CARGO_PKG_VERSION").to_string(),
        components,
        environment,
        uptime_seconds,
    })
}