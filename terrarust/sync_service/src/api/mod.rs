use actix_web::web;

pub mod sync_pairs;
pub mod sync_operations;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/sync")
            .configure(sync_pairs::configure)
            .configure(sync_operations::configure)
    );
}