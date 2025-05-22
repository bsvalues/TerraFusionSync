use actix_web::{web, HttpResponse, Responder, http::header};
use common::error::{Error, Result};
use common::models::gis_export::GisExport;
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
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::Ok().json(GisExportsResponse {
        exports: Vec::new(),
        total_count: 0,
    })
}

pub async fn create_export(
    req: web::Json<CreateExportRequest>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Create the export using the export service
    match state.export_service.create_export(
        req.county_id.clone(),
        req.export_format.clone(),
        req.area_of_interest.clone(),
        req.layers.clone(),
        req.parameters.clone(),
        "system".to_string(), // In a real implementation, this would come from the authenticated user
    ).await {
        Ok(export) => {
            // In a real implementation, we would save this to the database
            
            // Start the export process in the background
            let export_id = export.id;
            let export_service = state.export_service.clone();
            
            tokio::spawn(async move {
                match export_service.execute_export(export_id).await {
                    Ok(result_url) => {
                        log::info!("Export {} completed successfully: {}", export_id, result_url);
                        // In a real implementation, we would update the export record in the database
                    },
                    Err(e) => {
                        log::error!("Export {} failed: {}", export_id, e);
                        // In a real implementation, we would update the export record in the database
                    }
                }
            });
            
            HttpResponse::Created().json(GisExportResponse {
                export,
            })
        },
        Err(e) => {
            log::error!("Failed to create export: {}", e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to create export: {}", e),
                    "status": 400
                })
            ))
        }
    }
}

pub async fn get_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": format!("Export not found: {}", id),
            "status": 404
        })
    ))
}

pub async fn cancel_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Try to cancel the export
    match state.export_service.cancel_export(*id).await {
        Ok(_) => {
            log::info!("Export {} cancelled", id);
            HttpResponse::Ok().json(web::Json(
                serde_json::json!({
                    "message": "Export cancelled successfully",
                    "status": 200
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to cancel export {}: {}", id, e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to cancel export: {}", e),
                    "status": 400
                })
            ))
        }
    }
}

pub async fn download_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would fetch the export result from storage
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": format!("Export not found: {}", id),
            "status": 404
        })
    ))
}