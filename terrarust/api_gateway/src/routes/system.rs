use actix_web::{web, HttpResponse, Responder, get};
use crate::errors::{AppError, AppResult};
use crate::handlers;
use serde_json::json;

/// Configure system routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(health)
       .service(metrics)
       .service(liveness)
       .service(readiness);
}

/// Health check endpoint
#[get("/health")]
async fn health() -> AppResult<impl Responder> {
    let health_status = handlers::system::check_health().await?;
    
    Ok(web::Json(json!({
        "status": health_status.status,
        "version": health_status.version,
        "services": health_status.services,
        "timestamp": health_status.timestamp,
    })))
}

/// Metrics endpoint
#[get("/metrics")]
async fn metrics() -> AppResult<impl Responder> {
    let metrics_data = handlers::system::get_metrics().await?;
    
    // For Prometheus format, return plain text
    if metrics_data.format == "prometheus" {
        return Ok(HttpResponse::Ok()
            .content_type("text/plain")
            .body(metrics_data.prometheus_data));
    }
    
    // For JSON format, return JSON
    Ok(web::Json(json!({
        "metrics": metrics_data.metrics,
        "timestamp": metrics_data.timestamp,
    })))
}

/// Kubernetes liveness probe endpoint
#[get("/liveness")]
async fn liveness() -> AppResult<impl Responder> {
    // Simple check if the service is running
    Ok(web::Json(json!({
        "status": "UP",
        "timestamp": chrono::Utc::now().to_rfc3339(),
    })))
}

/// Kubernetes readiness probe endpoint
#[get("/readiness")]
async fn readiness() -> AppResult<impl Responder> {
    // Check if the service is ready to handle requests
    let readiness_status = handlers::system::check_readiness().await?;
    
    if readiness_status.is_ready {
        Ok(web::Json(json!({
            "status": "READY",
            "checks": readiness_status.checks,
            "timestamp": readiness_status.timestamp,
        })))
    } else {
        // Return 503 Service Unavailable if not ready
        Err(AppError::ServiceUnavailable(format!(
            "Service not ready: {}",
            readiness_status.message.unwrap_or_else(|| "Unknown reason".to_string())
        )))
    }
}