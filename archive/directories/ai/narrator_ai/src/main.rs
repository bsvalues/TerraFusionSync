use actix_web::{web, App, HttpServer, middleware::Logger};
use env_logger::Env;
use dotenv::dotenv;
use std::env;

mod config;
mod routes;
mod ollama_client;
mod metrics;

use config::Config;
use metrics::setup_metrics;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Load environment variables
    dotenv().ok();
    
    // Initialize logger
    env_logger::init_from_env(Env::default().default_filter_or("info"));
    
    // Load configuration
    let config = Config::from_env();
    
    log::info!("🤖 Starting NarratorAI Service v{}", env!("CARGO_PKG_VERSION"));
    log::info!("🌐 Ollama URL: {}", config.ollama_url);
    log::info!("🧠 Default Model: {}", config.default_model);
    log::info!("🚀 Server will start on port {}", config.port);
    
    // Setup metrics
    let metrics = setup_metrics();
    
    // Start HTTP server
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(config.clone()))
            .app_data(web::Data::new(metrics.clone()))
            .wrap(Logger::default())
            .service(
                web::scope("/api/v1")
                    .route("/health", web::get().to(routes::health_check))
                    .route("/summarize", web::post().to(routes::summarize_text))
                    .route("/classify", web::post().to(routes::classify_text))
                    .route("/explain", web::post().to(routes::explain_data))
                    .route("/metrics", web::get().to(routes::get_metrics))
            )
            .route("/", web::get().to(routes::index))
    })
    .bind(("0.0.0.0", config.port))?
    .run()
    .await
}