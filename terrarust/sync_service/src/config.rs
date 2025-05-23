use std::env;
use std::time::Duration;

/// Configuration for the Sync Service
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
    
    // Sync configuration
    pub sync_batch_size: usize,
    pub sync_timeout_seconds: u64,
    pub max_concurrent_syncs: usize,
    pub retry_attempts: u32,
    pub retry_delay_seconds: u64,
    
    // Scheduler configuration
    pub scheduler_enabled: bool,
    pub scheduler_interval_seconds: u64,
    pub cleanup_interval_hours: u64,
    
    // Metrics configuration
    pub metrics_enabled: bool,
    pub metrics_port: u16,
}

impl Config {
    /// Create a new Config from environment variables
    pub fn from_env() -> Self {
        let host = env::var("SYNC_SERVICE_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = env::var("SYNC_SERVICE_PORT")
            .unwrap_or_else(|_| "8001".to_string())
            .parse::<u16>()
            .expect("SYNC_SERVICE_PORT must be a valid port number");
        
        let worker_threads = env::var("SYNC_SERVICE_WORKERS")
            .unwrap_or_else(|_| num_cpus::get().to_string())
            .parse::<usize>()
            .expect("SYNC_SERVICE_WORKERS must be a valid integer");
        
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
            .unwrap_or_else(|_| "10".to_string())
            .parse::<u32>()
            .expect("DATABASE_POOL_SIZE must be a valid integer");
        
        // Sync configuration
        let sync_batch_size = env::var("SYNC_BATCH_SIZE")
            .unwrap_or_else(|_| "100".to_string())
            .parse::<usize>()
            .expect("SYNC_BATCH_SIZE must be a valid integer");
        
        let sync_timeout_seconds = env::var("SYNC_TIMEOUT_SECONDS")
            .unwrap_or_else(|_| "3600".to_string())
            .parse::<u64>()
            .expect("SYNC_TIMEOUT_SECONDS must be a valid integer");
        
        let max_concurrent_syncs = env::var("MAX_CONCURRENT_SYNCS")
            .unwrap_or_else(|_| "5".to_string())
            .parse::<usize>()
            .expect("MAX_CONCURRENT_SYNCS must be a valid integer");
        
        let retry_attempts = env::var("SYNC_RETRY_ATTEMPTS")
            .unwrap_or_else(|_| "3".to_string())
            .parse::<u32>()
            .expect("SYNC_RETRY_ATTEMPTS must be a valid integer");
        
        let retry_delay_seconds = env::var("SYNC_RETRY_DELAY_SECONDS")
            .unwrap_or_else(|_| "60".to_string())
            .parse::<u64>()
            .expect("SYNC_RETRY_DELAY_SECONDS must be a valid integer");
        
        // Scheduler configuration
        let scheduler_enabled = env::var("SCHEDULER_ENABLED")
            .unwrap_or_else(|_| "true".to_string())
            .parse::<bool>()
            .expect("SCHEDULER_ENABLED must be true or false");
        
        let scheduler_interval_seconds = env::var("SCHEDULER_INTERVAL_SECONDS")
            .unwrap_or_else(|_| "60".to_string())
            .parse::<u64>()
            .expect("SCHEDULER_INTERVAL_SECONDS must be a valid integer");
        
        let cleanup_interval_hours = env::var("CLEANUP_INTERVAL_HOURS")
            .unwrap_or_else(|_| "24".to_string())
            .parse::<u64>()
            .expect("CLEANUP_INTERVAL_HOURS must be a valid integer");
        
        // Metrics configuration
        let metrics_enabled = env::var("METRICS_ENABLED")
            .unwrap_or_else(|_| "true".to_string())
            .parse::<bool>()
            .expect("METRICS_ENABLED must be true or false");
        
        let metrics_port = env::var("METRICS_PORT")
            .unwrap_or_else(|_| "9090".to_string())
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
            sync_batch_size,
            sync_timeout_seconds,
            max_concurrent_syncs,
            retry_attempts,
            retry_delay_seconds,
            scheduler_enabled,
            scheduler_interval_seconds,
            cleanup_interval_hours,
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
    
    /// Get sync timeout as Duration
    pub fn sync_timeout(&self) -> Duration {
        Duration::from_secs(self.sync_timeout_seconds)
    }
    
    /// Get retry delay as Duration
    pub fn retry_delay(&self) -> Duration {
        Duration::from_secs(self.retry_delay_seconds)
    }
    
    /// Get scheduler interval as Duration
    pub fn scheduler_interval(&self) -> Duration {
        Duration::from_secs(self.scheduler_interval_seconds)
    }
    
    /// Get cleanup interval as Duration
    pub fn cleanup_interval(&self) -> Duration {
        Duration::from_secs(self.cleanup_interval_hours * 3600)
    }
}