use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/system-metrics")
            .route("", web::get().to(handlers::metrics::get_system_metrics))
            .route("/refresh", web::post().to(handlers::metrics::refresh_metrics))
            .route("/status", web::get().to(handlers::metrics::get_metrics_status))
            .route("/overview", web::get().to(handlers::metrics::get_metrics_overview))
    );
}