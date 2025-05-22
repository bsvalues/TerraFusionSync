use actix_web::{middleware, web, App, HttpServer};
use actix_cors::Cors;
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
    pub sync_engine: services::sync_engine::SyncEngine,
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
    
    // Initialize sync engine
    let sync_engine = services::sync_engine::SyncEngine::new(
        database.clone(),
        telemetry.clone(),
    );
    
    // Set up application state
    let app_state = web::Data::new(AppState {
        config: config.clone(),
        database: database.clone(),
        telemetry: telemetry.clone(),
        sync_engine,
    });
    
    // Test database connection
    if let Err(e) = database.test_connection() {
        log::error!("Database connection test failed: {}", e);
        return Err(e);
    }
    
    // Start HTTP server
    log::info!("Starting Sync Service on {}:{}", config.server.host, config.server.port);
    
    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
        
        App::new()
            .app_data(app_state.clone())
            .wrap(middleware::Logger::default())
            .wrap(cors)
            .configure(api::configure_routes)
    })
    .workers(config.server.workers)
    .bind((config.server.host.clone(), config.server.port))?
    .run()
    .await?;
    
    Ok(())
}