use std::fmt;
use thiserror::Error;
use serde::{Serialize, Deserialize};

/// Result type alias with the common Error type
pub type Result<T> = std::result::Result<T, Error>;

/// Common error type for all TerraFusion services
#[derive(Error, Debug)]
pub enum Error {
    /// Database errors
    #[error("Database error: {0}")]
    Database(#[from] DatabaseError),
    
    /// Validation errors
    #[error("Validation error: {0}")]
    Validation(String),
    
    /// Authentication errors
    #[error("Authentication error: {0}")]
    Authentication(String),
    
    /// Authorization errors
    #[error("Authorization error: {0}")]
    Authorization(String),
    
    /// Not found errors
    #[error("Not found: {0}")]
    NotFound(String),
    
    /// Config errors
    #[error("Configuration error: {0}")]
    Config(String),
    
    /// External service errors
    #[error("External service error: {0}")]
    ExternalService(String),
    
    /// Geo processing errors
    #[error("Geo processing error: {0}")]
    GeoProcessing(String),
    
    /// Data sync errors
    #[error("Data sync error: {0}")]
    DataSync(String),
    
    /// Serialization errors
    #[error("Serialization error: {0}")]
    Serialization(String),
    
    /// Internal server errors
    #[error("Internal server error: {0}")]
    Internal(String),
    
    /// SQLx specific database errors
    #[error("SQLx error: {0}")]
    Sqlx(#[from] sqlx::Error),
    
    /// Diesel specific database errors
    #[error("Diesel error: {0}")]
    Diesel(String),
    
    /// IO errors
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    /// HTTP client errors
    #[error("HTTP client error: {0}")]
    HttpClient(#[from] reqwest::Error),
    
    /// Parse errors
    #[error("Parse error: {0}")]
    Parse(String),
}

impl Error {
    /// Get the HTTP status code for this error
    pub fn status_code(&self) -> u16 {
        match self {
            Error::Database(_) => 500,
            Error::Validation(_) => 400,
            Error::Authentication(_) => 401,
            Error::Authorization(_) => 403,
            Error::NotFound(_) => 404,
            Error::Config(_) => 500,
            Error::ExternalService(_) => 502,
            Error::GeoProcessing(_) => 500,
            Error::DataSync(_) => 500,
            Error::Serialization(_) => 500,
            Error::Internal(_) => 500,
            Error::Sqlx(_) => 500,
            Error::Diesel(_) => 500,
            Error::Io(_) => 500,
            Error::HttpClient(_) => 500,
            Error::Parse(_) => 400,
        }
    }
    
    /// Get the error type as a string
    pub fn error_type(&self) -> &str {
        match self {
            Error::Database(_) => "database_error",
            Error::Validation(_) => "validation_error",
            Error::Authentication(_) => "authentication_error",
            Error::Authorization(_) => "authorization_error",
            Error::NotFound(_) => "not_found",
            Error::Config(_) => "configuration_error",
            Error::ExternalService(_) => "external_service_error",
            Error::GeoProcessing(_) => "geo_processing_error",
            Error::DataSync(_) => "data_sync_error",
            Error::Serialization(_) => "serialization_error",
            Error::Internal(_) => "internal_server_error",
            Error::Sqlx(_) => "database_error",
            Error::Diesel(_) => "database_error",
            Error::Io(_) => "io_error",
            Error::HttpClient(_) => "http_client_error",
            Error::Parse(_) => "parse_error",
        }
    }
    
    /// Convert the error to an ErrorResponse
    pub fn to_response(&self) -> ErrorResponse {
        ErrorResponse {
            code: self.status_code(),
            error_type: self.error_type().to_string(),
            message: self.to_string(),
            details: None,
        }
    }
}

/// Database error details
#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Connection error: {0}")]
    Connection(String),
    
    #[error("Query error: {0}")]
    Query(String),
    
    #[error("Transaction error: {0}")]
    Transaction(String),
    
    #[error("Migration error: {0}")]
    Migration(String),
    
    #[error("Constraint violation: {0}")]
    Constraint(String),
    
    #[error("Unique violation: {0}")]
    UniqueViolation(String),
    
    #[error("Foreign key violation: {0}")]
    ForeignKey(String),
    
    #[error("Check violation: {0}")]
    Check(String),
    
    #[error("Not null violation: {0}")]
    NotNull(String),
    
    #[error("Database error: {0}")]
    Other(String),
}

/// Error response for API endpoints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub code: u16,
    #[serde(rename = "type")]
    pub error_type: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<serde_json::Value>,
}

impl fmt::Display for ErrorResponse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.error_type, self.message)
    }
}

/// Helper function to convert sqlx database errors into more specific errors
pub fn map_sqlx_error(error: sqlx::Error) -> Error {
    match &error {
        sqlx::Error::Database(db_error) => {
            // PostgreSQL error codes
            if let Some(code) = db_error.code() {
                let code_str = code.to_string();
                match code_str.as_str() {
                    // Unique violation
                    "23505" => Error::Database(DatabaseError::UniqueViolation(db_error.message().to_string())),
                    // Foreign key violation
                    "23503" => Error::Database(DatabaseError::ForeignKey(db_error.message().to_string())),
                    // Check constraint violation
                    "23514" => Error::Database(DatabaseError::Check(db_error.message().to_string())),
                    // Not null violation
                    "23502" => Error::Database(DatabaseError::NotNull(db_error.message().to_string())),
                    // Other constraint violations
                    "23000" => Error::Database(DatabaseError::Constraint(db_error.message().to_string())),
                    // Connection related
                    "08000" | "08003" | "08006" | "08001" | "08004" => {
                        Error::Database(DatabaseError::Connection(db_error.message().to_string()))
                    }
                    _ => Error::Database(DatabaseError::Other(db_error.message().to_string())),
                }
            } else {
                Error::Database(DatabaseError::Other(db_error.message().to_string()))
            }
        }
        sqlx::Error::RowNotFound => Error::NotFound("Record not found".to_string()),
        sqlx::Error::ColumnNotFound(col) => {
            Error::Database(DatabaseError::Query(format!("Column not found: {}", col)))
        }
        sqlx::Error::ColumnDecode { source, index } => {
            Error::Database(DatabaseError::Query(format!(
                "Error decoding column {}: {}",
                index, source
            )))
        }
        _ => Error::Sqlx(error),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_status_code() {
        assert_eq!(Error::NotFound("test".to_string()).status_code(), 404);
        assert_eq!(Error::Authentication("test".to_string()).status_code(), 401);
        assert_eq!(Error::Authorization("test".to_string()).status_code(), 403);
    }

    #[test]
    fn test_error_to_response() {
        let err = Error::NotFound("Resource not found".to_string());
        let resp = err.to_response();
        
        assert_eq!(resp.code, 404);
        assert_eq!(resp.error_type, "not_found");
        assert_eq!(resp.message, "Not found: Resource not found");
    }
}