use actix_web::{web, HttpResponse, Responder, http::header};
use common::error::Error;
use common::models::gis_export::{CountyConfiguration, GisExport, NewGisExport};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct GisExportResponse {
    pub export: GisExport,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GisExportsResponse {
    pub exports: Vec<GisExport>,
    pub total_count: i64,
}

#[derive(Debug, Deserialize)]
pub struct GisExportQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
    pub county_id: Option<String>,
    pub export_format: Option<String>,
    pub status: Option<String>,
    pub created_by: Option<String>,
    pub from_date: Option<String>,
    pub to_date: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateExportRequest {
    pub county_id: String,
    pub export_format: String,
    pub area_of_interest: Option<serde_json::Value>,
    pub layers: Vec<String>,
    pub parameters: serde_json::Value,
}

pub async fn get_exports(
    query: web::Query<GisExportQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Implementation will call the GIS Export microservice
    // For now, return a stub response
    HttpResponse::Ok().json(GisExportsResponse {
        exports: Vec::new(),
        total_count: 0,
    })
}

pub async fn create_export(
    new_export: web::Json<CreateExportRequest>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would:
    // 1. Validate the export request against county configuration
    // 2. Create a new export job
    // 3. Return the export details
    
    // For now, return a stub response
    let layers_json = serde_json::to_value(&new_export.layers).unwrap_or(serde_json::Value::Array(vec![]));
    
    HttpResponse::Created().json(GisExportResponse {
        export: GisExport {
            id: Uuid::new_v4(),
            county_id: new_export.county_id.clone(),
            export_format: new_export.export_format.clone(),
            status: "pending".to_string(),
            area_of_interest: new_export.area_of_interest.clone(),
            layers: layers_json,
            parameters: new_export.parameters.clone(),
            result_url: None,
            started_at: None,
            completed_at: None,
            error_message: None,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            created_by: "system".to_string(), // In real impl, this would come from auth
        },
    })
}

pub async fn get_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Implementation will call the GIS Export microservice
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": "GIS export not found",
            "status": 404
        })
    ))
}

pub async fn cancel_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Implementation will call the GIS Export microservice
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": "GIS export not found",
            "status": 404
        })
    ))
}

pub async fn download_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Implementation will call the GIS Export microservice
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": "GIS export not found",
            "status": 404
        })
    ))
}

pub async fn get_county_config(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would fetch county configuration from the database
    // For now, return a stub response with example data
    
    // Use the utility function from common
    match common::utils::county_config::load_county_configuration(&county_id).await {
        Ok(config) => HttpResponse::Ok().json(config),
        Err(e) => HttpResponse::InternalServerError().json(web::Json(
            serde_json::json!({
                "error": format!("Failed to load county configuration: {}", e),
                "status": 500
            })
        )),
    }
}

pub async fn get_county_layers(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would fetch county layers from the database
    // For now, load the county config and extract layers
    match common::utils::county_config::load_county_configuration(&county_id).await {
        Ok(config) => HttpResponse::Ok().json(web::Json(config.available_layers)),
        Err(e) => HttpResponse::InternalServerError().json(web::Json(
            serde_json::json!({
                "error": format!("Failed to load county layers: {}", e),
                "status": 500
            })
        )),
    }
}