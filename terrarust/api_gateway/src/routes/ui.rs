use actix_web::{web, HttpRequest, HttpResponse, Result};
use serde_json::json;
use crate::AppState;

/// Configure UI routes
pub fn configure() -> actix_web::Scope {
    web::scope("")
        .route("/", web::get().to(dashboard))
        .route("/dashboard", web::get().to(dashboard))
        .route("/gis/dashboard", web::get().to(gis_dashboard))
        .route("/district-lookup", web::get().to(district_lookup_dashboard))
        .route("/sync/dashboard", web::get().to(sync_dashboard))
}

/// Main dashboard view
async fn dashboard(data: web::Data<AppState>) -> Result<HttpResponse> {
    let template_data = json!({
        "title": "TerraFusion Platform",
        "service": "Rust Gateway",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    });

    let body = data.handlebars
        .render("dashboard", &template_data)
        .map_err(|e| {
            log::error!("Template rendering error: {}", e);
            actix_web::error::ErrorInternalServerError("Template rendering failed")
        })?;

    Ok(HttpResponse::Ok().content_type("text/html").body(body))
}

/// GIS Export dashboard
async fn gis_dashboard(data: web::Data<AppState>) -> Result<HttpResponse> {
    let template_data = json!({
        "title": "GIS Export Dashboard",
        "service": "TerraFusion GIS Export",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    });

    let body = data.handlebars
        .render("gis_export_dashboard", &template_data)
        .map_err(|e| {
            log::error!("Template rendering error: {}", e);
            actix_web::error::ErrorInternalServerError("Template rendering failed")
        })?;

    Ok(HttpResponse::Ok().content_type("text/html").body(body))
}

/// District lookup dashboard
async fn district_lookup_dashboard(data: web::Data<AppState>) -> Result<HttpResponse> {
    let template_data = json!({
        "title": "District Lookup",
        "service": "Benton County District Lookup",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    });

    let body = data.handlebars
        .render("index", &template_data)
        .map_err(|e| {
            log::error!("Template rendering error: {}", e);
            actix_web::error::ErrorInternalServerError("Template rendering failed")
        })?;

    Ok(HttpResponse::Ok().content_type("text/html").body(body))
}

/// Sync dashboard
async fn sync_dashboard(data: web::Data<AppState>) -> Result<HttpResponse> {
    let template_data = json!({
        "title": "Data Synchronization",
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    });

    let body = data.handlebars
        .render("sync_dashboard", &template_data)
        .map_err(|e| {
            log::error!("Template rendering error: {}", e);
            actix_web::error::ErrorInternalServerError("Template rendering failed")
        })?;

    Ok(HttpResponse::Ok().content_type("text/html").body(body))
}