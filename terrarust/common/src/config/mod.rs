use serde::Deserialize;
use std::env;
use std::fs::File;
use std::io::Read;
use std::path::Path;
use toml;

use crate::error::{Error, Result};

#[derive(Clone, Debug, Deserialize)]
pub struct Config {
    pub database: DatabaseConfig,
    pub server: ServerConfig,
    pub logging: LoggingConfig,
    pub telemetry: TelemetryConfig,
    pub security: SecurityConfig,
}

#[derive(Clone, Debug, Deserialize)]
pub struct DatabaseConfig {
    pub username: String,
    pub password: String,
    pub host: String,
    pub port: u16,
    pub database_name: String,
    pub max_connections: u32,
}

#[derive(Clone, Debug, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub workers: usize,
}

#[derive(Clone, Debug, Deserialize)]
pub struct LoggingConfig {
    pub level: String,
}

#[derive(Clone, Debug, Deserialize)]
pub struct TelemetryConfig {
    pub jaeger_endpoint: String,
    pub service_name: String,
}

#[derive(Clone, Debug, Deserialize)]
pub struct SecurityConfig {
    pub jwt_secret: String,
    pub token_expiration: u64,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        // Look for TERRAFUSION_CONFIG environment variable
        let config_path = env::var("TERRAFUSION_CONFIG")
            .unwrap_or_else(|_| "config/default.toml".to_string());
        
        Self::from_file(&config_path)
    }
    
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let mut file = File::open(&path)
            .map_err(|e| Error::ConfigError(format!("Failed to open config file: {}", e)))?;
        
        let mut content = String::new();
        file.read_to_string(&mut content)
            .map_err(|e| Error::ConfigError(format!("Failed to read config file: {}", e)))?;
        
        let config: Config = toml::from_str(&content)
            .map_err(|e| Error::ConfigError(format!("Failed to parse config file: {}", e)))?;
        
        Ok(config)
    }
}