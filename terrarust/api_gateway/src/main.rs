mod api;
mod auth;
mod config;
mod handlers;
mod middleware;
mod routes;
mod services;

use actix_cors::Cors;
use actix_web::{web, App, HttpServer};
use common::config::Settings;
use common::database::Database;
use common::telemetry::TelemetryService;
use dotenv::dotenv;
use std::sync::Arc;
use tracing_actix_web::TracingLogger;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Load environment variables from .env file
    dotenv().ok();
    
    // Initialize configuration
    let settings = Settings::new().expect("Failed to read configuration");
    
    // Set up logging
    env_logger::init_from_env(env_logger::Env::new().default_filter_or(&settings.logging.level));
    
    // Initialize telemetry
    let telemetry_service = Arc::new(TelemetryService::new());
    let _subscriber = TelemetryService::init_tracing(&settings.telemetry);
    
    // Set up database connection pool
    let database = Database::new(&settings.database)
        .expect("Failed to create database connection pool");
    
    // Create application state
    let app_state = web::Data::new(AppState {
        settings: settings.clone(),
        database: database.clone(),
        telemetry: telemetry_service.clone(),
    });
    
    // Start HTTP server
    log::info!("Starting API Gateway on {}:{}", settings.server.host, settings.server.port);
    
    HttpServer::new(move || {
        // Configure CORS
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
            
        App::new()
            .wrap(TracingLogger::default())
            .wrap(cors)
            .wrap(middleware::auth::AuthMiddleware::new(settings.security.jwt_secret.clone()))
            .app_data(app_state.clone())
            .service(
                web::scope("/api")
                    .configure(routes::configure_routes)
            )
            .service(
                web::scope("/metrics")
                    .route("", web::get().to(handlers::metrics::get_metrics))
            )
            .service(
                web::resource("/health")
                    .route(web::get().to(handlers::health::health_check))
            )
    })
    .workers(settings.server.workers)
    .bind(format!("{}:{}", settings.server.host, settings.server.port))?
    .run()
    .await
}

#[derive(Clone)]
pub struct AppState {
    pub settings: Settings,
    pub database: Database,
    pub telemetry: Arc<TelemetryService>,
}