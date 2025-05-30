use std::env;
use std::path::PathBuf;

/// Configuration for the GIS Export Service
#[derive(Debug, Clone)]
pub struct Config {
    // Server configuration
    pub host: String,
    pub port: u16,
    pub worker_threads: usize,
    pub environment: String,
    
    // Security configuration
    pub use_ssl: bool,
    pub ssl_cert_file: String,
    pub ssl_key_file: String,
    
    // Database configuration
    pub database_url: String,
    pub database_pool_size: u32,
    
    // Export configuration
    pub exports_directory: PathBuf,
    pub temp_directory: PathBuf,
    pub max_export_size_mb: u64,
    pub export_timeout_minutes: u64,
    pub cleanup_age_hours: u64,
    
    // GDAL configuration
    pub gdal_data_path: Option<String>,
    pub proj_lib_path: Option<String>,
    
    // Metrics configuration
    pub metrics_enabled: bool,
    pub metrics_port: u16,
}

impl Config {
    /// Create a new Config from environment variables
    pub fn from_env() -> Self {
        let host = env::var("GIS_EXPORT_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = env::var("GIS_EXPORT_PORT")
            .unwrap_or_else(|_| "8002".to_string())
            .parse::<u16>()
            .expect("GIS_EXPORT_PORT must be a valid port number");
        
        let worker_threads = env::var("GIS_EXPORT_WORKERS")
            .unwrap_or_else(|_| num_cpus::get().to_string())
            .parse::<usize>()
            .expect("GIS_EXPORT_WORKERS must be a valid integer");
        
        let environment = env::var("ENVIRONMENT").unwrap_or_else(|_| "development".to_string());
        
        // Security configuration
        let use_ssl = env::var("USE_SSL")
            .unwrap_or_else(|_| "false".to_string())
            .parse::<bool>()
            .expect("USE_SSL must be true or false");
        
        let ssl_cert_file = env::var("SSL_CERT_FILE").unwrap_or_else(|_| "certs/server.crt".to_string());
        let ssl_key_file = env::var("SSL_KEY_FILE").unwrap_or_else(|_| "certs/server.key".to_string());
        
        // Database configuration
        let database_url = env::var("DATABASE_URL").expect("DATABASE_URL is required");
        let database_pool_size = env::var("DATABASE_POOL_SIZE")
            .unwrap_or_else(|_| "5".to_string())
            .parse::<u32>()
            .expect("DATABASE_POOL_SIZE must be a valid integer");
        
        // Export configuration
        let exports_directory = env::var("EXPORTS_DIRECTORY")
            .unwrap_or_else(|_| "./exports".to_string())
            .into();
        
        let temp_directory = env::var("TEMP_DIRECTORY")
            .unwrap_or_else(|_| "./temp".to_string())
            .into();
        
        let max_export_size_mb = env::var("MAX_EXPORT_SIZE_MB")
            .unwrap_or_else(|_| "1024".to_string())
            .parse::<u64>()
            .expect("MAX_EXPORT_SIZE_MB must be a valid integer");
        
        let export_timeout_minutes = env::var("EXPORT_TIMEOUT_MINUTES")
            .unwrap_or_else(|_| "30".to_string())
            .parse::<u64>()
            .expect("EXPORT_TIMEOUT_MINUTES must be a valid integer");
        
        let cleanup_age_hours = env::var("CLEANUP_AGE_HOURS")
            .unwrap_or_else(|_| "24".to_string())
            .parse::<u64>()
            .expect("CLEANUP_AGE_HOURS must be a valid integer");
        
        // GDAL configuration
        let gdal_data_path = env::var("GDAL_DATA").ok();
        let proj_lib_path = env::var("PROJ_LIB").ok();
        
        // Metrics configuration
        let metrics_enabled = env::var("METRICS_ENABLED")
            .unwrap_or_else(|_| "true".to_string())
            .parse::<bool>()
            .expect("METRICS_ENABLED must be true or false");
        
        let metrics_port = env::var("METRICS_PORT")
            .unwrap_or_else(|_| "9092".to_string())
            .parse::<u16>()
            .expect("METRICS_PORT must be a valid port number");
        
        Self {
            host,
            port,
            worker_threads,
            environment,
            use_ssl,
            ssl_cert_file,
            ssl_key_file,
            database_url,
            database_pool_size,
            exports_directory,
            temp_directory,
            max_export_size_mb,
            export_timeout_minutes,
            cleanup_age_hours,
            gdal_data_path,
            proj_lib_path,
            metrics_enabled,
            metrics_port,
        }
    }
    
    /// Check if the application is running in development mode
    pub fn is_development(&self) -> bool {
        self.environment == "development"
    }
    
    /// Check if the application is running in production mode
    pub fn is_production(&self) -> bool {
        self.environment == "production"
    }
    
    /// Get the server address string
    pub fn server_addr(&self) -> String {
        format!("{}:{}", self.host, self.port)
    }
    
    /// Get export timeout as Duration
    pub fn export_timeout(&self) -> std::time::Duration {
        std::time::Duration::from_secs(self.export_timeout_minutes * 60)
    }
    
    /// Get cleanup age as Duration
    pub fn cleanup_age(&self) -> std::time::Duration {
        std::time::Duration::from_secs(self.cleanup_age_hours * 3600)
    }
    
    /// Get maximum export size in bytes
    pub fn max_export_size_bytes(&self) -> u64 {
        self.max_export_size_mb * 1024 * 1024
    }
    
    /// Ensure required directories exist
    pub fn ensure_directories(&self) -> Result<(), std::io::Error> {
        std::fs::create_dir_all(&self.exports_directory)?;
        std::fs::create_dir_all(&self.temp_directory)?;
        Ok(())
    }
}