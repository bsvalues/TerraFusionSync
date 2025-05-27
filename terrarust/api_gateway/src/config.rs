use std::env;
use std::time::Duration;

/// Configuration for the API Gateway application
#[derive(Debug, Clone)]
pub struct AppConfig {
    // Server configuration
    pub host: String,
    pub port: u16,
    pub worker_threads: usize,
    pub environment: String,
    
    // Security configuration
    pub use_ssl: bool,
    pub ssl_cert_file: String,
    pub ssl_key_file: String,
    pub jwt_secret: String,
    pub jwt_expiry: Duration,
    pub allowed_origins: Vec<String>,
    
    // Service URLs
    pub sync_service_url: String,
    pub gis_export_service_url: String,
    
    // Database configuration
    pub database_url: String,
    pub database_pool_size: u32,
    
    // Session configuration
    pub session_secret: String,
    pub session_expiry: Duration,
    pub cookie_secure: bool,
    
    // Logging configuration
    pub log_format: String,
    pub log_level: String,
    
    // Metrics configuration
    pub metrics_enabled: bool,
    pub metrics_interval: Duration,
}

impl AppConfig {
    /// Create a new AppConfig from environment variables
    pub fn from_env() -> Self {
        let host = env::var("API_GATEWAY_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = env::var("API_GATEWAY_PORT")
            .unwrap_or_else(|_| "6000".to_string())
            .parse::<u16>()
            .expect("API_GATEWAY_PORT must be a valid port number");
        
        let worker_threads = env::var("API_GATEWAY_WORKERS")
            .unwrap_or_else(|_| num_cpus::get().to_string())
            .parse::<usize>()
            .expect("API_GATEWAY_WORKERS must be a valid integer");
        
        let environment = env::var("ENVIRONMENT").unwrap_or_else(|_| "development".to_string());
        
        // Security configuration
        let use_ssl = env::var("USE_SSL")
            .unwrap_or_else(|_| "false".to_string())
            .parse::<bool>()
            .expect("USE_SSL must be true or false");
        
        let ssl_cert_file = env::var("SSL_CERT_FILE").unwrap_or_else(|_| "certs/server.crt".to_string());
        let ssl_key_file = env::var("SSL_KEY_FILE").unwrap_or_else(|_| "certs/server.key".to_string());
        
        let jwt_secret = env::var("JWT_SECRET").expect("JWT_SECRET is required");
        let jwt_expiry_hours = env::var("JWT_EXPIRY_HOURS")
            .unwrap_or_else(|_| "24".to_string())
            .parse::<u64>()
            .expect("JWT_EXPIRY_HOURS must be a valid integer");
        
        let allowed_origins_str = env::var("ALLOWED_ORIGINS").unwrap_or_else(|_| "*".to_string());
        let allowed_origins = allowed_origins_str
            .split(',')
            .map(|s| s.trim().to_string())
            .collect();
        
        // Service URLs
        let sync_service_url = env::var("SYNC_SERVICE_URL")
            .unwrap_or_else(|_| "http://localhost:8001".to_string());
        
        let gis_export_service_url = env::var("GIS_EXPORT_SERVICE_URL")
            .unwrap_or_else(|_| "http://localhost:8002".to_string());
        
        // Database configuration
        let database_url = env::var("DATABASE_URL").expect("DATABASE_URL is required");
        let database_pool_size = env::var("DATABASE_POOL_SIZE")
            .unwrap_or_else(|_| "5".to_string())
            .parse::<u32>()
            .expect("DATABASE_POOL_SIZE must be a valid integer");
        
        // Session configuration
        let session_secret = env::var("SESSION_SECRET").expect("SESSION_SECRET is required");
        let session_expiry_hours = env::var("SESSION_EXPIRY_HOURS")
            .unwrap_or_else(|_| "24".to_string())
            .parse::<u64>()
            .expect("SESSION_EXPIRY_HOURS must be a valid integer");
        
        let cookie_secure = env::var("COOKIE_SECURE")
            .unwrap_or_else(|_| (environment == "production").to_string())
            .parse::<bool>()
            .expect("COOKIE_SECURE must be true or false");
        
        // Logging configuration
        let log_format = env::var("LOG_FORMAT").unwrap_or_else(|_| "json".to_string());
        let log_level = env::var("LOG_LEVEL").unwrap_or_else(|_| "info".to_string());
        
        // Metrics configuration
        let metrics_enabled = env::var("METRICS_ENABLED")
            .unwrap_or_else(|_| "true".to_string())
            .parse::<bool>()
            .expect("METRICS_ENABLED must be true or false");
        
        let metrics_interval_secs = env::var("METRICS_INTERVAL_SECS")
            .unwrap_or_else(|_| "60".to_string())
            .parse::<u64>()
            .expect("METRICS_INTERVAL_SECS must be a valid integer");
        
        Self {
            host,
            port,
            worker_threads,
            environment,
            use_ssl,
            ssl_cert_file,
            ssl_key_file,
            jwt_secret,
            jwt_expiry: Duration::from_secs(jwt_expiry_hours * 3600),
            allowed_origins,
            sync_service_url,
            gis_export_service_url,
            database_url,
            database_pool_size,
            session_secret,
            session_expiry: Duration::from_secs(session_expiry_hours * 3600),
            cookie_secure,
            log_format,
            log_level,
            metrics_enabled,
            metrics_interval: Duration::from_secs(metrics_interval_secs),
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
    
    /// Get the domain for cookies
    pub fn cookie_domain(&self) -> Option<String> {
        if self.host == "0.0.0.0" || self.host == "127.0.0.1" || self.host == "localhost" {
            None
        } else {
            Some(self.host.clone())
        }
    }
}