use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/operations")
            .route(web::get().to(handlers::sync_operations::get_sync_operations))
            .route(web::post().to(handlers::sync_operations::create_sync_operation))
    )
    .service(
        web::resource("/operations/{id}")
            .route(web::get().to(handlers::sync_operations::get_sync_operation))
    )
    .service(
        web::resource("/operations/{id}/cancel")
            .route(web::post().to(handlers::sync_operations::cancel_sync_operation))
    );
}