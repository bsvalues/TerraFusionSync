use actix_web::web;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/exports")
            .route("", web::get().to(crate::handlers::exports::get_exports))
            .route("", web::post().to(crate::handlers::exports::create_export))
            .route("/{id}", web::get().to(crate::handlers::exports::get_export))
            .route("/{id}/cancel", web::post().to(crate::handlers::exports::cancel_export))
            .route("/{id}/download", web::get().to(crate::handlers::exports::download_export))
    )
    .service(
        web::scope("/counties")
            .route("/{county_id}/config", web::get().to(crate::handlers::counties::get_county_config))
            .route("/{county_id}/layers", web::get().to(crate::handlers::counties::get_county_layers))
    );
}