use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/pairs")
            .route(web::get().to(handlers::sync_pairs::get_sync_pairs))
            .route(web::post().to(handlers::sync_pairs::create_sync_pair))
    )
    .service(
        web::resource("/pairs/{id}")
            .route(web::get().to(handlers::sync_pairs::get_sync_pair))
            .route(web::put().to(handlers::sync_pairs::update_sync_pair))
            .route(web::delete().to(handlers::sync_pairs::delete_sync_pair))
    )
    .service(
        web::resource("/pairs/{id}/toggle")
            .route(web::post().to(handlers::sync_pairs::toggle_sync_pair))
    );
}