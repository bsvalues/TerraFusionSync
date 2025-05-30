use actix_web::{web, App, HttpServer};
use actix_web::middleware::{Logger, NormalizePath};
use actix_files as fs;
use env_logger::Env;
use dotenv::dotenv;
use std::env;
use handlebars::Handlebars;
use std::io;
use std::sync::Arc;
use openssl::ssl::{SslAcceptor, SslFiletype, SslMethod};

mod routes;
mod handlers;
mod middlewares;
mod models;
mod services;
mod config;
mod errors;
mod utils;

#[actix_web::main]
async fn main() -> io::Result<()> {
    // Load environment variables from .env file
    dotenv().ok();
    
    // Initialize logger with environment-based configuration
    env_logger::init_from_env(Env::default().default_filter_or("info"));
    
    // Print startup banner
    println!("
    ████████╗███████╗██████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗██╗ ██████╗ ███╗   ██╗
    ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██║   ██║██╔════╝██║██╔═══██╗████╗  ██║
       ██║   █████╗  ██████╔╝██████╔╝███████║█████╗  ██║   ██║███████╗██║██║   ██║██╔██╗ ██║
       ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║██╔══╝  ██║   ██║╚════██║██║██║   ██║██║╚██╗██║
       ██║   ███████╗██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝███████║██║╚██████╔╝██║ ╚████║
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
       
    API Gateway - Starting up...
    ");
    
    let config = config::AppConfig::from_env();
    log::info!("Starting TerraFusion API Gateway on {}:{}", config.host, config.port);
    
    // Register and configure Handlebars for templates
    let mut handlebars = Handlebars::new();
    handlebars.register_templates_directory(".hbs", "./templates").expect("Failed to register Handlebars templates");
    handlebars.set_dev_mode(config.environment != "production");
    
    // Create shared application state
    let app_state = web::Data::new(AppState {
        handlebars: Arc::new(handlebars),
        config: config.clone(),
        sync_service_client: services::SyncServiceClient::new(&config.sync_service_url),
        gis_export_client: services::GisExportClient::new(&config.gis_export_service_url),
    });
    
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
        .wrap(middlewares::AuthMiddleware::default())
        .wrap(middlewares::SecurityHeadersMiddleware::default())
        .wrap(NormalizePath::trim())
        .app_data(app_state.clone())
        
        // Static files
        .service(fs::Files::new("/static", "./static").show_files_listing(false))
        
        // UI Routes
        .service(routes::ui::configure())
        
        // API Routes
        .service(
            web::scope("/api/v1")
                .wrap(middlewares::ApiKeyMiddleware::default())
                .configure(routes::api::configure)
        )
        
        // Health and metrics endpoints
        .service(
            web::scope("/system")
                .configure(routes::system::configure)
        )
        
        // Error handlers
        .app_data(web::JsonConfig::default().error_handler(|err, _req| {
            log::error!("JSON parsing error: {:?}", err);
            errors::AppError::BadRequest(err.to_string()).into()
        }))
}

pub struct AppState {
    pub handlebars: Arc<Handlebars<'static>>,
    pub config: config::AppConfig,
    pub sync_service_client: services::SyncServiceClient,
    pub gis_export_client: services::GisExportClient,
}