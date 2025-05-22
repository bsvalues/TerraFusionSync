use config::{Config, ConfigError, Environment, File};
use serde::Deserialize;
use std::env;

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseSettings {
    pub username: String,
    pub password: String,
    pub host: String,
    pub port: u16,
    pub database_name: String,
    pub max_connections: u32,
}

impl DatabaseSettings {
    pub fn connection_string(&self) -> String {
        format!(
            "postgres://{}:{}@{}:{}/{}",
            self.username, self.password, self.host, self.port, self.database_name
        )
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerSettings {
    pub host: String,
    pub port: u16,
    pub workers: usize,
}

#[derive(Debug, Deserialize, Clone)]
pub struct LoggingSettings {
    pub level: String,
}

#[derive(Debug, Deserialize, Clone)]
pub struct TelemetrySettings {
    pub jaeger_endpoint: String,
    pub service_name: String,
}

#[derive(Debug, Deserialize, Clone)]
pub struct SecuritySettings {
    pub jwt_secret: String,
    pub token_expiration: i64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Settings {
    pub database: DatabaseSettings,
    pub server: ServerSettings,
    pub logging: LoggingSettings,
    pub telemetry: TelemetrySettings,
    pub security: SecuritySettings,
    pub environment: String,
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        let run_mode = env::var("RUN_MODE").unwrap_or_else(|_| "development".into());

        let s = Config::builder()
            // Start with default settings
            .add_source(File::with_name("config/default"))
            // Add environment-specific settings
            .add_source(File::with_name(&format!("config/{}", run_mode)).required(false))
            // Add local overrides
            .add_source(File::with_name("config/local").required(false))
            // Add in environment variables with prefix TERRA_
            .add_source(Environment::with_prefix("TERRA").separator("__"))
            .build()?;

        s.try_deserialize()
    }
}