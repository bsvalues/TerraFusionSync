use actix_web::web;
use crate::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/audit")
            .route("/entries", web::get().to(handlers::audit::get_audit_entries))
            .route("/entries/{id}", web::get().to(handlers::audit::get_audit_entry))
            .route("/summary", web::get().to(handlers::audit::get_audit_summary))
    );
}