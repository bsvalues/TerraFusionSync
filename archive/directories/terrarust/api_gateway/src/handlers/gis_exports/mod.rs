use actix_web::{web, HttpResponse, Responder, http::header};
use common::error::{Error, Result};
use common::models::gis_export::GisExport;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::middleware::auth::Claims;
use crate::services::gis_export::CreateExportRequest;

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
    pub from_date: Option<String>,
    pub to_date: Option<String>,
}

/// Get all GIS exports with optional filtering
pub async fn get_all_exports(
    query: web::Query<GisExportQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Get query parameters
    let county_id = query.county_id.as_deref();
    let export_format = query.export_format.as_deref();
    let status = query.status.as_deref();
    let page = query.page;
    let per_page = query.per_page;
    
    // Call the service
    match state.services.gis_export.get_exports(
        county_id,
        export_format,
        status,
        page,
        per_page,
    ).await {
        Ok((exports, total_count)) => {
            HttpResponse::Ok().json(GisExportsResponse {
                exports,
                total_count,
            })
        },
        Err(e) => {
            log::error!("Failed to get GIS exports: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to get GIS exports: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

/// Create a new GIS export
pub async fn create_export(
    req: web::Json<CreateExportRequest>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Create the request with username from claims
    let mut request = req.into_inner();
    
    // Call the service
    match state.services.gis_export.create_export(request).await {
        Ok(export) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "GIS export {} created by user {} for county {}",
                export.id,
                claims.sub,
                export.county_id
            );
            
            HttpResponse::Created().json(GisExportResponse {
                export,
            })
        },
        Err(e) => {
            log::error!("Failed to create GIS export: {}", e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to create GIS export: {}", e),
                    "status": 400
                })
            ))
        }
    }
}

/// Get a specific GIS export by ID
pub async fn get_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.gis_export.get_export(*id).await {
        Ok(export) => {
            HttpResponse::Ok().json(GisExportResponse {
                export,
            })
        },
        Err(e) => {
            log::error!("Failed to get GIS export {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get GIS export: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Cancel a GIS export
pub async fn cancel_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Call the service
    match state.services.gis_export.cancel_export(*id).await {
        Ok(_) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "GIS export {} canceled by user {}",
                id,
                claims.sub
            );
            
            HttpResponse::Ok().json(web::Json(
                serde_json::json!({
                    "message": "Export canceled successfully",
                    "status": 200
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to cancel GIS export {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to cancel GIS export: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Download a GIS export
pub async fn download_export(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.gis_export.download_export(*id).await {
        Ok(data) => {
            // Get the export to determine the format
            match state.services.gis_export.get_export(*id).await {
                Ok(export) => {
                    // Determine content type and filename based on format
                    let (content_type, extension) = match export.export_format.as_str() {
                        "geojson" => ("application/json", "geojson"),
                        "shapefile" => ("application/zip", "zip"),
                        "kml" => ("application/vnd.google-earth.kml+xml", "kml"),
                        _ => ("application/octet-stream", "bin"),
                    };
                    
                    let filename = format!("export_{}.{}", id, extension);
                    
                    // Return the file
                    HttpResponse::Ok()
                        .content_type(content_type)
                        .append_header((
                            header::CONTENT_DISPOSITION, 
                            format!("attachment; filename=\"{}\"", filename)
                        ))
                        .body(data)
                },
                Err(e) => {
                    log::error!("Failed to get GIS export metadata {}: {}", id, e);
                    HttpResponse::Ok()
                        .content_type("application/octet-stream")
                        .append_header((
                            header::CONTENT_DISPOSITION, 
                            format!("attachment; filename=\"export_{}.bin\"", id)
                        ))
                        .body(data)
                }
            }
        },
        Err(e) => {
            log::error!("Failed to download GIS export {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to download GIS export: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}