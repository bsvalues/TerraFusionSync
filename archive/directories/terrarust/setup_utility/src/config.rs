use anyhow::{Result, Context};
use std::path::PathBuf;
use tokio::fs;
use log::{info, warn};
use serde::{Deserialize, Serialize};

/// Generate configuration files for TerraFusion Platform
pub async fn generate_configuration(
    install_dir: &PathBuf,
    county_id: &str,
    admin_email: &str,
) -> Result<()> {
    info!("Generating configuration for county: {}", county_id);
    
    let config_dir = install_dir.join("config");
    fs::create_dir_all(&config_dir).await
        .context("Failed to create config directory")?;
    
    // Generate main application configuration
    generate_app_config(&config_dir, county_id, admin_email).await?;
    
    // Generate logging configuration
    generate_logging_config(&config_dir).await?;
    
    // Generate county-specific configuration
    generate_county_config(&config_dir, county_id, admin_email).await?;
    
    // Generate service configurations
    generate_service_configs(&config_dir, county_id).await?;
    
    // Generate environment file
    generate_environment_file(&config_dir, county_id).await?;
    
    info!("Configuration files generated successfully");
    Ok(())
}

/// Generate main application configuration
async fn generate_app_config(
    config_dir: &PathBuf,
    county_id: &str,
    admin_email: &str,
) -> Result<()> {
    let config = AppConfig {
        application: ApplicationConfig {
            name: "TerraFusion Platform".to_string(),
            version: "1.0.0".to_string(),
            environment: "production".to_string(),
            county_id: county_id.to_string(),
            admin_email: admin_email.to_string(),
        },
        server: ServerConfig {
            host: "0.0.0.0".to_string(),
            port: 8000,
            workers: 4,
            max_connections: 1000,
            timeout_seconds: 30,
        },
        database: DatabaseConfig {
            host: "localhost".to_string(),
            port: 5433,
            name: format!("terrafusion_{}", county_id.replace("-", "_")),
            user: "terrafusion".to_string(),
            max_connections: 20,
            connection_timeout: 30,
        },
        security: SecurityConfig {
            jwt_secret_key: generate_secret_key(),
            session_timeout_hours: 8,
            max_login_attempts: 5,
            lockout_duration_minutes: 15,
            password_min_length: 8,
        },
        logging: LoggingConfig {
            level: "info".to_string(),
            file_enabled: true,
            console_enabled: true,
            max_file_size_mb: 50,
            max_files: 10,
        },
        sync: SyncConfig {
            max_concurrent_jobs: 5,
            job_timeout_minutes: 60,
            retry_attempts: 3,
            retry_delay_seconds: 30,
        },
        gis_export: GisExportConfig {
            max_export_size_mb: 500,
            temp_directory: "temp/exports".to_string(),
            cleanup_after_hours: 24,
            supported_formats: vec![
                "shapefile".to_string(),
                "geojson".to_string(), 
                "kml".to_string(),
                "geopackage".to_string(),
            ],
        },
    };
    
    let toml_content = toml::to_string_pretty(&config)
        .context("Failed to serialize app configuration")?;
    
    let config_file = config_dir.join("app.toml");
    fs::write(&config_file, toml_content).await
        .context("Failed to write app configuration")?;
    
    info!("Application configuration saved to {}", config_file.display());
    Ok(())
}

