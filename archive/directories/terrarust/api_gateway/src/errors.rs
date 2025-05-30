use actix_web::{HttpResponse, ResponseError};
use thiserror::Error;
use handlebars::RenderError;
use serde_json::{json, Value};
use std::fmt;
use actix_http::StatusCode;

/// Main application error type
#[derive(Error, Debug)]
pub enum AppError {
    #[error("Authentication error: {0}")]
    Authentication(String),
    
    #[error("Authorization error: {0}")]
    Authorization(String),
    
    #[error("Bad request: {0}")]
    BadRequest(String),
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("Internal server error: {0}")]
    InternalServerError(String),
    
    #[error("Not found: {0}")]
    NotFound(String),
    
    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),
    
    #[error("Template rendering error: {0}")]
    TemplateError(#[from] RenderError),
    
    #[error("Validation error: {0}")]
    Validation(String),
    
    #[error("External service error: {0}")]
    ExternalService(String),
}

impl ResponseError for AppError {
    fn error_response(&self) -> HttpResponse {
        let status_code = self.status_code();
        
        // Create common error response structure
        let error_response = json!({
            "error": {
                "code": status_code.as_u16(),
                "message": self.to_string(),
                "type": self.error_type(),
            }
        });
        
        HttpResponse::build(status_code)
            .content_type("application/json")
            .json(error_response)
    }
    
    fn status_code(&self) -> StatusCode {
        match self {
            AppError::Authentication(_) => StatusCode::UNAUTHORIZED,
            AppError::Authorization(_) => StatusCode::FORBIDDEN,
            AppError::BadRequest(_) => StatusCode::BAD_REQUEST,
            AppError::Database(_) => StatusCode::INTERNAL_SERVER_ERROR,
            AppError::InternalServerError(_) => StatusCode::INTERNAL_SERVER_ERROR,
            AppError::NotFound(_) => StatusCode::NOT_FOUND,
            AppError::ServiceUnavailable(_) => StatusCode::SERVICE_UNAVAILABLE,
            AppError::TemplateError(_) => StatusCode::INTERNAL_SERVER_ERROR,
            AppError::Validation(_) => StatusCode::BAD_REQUEST,
            AppError::ExternalService(_) => StatusCode::BAD_GATEWAY,
        }
    }
}

impl AppError {
    /// Get the error type as a string
    pub fn error_type(&self) -> &'static str {
        match self {
            AppError::Authentication(_) => "authentication_error",
            AppError::Authorization(_) => "authorization_error",
            AppError::BadRequest(_) => "bad_request",
            AppError::Database(_) => "database_error",
            AppError::InternalServerError(_) => "internal_server_error",
            AppError::NotFound(_) => "not_found",
            AppError::ServiceUnavailable(_) => "service_unavailable",
            AppError::TemplateError(_) => "template_error",
            AppError::Validation(_) => "validation_error",
            AppError::ExternalService(_) => "external_service_error",
        }
    }
    
    /// Create an error response for HTML templates
    pub fn to_html_response(&self) -> HttpResponse {
        let status = self.status_code();
        
        // For HTML responses, create a user-friendly error page
        let body = format!(
            r#"<!DOCTYPE html>
            <html>
            <head>
                <title>Error {}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
                    .error-container {{ max-width: 800px; margin: 40px auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                    .error-title {{ color: #d9534f; }}
                    .error-message {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #d9534f; }}
                    .back-link {{ display: inline-block; margin-top: 20px; color: #0275d8; text-decoration: none; }}
                    .back-link:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1 class="error-title">Error {}</h1>
                    <div class="error-message">
                        <p>{}</p>
                    </div>
                    <a href="/" class="back-link">← Back to Home</a>
                </div>
            </body>
            </html>"#,
            status.as_u16(),
            status.as_u16(),
            self.to_string()
        );
        
        HttpResponse::build(status)
            .content_type("text/html; charset=utf-8")
            .body(body)
    }
}

/// Result type alias with AppError
pub type AppResult<T> = Result<T, AppError>;

/// API error response
#[derive(Debug, serde::Serialize)]
pub struct ApiErrorResponse {
    pub error: ApiError,
}

/// API error details
#[derive(Debug, serde::Serialize)]
pub struct ApiError {
    pub code: u16,
    pub message: String,
    #[serde(rename = "type")]
    pub error_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<Value>,
}