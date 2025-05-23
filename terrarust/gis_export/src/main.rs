use actix_web::{web, App, HttpServer};
use actix_web::middleware::{Logger, NormalizePath};
use actix_files as fs;
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
       
    GIS Export Service - Starting up...
    ");
    
    // Load configuration
    let config = config::Config::from_env();
    
    // Initialize database connection
    let db_pool = terrafusion_common::database::create_pool_from_env().await
        .expect("Failed to create database pool");
    
    // Initialize export engine
    let export_engine = services::export_engine::ExportEngine::new(db_pool.clone(), &config);
    
    // Create shared application state
    let app_state = web::Data::new(AppState {
        db_pool: db_pool.clone(),
        config: config.clone(),
        export_engine: export_engine.clone(),
    });
    
    // Run database migrations
    let mut migrator = terrafusion_common::database::migrations::Migrator::new(db_pool.clone());
    // Register GIS export migrations here
    // migrations::register_gis_export_migrations(&mut migrator);
    
    // Run pending migrations
    match migrator.run_pending_migrations().await {
        Ok(_) => log::info!("Database migrations completed successfully"),
        Err(e) => log::error!("Database migration error: {}", e),
    }
    
    log::info!("Starting GIS Export Service on {}:{}", config.host, config.port);
    
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
    server
        .workers(config.worker_threads)
        .run()
        .await
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
        
        // Static files for export downloads
        .service(fs::Files::new("/exports", "./exports").show_files_listing(false))
        
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
        
        // GIS export endpoints
        .service(
            web::scope("/gis-exports")
                .configure(routes::gis_exports::configure)
        )
        
        // County configuration endpoints
        .service(
            web::scope("/counties")
                .configure(routes::counties::configure)
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
    pub export_engine: services::export_engine::ExportEngine,
}