use actix_cors::Cors;
use actix_files::Files;
use actix_session::{SessionMiddleware, storage::CookieSessionStore};
use actix_web::{cookie::Key, middleware, web, App, HttpServer};
use common::config::Config;
use common::database::Database;
use common::error::Result;
use common::telemetry::TelemetryService;
use handlebars::Handlebars;
use std::sync::Arc;

mod api;
mod handlers;
mod middleware as app_middleware;
mod services;

// Define the application state shared across request handlers
pub struct AppState {
    pub config: Config,
    pub database: Database,
    pub telemetry: Arc<TelemetryService>,
    pub handlebars: web::Data<Handlebars<'static>>,
    pub services: services::Services,
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
    
    // Initialize templating engine
    let mut handlebars = Handlebars::new();
    handlebars.register_templates_directory(".hbs", "templates")
        .expect("Failed to register template directory");
    let handlebars_data = web::Data::new(handlebars);
    
    // Initialize services
    let services = services::Services::new(&config);
    
    // Set up application state
    let app_state = web::Data::new(AppState {
        config: config.clone(),
        database: database.clone(),
        telemetry: telemetry.clone(),
        handlebars: handlebars_data.clone(),
        services,
    });
    
    // Test database connection
    if let Err(e) = database.test_connection() {
        log::error!("Database connection test failed: {}", e);
        return Err(e);
    }
    
    // Generate a key for cookie session
    let secret_key = Key::generate();
    
    // Start HTTP server
    log::info!("Starting API Gateway on {}:{}", config.server.host, config.server.port);
    
    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
        
        App::new()
            .app_data(app_state.clone())
            .app_data(handlebars_data.clone())
            .wrap(middleware::Logger::default())
            .wrap(cors)
            .wrap(SessionMiddleware::new(
                CookieSessionStore::default(),
                secret_key.clone()
            ))
            .wrap(app_middleware::auth::AuthMiddleware)
            .configure(api::configure_routes)
            .service(Files::new("/static", "static").prefer_utf8(true))
    })
    .workers(config.server.workers)
    .bind((config.server.host.clone(), config.server.port))?
    .run()
    .await?;
    
    Ok(())
}