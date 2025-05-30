use actix_web::web;

// Configure all routes for the API Gateway
pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    // Web UI routes
    cfg.service(
        web::scope("")
            .route("/", web::get().to(crate::handlers::ui::index))
            .route("/login", web::get().to(crate::handlers::auth::login_page))
            .route("/login", web::post().to(crate::handlers::auth::login))
            .route("/logout", web::get().to(crate::handlers::auth::logout))
            .route("/dashboard", web::get().to(crate::handlers::ui::dashboard))
            .route("/sync-dashboard", web::get().to(crate::handlers::ui::sync_dashboard))
            .route("/gis-export", web::get().to(crate::handlers::ui::gis_export_dashboard))
    );
    
    // API v1 routes
    cfg.service(
        web::scope("/api/v1")
            // Health and status
            .route("/health", web::get().to(crate::handlers::health::health_check))
            .route("/status", web::get().to(crate::handlers::health::status))
            .route("/metrics", web::get().to(crate::handlers::metrics::get_metrics))
            
            // Sync operations
            .service(
                web::scope("/sync-operations")
                    .route("", web::get().to(crate::handlers::sync_operations::get_all_operations))
                    .route("", web::post().to(crate::handlers::sync_operations::start_operation))
                    .route("/{id}", web::get().to(crate::handlers::sync_operations::get_operation))
                    .route("/{id}/cancel", web::post().to(crate::handlers::sync_operations::cancel_operation))
                    .route("/{id}/diffs", web::get().to(crate::handlers::sync_operations::get_operation_diffs))
            )
            
            // Sync pairs
            .service(
                web::scope("/sync-pairs")
                    .route("", web::get().to(crate::handlers::sync_pairs::get_all_pairs))
                    .route("", web::post().to(crate::handlers::sync_pairs::create_pair))
                    .route("/{id}", web::get().to(crate::handlers::sync_pairs::get_pair))
                    .route("/{id}", web::put().to(crate::handlers::sync_pairs::update_pair))
                    .route("/{id}/toggle", web::post().to(crate::handlers::sync_pairs::toggle_pair))
            )
            
            // GIS Exports
            .service(
                web::scope("/gis-exports")
                    .route("", web::get().to(crate::handlers::gis_exports::get_all_exports))
                    .route("", web::post().to(crate::handlers::gis_exports::create_export))
                    .route("/{id}", web::get().to(crate::handlers::gis_exports::get_export))
                    .route("/{id}/cancel", web::post().to(crate::handlers::gis_exports::cancel_export))
                    .route("/{id}/download", web::get().to(crate::handlers::gis_exports::download_export))
            )
            
            // County configurations
            .service(
                web::scope("/counties")
                    .route("", web::get().to(crate::handlers::counties::get_all_counties))
                    .route("/{county_id}/config", web::get().to(crate::handlers::counties::get_county_config))
                    .route("/{county_id}/layers", web::get().to(crate::handlers::counties::get_county_layers))
            )
            
            // User management
            .service(
                web::scope("/users")
                    .route("", web::get().to(crate::handlers::users::get_all_users))
                    .route("", web::post().to(crate::handlers::users::create_user))
                    .route("/me", web::get().to(crate::handlers::users::get_current_user))
                    .route("/{id}", web::get().to(crate::handlers::users::get_user))
                    .route("/{id}", web::put().to(crate::handlers::users::update_user))
            )
    );
}