/// Generate logging configuration
async fn generate_logging_config(config_dir: &PathBuf) -> Result<()> {
    let config = LoggingDetailedConfig {
        appenders: AppendersConfig {
            console: ConsoleAppenderConfig {
                kind: "console".to_string(),
                encoder: EncoderConfig {
                    pattern: "[{d(%Y-%m-%d %H:%M:%S)} {l}] {t} - {m}{n}".to_string(),
                },
            },
            file: FileAppenderConfig {
                kind: "rolling_file".to_string(),
                path: "logs/terrafusion.log".to_string(),
                encoder: EncoderConfig {
                    pattern: "[{d(%Y-%m-%d %H:%M:%S)} {l}] {t} - {m}{n}".to_string(),
                },
                policy: PolicyConfig {
                    kind: "compound".to_string(),
                    trigger: TriggerConfig {
                        kind: "size".to_string(),
                        limit: "50mb".to_string(),
                    },
                    roller: RollerConfig {
                        kind: "fixed_window".to_string(),
                        pattern: "logs/terrafusion.{}.log".to_string(),
                        count: 10,
                    },
                },
            },
        },
        loggers: LoggersConfig {
            terrafusion: LoggerConfig {
                level: "info".to_string(),
                appenders: vec!["console".to_string(), "file".to_string()],
                additive: false,
            },
        },
        root: RootLoggerConfig {
            level: "warn".to_string(),
            appenders: vec!["console".to_string()],
        },
    };
    
    let toml_content = toml::to_string_pretty(&config)
        .context("Failed to serialize logging configuration")?;
    
    let config_file = config_dir.join("logging.toml");
    fs::write(&config_file, toml_content).await
        .context("Failed to write logging configuration")?;
    
    info!("Logging configuration saved to {}", config_file.display());
    Ok(())
}

/// Generate county-specific configuration
async fn generate_county_config(
    config_dir: &PathBuf,
    county_id: &str,
    admin_email: &str,
) -> Result<()> {
    let counties_dir = config_dir.join("counties");
    fs::create_dir_all(&counties_dir).await
        .context("Failed to create counties directory")?;
    
    let config = CountyConfig {
        county: CountyInfo {
            id: county_id.to_string(),
            name: format!("{} County", county_id.replace("-", " ").to_title_case()),
            state: extract_state_from_county_id(county_id),
            admin_email: admin_email.to_string(),
            timezone: "America/Los_Angeles".to_string(), // Default, can be customized
        },
        data_sources: vec![
            DataSourceConfig {
                name: "Assessment Database".to_string(),
                type_name: "postgresql".to_string(),
                connection_string: "postgresql://user:pass@localhost:5432/assessments".to_string(),
                enabled: false,
                sync_frequency_hours: 24,
            },
            DataSourceConfig {
                name: "GIS Database".to_string(),
                type_name: "postgresql".to_string(),
                connection_string: "postgresql://user:pass@localhost:5432/gis".to_string(),
                enabled: false,
                sync_frequency_hours: 6,
            },
        ],
        export_settings: ExportSettings {
            default_format: "shapefile".to_string(),
            coordinate_system: "EPSG:4326".to_string(),
            max_features_per_export: 50000,
            include_metadata: true,
        },
        notifications: NotificationSettings {
            email_enabled: true,
            admin_notifications: true,
            error_notifications: true,
            sync_completion_notifications: false,
        },
    };
    
    let toml_content = toml::to_string_pretty(&config)
        .context("Failed to serialize county configuration")?;
    
    let config_file = counties_dir.join(format!("{}.toml", county_id));
    fs::write(&config_file, toml_content).await
        .context("Failed to write county configuration")?;
    
    info!("County configuration saved to {}", config_file.display());
    Ok(())
}

/// Generate service-specific configurations
async fn generate_service_configs(config_dir: &PathBuf, county_id: &str) -> Result<()> {
    // API Gateway configuration
    let api_config = ApiGatewayConfig {
        port: 8000,
        cors_origins: vec!["http://localhost:3000".to_string()],
        rate_limiting: RateLimitConfig {
            enabled: true,
            requests_per_minute: 1000,
            burst_size: 100,
        },
        authentication: AuthConfig {
            method: "jwt".to_string(),
            token_expiry_hours: 8,
        },
    };
    
    let api_toml = toml::to_string_pretty(&api_config)
        .context("Failed to serialize API gateway configuration")?;
    
    fs::write(config_dir.join("api_gateway.toml"), api_toml).await
        .context("Failed to write API gateway configuration")?;
    
    // Sync Service configuration
    let sync_config = SyncServiceConfig {
        port: 8001,
        max_concurrent_syncs: 5,
        sync_timeout_minutes: 60,
        health_check_interval_seconds: 30,
    };
    
    let sync_toml = toml::to_string_pretty(&sync_config)
        .context("Failed to serialize sync service configuration")?;
    
    fs::write(config_dir.join("sync_service.toml"), sync_toml).await
        .context("Failed to write sync service configuration")?;
    
    // GIS Export Service configuration
    let gis_config = GisExportServiceConfig {
        port: 8002,
        temp_directory: "temp/gis_exports".to_string(),
        max_export_size_mb: 500,
        cleanup_interval_hours: 24,
    };
    
    let gis_toml = toml::to_string_pretty(&gis_config)
        .context("Failed to serialize GIS export service configuration")?;
    
    fs::write(config_dir.join("gis_export.toml"), gis_toml).await
        .context("Failed to write GIS export service configuration")?;
    
    info!("Service configurations generated successfully");
    Ok(())
}

