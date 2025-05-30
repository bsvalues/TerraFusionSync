use actix_web::{web, App, HttpServer};
use actix_web::middleware::{Logger, NormalizePath};
use env_logger::Env;
use dotenv::dotenv;
use std::io;
use openssl::ssl::{SslAcceptor, SslFiletype, SslMethod};

mod routes;
mod handlers;
mod services;
mod models;
mod config;

#[actix_web::main]
async fn main() -> io::Result<()> {
    // Load environment variables from .env file
    dotenv().ok();
    
    // Initialize logger
    env_logger::init_from_env(Env::default().default_filter_or("info"));
    
    // Print startup banner
    println!("
    ████████╗███████╗██████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗██╗ ██████╗ ███╗   ██╗
    ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██║   ██║██╔════╝██║██╔═══██╗████╗  ██║
       ██║   █████╗  ██████╔╝██████╔╝███████║█████╗  ██║   ██║███████╗██║██║   ██║██╔██╗ ██║
       ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║██╔══╝  ██║   ██║╚════██║██║██║   ██║██║╚██╗██║
       ██║   ███████╗██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝███████║██║╚██████╔╝██║ ╚████║
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
       
    Sync Service - Starting up...
    ");
    
    // Load configuration
    let config = config::Config::from_env();
    
    // Initialize database connection
    let db_pool = terrafusion_common::database::create_pool_from_env().await
        .expect("Failed to create database pool");
    
    // Initialize services
    let sync_engine = services::sync_engine::SyncEngine::new(db_pool.clone());
    
    // Create shared application state
    let app_state = web::Data::new(AppState {
        db_pool: db_pool.clone(),
        config: config.clone(),
        sync_engine: sync_engine.clone(),
    });
    
    // Run database migrations
    let mut migrator = terrafusion_common::database::migrations::Migrator::new(db_pool.clone());
    // Register migrations here
    // migrations::register_all_migrations(&mut migrator);
    
    // Run pending migrations
    match migrator.run_pending_migrations().await {
        Ok(_) => log::info!("Database migrations completed successfully"),
        Err(e) => log::error!("Database migration error: {}", e),
    }
    
    // Initialize scheduler
    let scheduler_handle = services::scheduler::start_scheduler(sync_engine, db_pool.clone())
        .await
        .expect("Failed to start scheduler");
    
    log::info!("Starting Sync Service on {}:{}", config.host, config.port);
    
    // Configure and start HTTP server
    let server = if config.use_ssl {
        // Configure SSL
        let mut builder = SslAcceptor::mozilla_intermediate(SslMethod::tls()).unwrap();
        builder.set_private_key_file(&config.ssl_key_file, SslFiletype::PEM).unwrap();
        builder.set_certificate_chain_file(&config.ssl_cert_file).unwrap();
        
        // Start HTTPS server
        HttpServer::new(move || create_app(app_state.clone()))
            .bind_openssl(format!("{}:{}", config.host, config.port), builder)?
    } else {
        // Start HTTP server
        HttpServer::new(move || create_app(app_state.clone()))
            .bind(format!("{}:{}", config.host, config.port))?
    };
    
    // Run the server with configured workers
    let server_handle = server
        .workers(config.worker_threads)
        .run();
    
    // Wait for server to complete
    server_handle.await?;
    
    // Shutdown scheduler gracefully
    scheduler_handle.shutdown().await;
    
    Ok(())
}

fn create_app(app_state: web::Data<AppState>) -> App<
    impl actix_service::ServiceFactory<
        actix_web::dev::ServiceRequest,
        Response = actix_web::dev::ServiceResponse,
        Error = actix_web::Error,
        Config = (),
    >,
> {
    App::new()
        .wrap(Logger::default())
        .wrap(NormalizePath::trim())
        .app_data(app_state.clone())
        
        // API Routes
        .service(
            web::scope("/api/v1")
                .configure(routes::api::configure)
        )
        
        // Health and metrics endpoints
        .service(
            web::scope("/system")
                .configure(routes::system::configure)
        )
        
        // Sync operations
        .service(
            web::scope("/sync-pairs")
                .configure(routes::sync_pairs::configure)
        )
        .service(
            web::scope("/sync-operations")
                .configure(routes::sync_operations::configure)
        )
        
        // Error handlers
        .app_data(web::JsonConfig::default().error_handler(|err, _req| {
            log::error!("JSON parsing error: {:?}", err);
            actix_web::error::ErrorBadRequest(format!("JSON parsing error: {}", err))
        }))
}

/// Application state shared across all handlers
#[derive(Clone)]
pub struct AppState {
    pub db_pool: terrafusion_common::database::DbPool,
    pub config: config::Config,
    pub sync_engine: services::sync_engine::SyncEngine,
}