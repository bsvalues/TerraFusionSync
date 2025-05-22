use actix_web::{middleware, web, App, HttpServer};
use common::config::Config;
use common::database::Database;
use common::error::Result;
use common::telemetry::TelemetryService;
use std::sync::Arc;

mod api;
mod handlers;
mod services;

// Define the application state shared across request handlers
pub struct AppState {
    pub config: Config,
    pub database: Database,
    pub telemetry: Arc<TelemetryService>,
    pub export_service: services::export::GisExportService,
}

#[actix_web::main]
async fn main() -> Result<()> {
    // Initialize configuration
    let config = Config::from_env().expect("Failed to load configuration");
    
    // Initialize logging based on configuration
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(&config.logging.level))
        .init();
    
    // Initialize telemetry
    let telemetry = Arc::new(TelemetryService::new(
        &config.telemetry.service_name,
        &config.telemetry.jaeger_endpoint,
    )?);
    
    // Initialize database connection
    let database = Database::new(
        &config.database.username,
        &config.database.password,
        &config.database.host,
        config.database.port,
        &config.database.database_name,
        config.database.max_connections,
    )?;
    
    // Create export service
    let export_service = services::export::GisExportService::new(database.clone(), telemetry.clone());
    
    // Set up application state
    let app_state = web::Data::new(AppState {
        config: config.clone(),
        database: database.clone(),
        telemetry: telemetry.clone(),
        export_service,
    });
    
    // Start HTTP server
    log::info!("Starting GIS Export service on {}:{}", config.server.host, config.server.port);
    
    HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .wrap(middleware::Logger::default())
            .configure(api::configure_routes)
            .service(web::resource("/health").to(handlers::health::health_check))
            .service(web::resource("/metrics").to(handlers::metrics::get_metrics))
    })
    .workers(config.server.workers)
    .bind((config.server.host.clone(), config.server.port))?
    .run()
    .await?;
    
    Ok(())
}