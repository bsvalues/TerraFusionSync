use actix_web::web;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/sync-pairs")
            .route("", web::get().to(crate::handlers::sync_pairs::get_all_pairs))
            .route("", web::post().to(crate::handlers::sync_pairs::create_pair))
            .route("/{id}", web::get().to(crate::handlers::sync_pairs::get_pair))
            .route("/{id}", web::put().to(crate::handlers::sync_pairs::update_pair))
            .route("/{id}/toggle", web::post().to(crate::handlers::sync_pairs::toggle_pair))
    )
    .service(
        web::scope("/sync-operations")
            .route("", web::get().to(crate::handlers::sync_operations::get_all_operations))
            .route("", web::post().to(crate::handlers::sync_operations::start_operation))
            .route("/{id}", web::get().to(crate::handlers::sync_operations::get_operation))
            .route("/{id}/cancel", web::post().to(crate::handlers::sync_operations::cancel_operation))
    )
    .service(
        web::scope("/sync-diffs")
            .route("", web::get().to(crate::handlers::sync_diffs::get_all_diffs))
            .route("/{id}", web::get().to(crate::handlers::sync_diffs::get_diff))
    )
    .service(
        web::resource("/health").to(crate::handlers::health::health_check)
    )
    .service(
        web::resource("/metrics").to(crate::handlers::metrics::get_metrics)
    );
}