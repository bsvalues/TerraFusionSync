use actix_web::{web, HttpResponse, Result};
use serde_json::json;
use crate::AppState;

/// Configure system routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/health")
            .route(web::get().to(health_check))
    )
    .service(
        web::resource("/metrics")
            .route(web::get().to(metrics))
    )
    .service(
        web::resource("/status")
            .route(web::get().to(status))
    );
}

/// Health check endpoint
async fn health_check() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(json!({
        "status": "healthy",
        "service": "TerraFusion Rust Gateway",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    })))
}

/// Metrics endpoint for monitoring
async fn metrics(data: web::Data<AppState>) -> Result<HttpResponse> {
    let uptime = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    Ok(HttpResponse::Ok().json(json!({
        "service": "TerraFusion Rust Gateway",
        "version": "0.1.0",
        "uptime_seconds": uptime,
        "environment": data.config.environment,
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "system": {
            "rust_version": env!("CARGO_PKG_RUST_VERSION"),
            "target": env!("TARGET"),
            "workers": data.config.worker_threads
        }
    })))
}

/// Overall system status
async fn status(data: web::Data<AppState>) -> Result<HttpResponse> {
    // Check connectivity to Python services
    let sync_status = check_service_health(&data.config.sync_service_url).await;
    let gis_status = check_service_health(&data.config.gis_export_service_url).await;

    Ok(HttpResponse::Ok().json(json!({
        "gateway": "healthy",
        "services": {
            "sync_service": sync_status,
            "gis_export": gis_status
        },
        "timestamp": chrono::Utc::now().to_rfc3339()
    })))
}

/// Helper function to check service health
async fn check_service_health(url: &str) -> &'static str {
    match reqwest::get(&format!("{}/health", url)).await {
        Ok(response) if response.status().is_success() => "healthy",
        _ => "unavailable"
    }
}