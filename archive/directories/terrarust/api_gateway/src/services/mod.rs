use common::config::Config;
use reqwest::Client;
use std::time::Duration;

pub mod sync_service;
pub mod gis_export;

/// Container for all service clients
pub struct Services {
    pub sync_service: sync_service::SyncServiceClient,
    pub gis_export: gis_export::GisExportClient,
}

impl Services {
    pub fn new(config: &Config) -> Self {
        // Create a shared HTTP client with defaults
        let http_client = Client::builder()
            .timeout(Duration::from_secs(30))
            .connect_timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to build HTTP client");
        
        // Initialize service clients
        // Note: In a production environment, these URLs would come from config
        let sync_service = sync_service::SyncServiceClient::new(
            "http://localhost:5001",
            http_client.clone(),
        );
        
        let gis_export = gis_export::GisExportClient::new(
            "http://localhost:8080",
            http_client,
        );
        
        Self {
            sync_service,
            gis_export,
        }
    }
}