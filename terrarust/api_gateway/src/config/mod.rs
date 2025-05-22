use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct ServiceConfig {
    pub sync_service_url: String,
    pub gis_service_url: String,
}

impl Default for ServiceConfig {
    fn default() -> Self {
        Self {
            sync_service_url: "http://localhost:8080".to_string(),
            gis_service_url: "http://localhost:8081".to_string(),
        }
    }
}