/// Generate environment file
async fn generate_environment_file(config_dir: &PathBuf, county_id: &str) -> Result<()> {
    let env_content = format!(
        "# TerraFusion Platform Environment Configuration\n\
         # Generated for County: {}\n\
         \n\
         # Application Settings\n\
         TERRAFUSION_ENVIRONMENT=production\n\
         TERRAFUSION_COUNTY_ID={}\n\
         TERRAFUSION_LOG_LEVEL=info\n\
         \n\
         # Server Configuration\n\
         TERRAFUSION_API_HOST=0.0.0.0\n\
         TERRAFUSION_API_PORT=8000\n\
         TERRAFUSION_SYNC_PORT=8001\n\
         TERRAFUSION_GIS_PORT=8002\n\
         \n\
         # Database Configuration (will be updated during installation)\n\
         DATABASE_URL=postgresql://terrafusion:password@localhost:5433/terrafusion_{}\n\
         DATABASE_MAX_CONNECTIONS=20\n\
         \n\
         # Security Settings (will be generated during installation)\n\
         JWT_SECRET_KEY=change-this-secret-key\n\
         SESSION_SECRET=change-this-session-secret\n\
         \n\
         # Logging Configuration\n\
         RUST_LOG=info\n\
         RUST_BACKTRACE=1\n\
         \n\
         # Feature Flags\n\
         ENABLE_METRICS=true\n\
         ENABLE_TRACING=true\n\
         ENABLE_HEALTH_CHECKS=true\n",
        county_id,
        county_id,
        county_id.replace("-", "_")
    );
    
    let env_file = config_dir.join(".env");
    fs::write(&env_file, env_content).await
        .context("Failed to write environment file")?;
    
    info!("Environment file saved to {}", env_file.display());
    Ok(())
}

/// Generate a secure random secret key
fn generate_secret_key() -> String {
    use uuid::Uuid;
    let uuid1 = Uuid::new_v4().to_string().replace("-", "");
    let uuid2 = Uuid::new_v4().to_string().replace("-", "");
    format!("{}{}", uuid1, uuid2)
}

/// Extract state abbreviation from county ID
fn extract_state_from_county_id(county_id: &str) -> String {
    if let Some(state) = county_id.split('-').last() {
        state.to_uppercase()
    } else {
        "UNKNOWN".to_string()
    }
}

/// Convert string to title case
trait ToTitleCase {
    fn to_title_case(&self) -> String;
}

impl ToTitleCase for str {
    fn to_title_case(&self) -> String {
        self.split_whitespace()
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                }
            })
            .collect::<Vec<_>>()
            .join(" ")
    }
}

// Configuration structures
#[derive(Serialize, Deserialize)]
struct AppConfig {
    application: ApplicationConfig,
    server: ServerConfig,
    database: DatabaseConfig,
    security: SecurityConfig,
    logging: LoggingConfig,
    sync: SyncConfig,
    gis_export: GisExportConfig,
}

#[derive(Serialize, Deserialize)]
struct ApplicationConfig {
    name: String,
    version: String,
    environment: String,
    county_id: String,
    admin_email: String,
}

#[derive(Serialize, Deserialize)]
struct ServerConfig {
    host: String,
    port: u16,
    workers: u16,
    max_connections: u32,
    timeout_seconds: u32,
}

#[derive(Serialize, Deserialize)]
struct DatabaseConfig {
    host: String,
    port: u16,
    name: String,
    user: String,
    max_connections: u32,
    connection_timeout: u32,
}

#[derive(Serialize, Deserialize)]
struct SecurityConfig {
    jwt_secret_key: String,
    session_timeout_hours: u32,
    max_login_attempts: u32,
    lockout_duration_minutes: u32,
    password_min_length: u32,
}

