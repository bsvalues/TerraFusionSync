use actix_web::{web, HttpResponse, Responder, get};
use serde_json::json;
use terrafusion_common::{Result, Error};
use terrafusion_common::models::{HealthStatus, HealthCheck, ServiceHealth};
use crate::AppState;

/// Configure system routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(health_check)
       .service(metrics)
       .service(liveness_check)
       .service(readiness_check);
}

/// Health check endpoint
#[get("/health")]
async fn health_check(app_state: web::Data<AppState>) -> Result<impl Responder> {
    let now = chrono::Utc::now();
    
    // Check database connectivity
    let db_status = match sqlx::query("SELECT 1")
        .execute(&app_state.db_pool)
        .await
    {
        Ok(_) => HealthStatus::Up,
        Err(_) => HealthStatus::Down,
    };
    
    // Check scheduler status
    let scheduler_status = if app_state.config.scheduler_enabled {
        HealthStatus::Up // TODO: Check actual scheduler status
    } else {
        HealthStatus::Down
    };
    
    let services = vec![
        ServiceHealth {
            name: "database".to_string(),
            status: db_status,
            version: None,
            latency_ms: None,
            message: None,
            last_check: now,
        },
        ServiceHealth {
            name: "scheduler".to_string(),
            status: scheduler_status,
            version: None,
            latency_ms: None,
            message: None,
            last_check: now,
        },
    ];
    
    let overall_status = if services.iter().all(|s| s.status == HealthStatus::Up) {
        HealthStatus::Up
    } else if services.iter().any(|s| s.status == HealthStatus::Up) {
        HealthStatus::Degraded
    } else {
        HealthStatus::Down
    };
    
    let health_check = HealthCheck {
        status: overall_status,
        version: env!("CARGO_PKG_VERSION").to_string(),
        services,
        timestamp: now,
    };
    
    Ok(web::Json(health_check))
}

/// Prometheus metrics endpoint
#[get("/metrics")]
async fn metrics(app_state: web::Data<AppState>) -> Result<impl Responder> {
    // TODO: Implement actual Prometheus metrics collection
    let metrics_data = format!(
        "# HELP sync_operations_total Total number of sync operations\n\
         # TYPE sync_operations_total counter\n\
         sync_operations_total{{status=\"completed\"}} 0\n\
         sync_operations_total{{status=\"failed\"}} 0\n\
         \n\
         # HELP sync_pairs_total Total number of sync pairs\n\
         # TYPE sync_pairs_total gauge\n\
         sync_pairs_total{{active=\"true\"}} 0\n\
         sync_pairs_total{{active=\"false\"}} 0\n\
         \n\
         # HELP sync_records_processed_total Total number of records processed\n\
         # TYPE sync_records_processed_total counter\n\
         sync_records_processed_total 0\n"
    );
    
    Ok(HttpResponse::Ok()
        .content_type("text/plain; charset=utf-8")
        .body(metrics_data))
}

/// Kubernetes liveness probe endpoint
#[get("/liveness")]
async fn liveness_check() -> Result<impl Responder> {
    Ok(web::Json(json!({
        "status": "UP",
        "timestamp": chrono::Utc::now()
    })))
}

/// Kubernetes readiness probe endpoint
#[get("/readiness")]
async fn readiness_check(app_state: web::Data<AppState>) -> Result<impl Responder> {
    // Check if the service is ready to handle requests
    let db_ready = sqlx::query("SELECT 1")
        .execute(&app_state.db_pool)
        .await
        .is_ok();
    
    if db_ready {
        Ok(web::Json(json!({
            "status": "READY",
            "checks": {
                "database": "UP"
            },
            "timestamp": chrono::Utc::now()
        })))
    } else {
        Err(Error::ServiceUnavailable("Database not ready".to_string()))
    }
}