use std::fmt;

// Define a common Result type for our application
pub type Result<T> = std::result::Result<T, Error>;

// Define the application's error types
#[derive(Debug)]
pub enum Error {
    ConfigError(String),
    DatabaseError(String),
    NotFound(String),
    InvalidInput(String),
    Unauthorized(String),
    Forbidden(String),
    GisProcessing(String),
    TelemetryError(String),
    Validation(String),
    Internal(String),
    External(String),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::ConfigError(msg) => write!(f, "Configuration error: {}", msg),
            Error::DatabaseError(msg) => write!(f, "Database error: {}", msg),
            Error::NotFound(msg) => write!(f, "Not found: {}", msg),
            Error::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            Error::Unauthorized(msg) => write!(f, "Unauthorized: {}", msg),
            Error::Forbidden(msg) => write!(f, "Forbidden: {}", msg),
            Error::GisProcessing(msg) => write!(f, "GIS processing error: {}", msg),
            Error::TelemetryError(msg) => write!(f, "Telemetry error: {}", msg),
            Error::Validation(msg) => write!(f, "Validation error: {}", msg),
            Error::Internal(msg) => write!(f, "Internal error: {}", msg),
            Error::External(msg) => write!(f, "External error: {}", msg),
        }
    }
}

impl std::error::Error for Error {}

// Implement From traits for common error conversions
impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        Error::Internal(format!("IO error: {}", err))
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        Error::Internal(format!("JSON error: {}", err))
    }
}

impl From<diesel::result::Error> for Error {
    fn from(err: diesel::result::Error) -> Self {
        match err {
            diesel::result::Error::NotFound => {
                Error::NotFound("Record not found".to_string())
            }
            _ => Error::DatabaseError(format!("Database error: {}", err)),
        }
    }
}

impl From<actix_web::Error> for Error {
    fn from(err: actix_web::Error) -> Self {
        Error::Internal(format!("Actix error: {}", err))
    }
}

// Conversion from our Error type to actix_web::Error for response handlers
impl actix_web::ResponseError for Error {
    fn status_code(&self) -> actix_web::http::StatusCode {
        use actix_web::http::StatusCode;
        
        match self {
            Error::NotFound(_) => StatusCode::NOT_FOUND,
            Error::InvalidInput(_) => StatusCode::BAD_REQUEST,
            Error::Unauthorized(_) => StatusCode::UNAUTHORIZED,
            Error::Forbidden(_) => StatusCode::FORBIDDEN,
            Error::Validation(_) => StatusCode::BAD_REQUEST,
            Error::ConfigError(_) | Error::DatabaseError(_) | Error::Internal(_) | Error::GisProcessing(_) | Error::TelemetryError(_) => {
                StatusCode::INTERNAL_SERVER_ERROR
            }
            Error::External(_) => StatusCode::BAD_GATEWAY,
        }
    }
}