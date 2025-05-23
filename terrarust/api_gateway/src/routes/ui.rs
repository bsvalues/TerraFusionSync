use actix_web::{web, HttpResponse, Responder, HttpRequest, get};
use handlebars::Handlebars;
use serde_json::json;
use std::sync::Arc;
use crate::errors::{AppError, AppResult};
use crate::handlers;

/// Configure UI routes
pub fn configure() -> actix_web::Resource {
    web::resource("/")
        .route(web::get().to(index))
}

/// Index/home page handler
#[get("/")]
async fn index(
    hb: web::Data<Arc<Handlebars<'_>>>,
    req: HttpRequest,
) -> AppResult<HttpResponse> {
    // Render the index template
    let data = json!({
        "title": "TerraFusion Platform - Home",
        "user": null,  // User will be provided by auth middleware if authenticated
    });
    
    let body = hb.render("index", &data)
        .map_err(AppError::from)?;
    
    Ok(HttpResponse::Ok().body(body))
}

/// Dashboard page handler
#[get("/dashboard")]
async fn dashboard(
    hb: web::Data<Arc<Handlebars<'_>>>,
    req: HttpRequest,
) -> AppResult<HttpResponse> {
    // Ensure user is authenticated
    // TODO: Get user from auth middleware extensions

    // Fetch dashboard data
    let dashboard_data = handlers::ui::get_dashboard_data().await?;
    
    // Render the dashboard template
    let data = json!({
        "title": "TerraFusion Platform - Dashboard",
        "sync_operations_count": dashboard_data.sync_operations_count,
        "active_sync_pairs": dashboard_data.active_sync_pairs,
        "recent_exports": dashboard_data.recent_exports,
        "pending_exports": dashboard_data.pending_exports,
        "user": dashboard_data.user,
    });
    
    let body = hb.render("dashboard", &data)
        .map_err(AppError::from)?;
    
    Ok(HttpResponse::Ok().body(body))
}

/// Sync dashboard page handler
#[get("/sync-dashboard")]
async fn sync_dashboard(
    hb: web::Data<Arc<Handlebars<'_>>>,
    req: HttpRequest,
) -> AppResult<HttpResponse> {
    // Fetch sync pairs and recent operations
    let sync_dashboard_data = handlers::ui::get_sync_dashboard_data().await?;
    
    // Render the sync dashboard template
    let data = json!({
        "title": "TerraFusion Platform - Sync Dashboard",
        "sync_pairs": sync_dashboard_data.sync_pairs,
        "recent_operations": sync_dashboard_data.recent_operations,
        "county_id": sync_dashboard_data.county_id,
        "user": sync_dashboard_data.user,
    });
    
    let body = hb.render("sync_dashboard", &data)
        .map_err(AppError::from)?;
    
    Ok(HttpResponse::Ok().body(body))
}

/// GIS Export dashboard page handler
#[get("/gis-export")]
async fn gis_export_dashboard(
    hb: web::Data<Arc<Handlebars<'_>>>,
    req: HttpRequest,
) -> AppResult<HttpResponse> {
    // Fetch export jobs and available formats/layers
    let export_dashboard_data = handlers::ui::get_gis_export_dashboard_data().await?;
    
    // Render the GIS export dashboard template
    let data = json!({
        "title": "TerraFusion Platform - GIS Export",
        "exports": export_dashboard_data.exports,
        "available_counties": export_dashboard_data.available_counties,
        "available_formats": export_dashboard_data.available_formats,
        "user": export_dashboard_data.user,
    });
    
    let body = hb.render("gis_export_dashboard", &data)
        .map_err(AppError::from)?;
    
    Ok(HttpResponse::Ok().body(body))
}

/// Login page handler
#[get("/login")]
async fn login(
    hb: web::Data<Arc<Handlebars<'_>>>,
    req: HttpRequest,
) -> AppResult<HttpResponse> {
    // Render the login template
    let data = json!({
        "title": "TerraFusion Platform - Login",
        "redirect_to": req.query_string(),
    });
    
    let body = hb.render("login", &data)
        .map_err(AppError::from)?;
    
    Ok(HttpResponse::Ok().body(body))
}

/// Configure all UI routes
pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(index)
       .service(dashboard)
       .service(sync_dashboard)
       .service(gis_export_dashboard)
       .service(login);
}