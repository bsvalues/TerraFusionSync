use actix_web::{web, HttpResponse, Responder, get, post, delete};
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use terrafusion_common::{Result, Error};
use terrafusion_common::models::geo::*;
use crate::AppState;

/// Configure GIS export routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(list_gis_exports)
       .service(create_gis_export)
       .service(get_gis_export)
       .service(cancel_gis_export)
       .service(download_gis_export)
       .service(get_export_formats);
}

/// List GIS exports with optional filtering
#[get("")]
async fn list_gis_exports(
    query: web::Query<GisExportQuery>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    log::info!("Listing GIS exports with filters: {:?}", query);
    
    // TODO: Implement database query with filters
    let exports = Vec::<GisExport>::new();
    
    Ok(web::Json(serde_json::json!({
        "exports": exports,
        "total": 0,
        "page": query.page.unwrap_or(1),
        "per_page": query.per_page.unwrap_or(20)
    })))
}

/// Create a new GIS export
#[post("")]
async fn create_gis_export(
    request: web::Json<CreateGisExportRequest>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    log::info!("Creating GIS export for county: {}", request.county_id);
    
    // Start the export using the export engine
    let export_id = app_state.export_engine.start_export(
        request.into_inner(),
        "api_user".to_string(), // TODO: Get from authentication context
    ).await?;
    
    log::info!("Created GIS export: {}", export_id);
    
    Ok(web::Json(serde_json::json!({
        "export_id": export_id,
        "status": "PENDING",
        "created_at": chrono::Utc::now()
    })))
}

/// Get a specific GIS export
#[get("/{export_id}")]
async fn get_gis_export(
    path: web::Path<Uuid>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    let export_id = path.into_inner();
    log::info!("Getting GIS export: {}", export_id);
    
    // Get export status from export engine
    let export_status = app_state.export_engine.get_export_status(export_id).await?;
    
    Ok(web::Json(serde_json::json!({
        "export": export_status
    })))
}

/// Cancel a running GIS export
#[delete("/{export_id}")]
async fn cancel_gis_export(
    path: web::Path<Uuid>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    let export_id = path.into_inner();
    log::info!("Canceling GIS export: {}", export_id);
    
    // Cancel the export using the export engine
    app_state.export_engine.cancel_export(export_id).await?;
    
    Ok(web::Json(serde_json::json!({
        "export_id": export_id,
        "status": "CANCELED",
        "message": "Export canceled successfully"
    })))
}

/// Download a completed GIS export
#[get("/{export_id}/download")]
async fn download_gis_export(
    path: web::Path<Uuid>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    let export_id = path.into_inner();
    log::info!("Downloading GIS export: {}", export_id);
    
    // Get export status to check if it's completed
    let export_status = app_state.export_engine.get_export_status(export_id).await?;
    
    if export_status.status != GisExportStatus::Completed {
        return Err(Error::Validation("Export is not completed yet".to_string()));
    }
    
    let result_url = export_status.result_url
        .ok_or_else(|| Error::NotFound("Export file not found".to_string()))?;
    
    // Return redirect to the actual file
    Ok(HttpResponse::Found()
        .append_header(("Location", result_url))
        .finish())
}

/// Get supported export formats
#[get("/formats")]
async fn get_export_formats() -> Result<impl Responder> {
    let formats = vec![
        serde_json::json!({
            "format": "SHAPEFILE",
            "name": "Shapefile",
            "description": "ESRI Shapefile format with multiple component files",
            "file_extension": "zip",
            "mime_type": "application/zip"
        }),
        serde_json::json!({
            "format": "GEOJSON",
            "name": "GeoJSON",
            "description": "Geographic JSON format",
            "file_extension": "geojson",
            "mime_type": "application/geo+json"
        }),
        serde_json::json!({
            "format": "KML",
            "name": "KML",
            "description": "Keyhole Markup Language",
            "file_extension": "kml",
            "mime_type": "application/vnd.google-earth.kml+xml"
        }),
        serde_json::json!({
            "format": "CSV",
            "name": "CSV",
            "description": "Comma-separated values with WKT geometry",
            "file_extension": "csv",
            "mime_type": "text/csv"
        }),
        serde_json::json!({
            "format": "GPKG",
            "name": "GeoPackage",
            "description": "OGC GeoPackage format",
            "file_extension": "gpkg",
            "mime_type": "application/geopackage+sqlite3"
        }),
    ];
    
    Ok(web::Json(serde_json::json!({
        "formats": formats
    })))
}

/// Query parameters for listing GIS exports
#[derive(Debug, Deserialize)]
pub struct GisExportQuery {
    pub county_id: Option<String>,
    pub status: Option<String>,
    pub export_format: Option<String>,
    pub from_date: Option<chrono::DateTime<chrono::Utc>>,
    pub to_date: Option<chrono::DateTime<chrono::Utc>>,
    pub page: Option<usize>,
    pub per_page: Option<usize>,
}