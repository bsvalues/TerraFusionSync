use actix_web::{web, App, HttpServer, middleware::Logger};
use env_logger::Env;
use std::sync::Arc;

mod models;
mod service;
mod handlers;

use service::GisExportService;
use handlers::{AppState, configure_routes};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logger
    env_logger::init_from_env(Env::default().default_filter_or("info"));

    // Load configuration
    let config = terrafusion_gis_export::GisExportConfig::default();
    
    // Initialize the GIS Export service
    let gis_service = match terrafusion_gis_export::init_service(config.clone()).await {
        Ok(service) => Arc::new(service),
        Err(e) => {
            log::error!("Failed to initialize GIS Export service: {}", e);
            std::process::exit(1);
        }
    };

    let port = std::env::var("GIS_EXPORT_PORT")
        .unwrap_or_else(|_| "7000".to_string())
        .parse::<u16>()
        .expect("Invalid port number");

    log::info!("🦀 TerraFusion GIS Export Service (Rust) starting on port {}", port);

    // Start HTTP server
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(AppState {
                gis_service: gis_service.clone(),
            }))
            .wrap(Logger::default())
            .configure(configure_routes)
    })
    .bind(("0.0.0.0", port))?
    .run()
    .await
}