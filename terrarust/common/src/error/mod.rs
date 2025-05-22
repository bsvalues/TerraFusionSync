use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Database error: {0}")]
    Database(#[from] diesel::result::Error),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Environment error: {0}")]
    Env(#[from] std::env::VarError),
    
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("GIS processing error: {0}")]
    GisProcessing(String),
    
    #[error("Sync operation error: {0}")]
    SyncOperation(String),
    
    #[error("Authentication error: {0}")]
    Authentication(String),
    
    #[error("Authorization error: {0}")]
    Authorization(String),
    
    #[error("Not found: {0}")]
    NotFound(String),
    
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    #[error("Internal server error: {0}")]
    InternalServer(String),
}

pub type Result<T> = std::result::Result<T, Error>;