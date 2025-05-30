use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/gis")
            .route("/exports", web::get().to(handlers::gis::get_exports))
            .route("/exports", web::post().to(handlers::gis::create_export))
            .route("/exports/{id}", web::get().to(handlers::gis::get_export))
            .route("/exports/{id}/cancel", web::post().to(handlers::gis::cancel_export))
            .route("/exports/{id}/download", web::get().to(handlers::gis::download_export))
            .route("/counties/{county_id}/config", web::get().to(handlers::gis::get_county_config))
            .route("/counties/{county_id}/layers", web::get().to(handlers::gis::get_county_layers))
    );
}