#[derive(Serialize, Deserialize)]
struct LoggingConfig {
    level: String,
    file_enabled: bool,
    console_enabled: bool,
    max_file_size_mb: u32,
    max_files: u32,
}

#[derive(Serialize, Deserialize)]
struct SyncConfig {
    max_concurrent_jobs: u32,
    job_timeout_minutes: u32,
    retry_attempts: u32,
    retry_delay_seconds: u32,
}

#[derive(Serialize, Deserialize)]
struct GisExportConfig {
    max_export_size_mb: u32,
    temp_directory: String,
    cleanup_after_hours: u32,
    supported_formats: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct CountyConfig {
    county: CountyInfo,
    data_sources: Vec<DataSourceConfig>,
    export_settings: ExportSettings,
    notifications: NotificationSettings,
}

#[derive(Serialize, Deserialize)]
struct CountyInfo {
    id: String,
    name: String,
    state: String,
    admin_email: String,
    timezone: String,
}

#[derive(Serialize, Deserialize)]
struct DataSourceConfig {
    name: String,
    #[serde(rename = "type")]
    type_name: String,
    connection_string: String,
    enabled: bool,
    sync_frequency_hours: u32,
}

#[derive(Serialize, Deserialize)]
struct ExportSettings {
    default_format: String,
    coordinate_system: String,
    max_features_per_export: u32,
    include_metadata: bool,
}

#[derive(Serialize, Deserialize)]
struct NotificationSettings {
    email_enabled: bool,
    admin_notifications: bool,
    error_notifications: bool,
    sync_completion_notifications: bool,
}

// Additional service configuration structures
#[derive(Serialize, Deserialize)]
struct ApiGatewayConfig {
    port: u16,
    cors_origins: Vec<String>,
    rate_limiting: RateLimitConfig,
    authentication: AuthConfig,
}

#[derive(Serialize, Deserialize)]
struct RateLimitConfig {
    enabled: bool,
    requests_per_minute: u32,
    burst_size: u32,
}

#[derive(Serialize, Deserialize)]
struct AuthConfig {
    method: String,
    token_expiry_hours: u32,
}

#[derive(Serialize, Deserialize)]
struct SyncServiceConfig {
    port: u16,
    max_concurrent_syncs: u32,
    sync_timeout_minutes: u32,
    health_check_interval_seconds: u32,
}

#[derive(Serialize, Deserialize)]
struct GisExportServiceConfig {
    port: u16,
    temp_directory: String,
    max_export_size_mb: u32,
    cleanup_interval_hours: u32,
}

// Detailed logging configuration structures
#[derive(Serialize, Deserialize)]
struct LoggingDetailedConfig {
    appenders: AppendersConfig,
    loggers: LoggersConfig,
    root: RootLoggerConfig,
}

#[derive(Serialize, Deserialize)]
struct AppendersConfig {
    console: ConsoleAppenderConfig,
    file: FileAppenderConfig,
}

#[derive(Serialize, Deserialize)]
struct ConsoleAppenderConfig {
    kind: String,
    encoder: EncoderConfig,
}

#[derive(Serialize, Deserialize)]
struct FileAppenderConfig {
    kind: String,
    path: String,
    encoder: EncoderConfig,
    policy: PolicyConfig,
}

#[derive(Serialize, Deserialize)]
struct EncoderConfig {
    pattern: String,
}

#[derive(Serialize, Deserialize)]
struct PolicyConfig {
    kind: String,
    trigger: TriggerConfig,
    roller: RollerConfig,
}

#[derive(Serialize, Deserialize)]
struct TriggerConfig {
    kind: String,
    limit: String,
}

#[derive(Serialize, Deserialize)]
struct RollerConfig {
    kind: String,
    pattern: String,
    count: u32,
}

#[derive(Serialize, Deserialize)]
struct LoggersConfig {
    terrafusion: LoggerConfig,
}

#[derive(Serialize, Deserialize)]
struct LoggerConfig {
    level: String,
    appenders: Vec<String>,
    additive: bool,
}

#[derive(Serialize, Deserialize)]
struct RootLoggerConfig {
    level: String,
    appenders: Vec<String>,
}