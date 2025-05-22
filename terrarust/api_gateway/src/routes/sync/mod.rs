use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/sync")
            .route("/pairs", web::get().to(handlers::sync::get_sync_pairs))
            .route("/pairs", web::post().to(handlers::sync::create_sync_pair))
            .route("/pairs/{id}", web::get().to(handlers::sync::get_sync_pair))
            .route("/pairs/{id}", web::put().to(handlers::sync::update_sync_pair))
            .route("/pairs/{id}", web::delete().to(handlers::sync::delete_sync_pair))
            .route("/pairs/{id}/toggle", web::post().to(handlers::sync::toggle_sync_pair))
            .route("/operations", web::get().to(handlers::sync::get_sync_operations))
            .route("/operations", web::post().to(handlers::sync::create_sync_operation))
            .route("/operations/{id}", web::get().to(handlers::sync::get_sync_operation))
            .route("/operations/{id}/cancel", web::post().to(handlers::sync::cancel_sync_operation))
    );
}