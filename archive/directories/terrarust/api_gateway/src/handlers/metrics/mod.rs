use actix_web::{web, HttpResponse, Responder};
use crate::AppState;

/// Prometheus metrics endpoint
pub async fn get_metrics(state: web::Data<AppState>) -> impl Responder {
    // Generate prometheus metrics format using the telemetry service
    let metrics_text = state.telemetry.metrics();
    HttpResponse::Ok()
        .content_type("text/plain")
        .body(metrics_text)
}