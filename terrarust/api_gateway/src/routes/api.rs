use actix_web::{web, Scope};

mod auth;
mod sync;
mod gis_export;
mod metrics;
mod counties;

/// Configure API routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/auth")
            .configure(auth::configure)
    );
    
    cfg.service(
        web::scope("/sync-pairs")
            .configure(sync::configure_pairs)
    );
    
    cfg.service(
        web::scope("/sync-operations")
            .configure(sync::configure_operations)
    );
    
    cfg.service(
        web::scope("/gis-exports")
            .configure(gis_export::configure)
    );
    
    cfg.service(
        web::scope("/metrics")
            .configure(metrics::configure)
    );
    
    cfg.service(
        web::scope("/counties")
            .configure(counties::configure)
    );
}