use actix_web::web;

pub mod sync;
pub mod gis;
pub mod audit;
pub mod metrics;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.configure(sync::configure)
       .configure(gis::configure)
       .configure(audit::configure)
       .configure(metrics::configure);
}