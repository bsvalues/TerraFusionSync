use std::future::{ready, Ready};
use std::rc::Rc;
use std::task::{Context, Poll};
use actix_web::{
    dev::{Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use actix_web::http::header;
use futures_util::future::LocalBoxFuture;
use crate::errors::AppError;

/// Middleware for API key authentication on API routes
pub struct ApiKeyMiddleware {
    pub exclude_paths: Vec<String>,
}

impl Default for ApiKeyMiddleware {
    fn default() -> Self {
        Self {
            exclude_paths: vec![
                "/api/v1/auth".to_string(),
                "/api/v1/health".to_string(),
                "/api/v1/metrics".to_string(),
            ],
        }
    }
}

impl<S, B> Transform<S, ServiceRequest> for ApiKeyMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = ApiKeyMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(ApiKeyMiddlewareService {
            service: Rc::new(service),
            exclude_paths: self.exclude_paths.clone(),
        }))
    }
}

pub struct ApiKeyMiddlewareService<S> {
    service: Rc<S>,
    exclude_paths: Vec<String>,
}

impl<S, B> Service<ServiceRequest> for ApiKeyMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.service.poll_ready(cx)
    }

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let path = req.path().to_string();
        
        // Skip API key check for excluded paths
        if self.should_skip_api_key_check(&path) {
            let fut = self.service.call(req);
            return Box::pin(async move {
                let res = fut.await?;
                Ok(res)
            });
        }
        
        // Check for API key in headers
        match self.validate_api_key(&req) {
            Ok(api_key_info) => {
                // Store API key info in request extensions
                req.extensions_mut().insert(api_key_info);
                let fut = self.service.call(req);
                Box::pin(async move {
                    let res = fut.await?;
                    Ok(res)
                })
            }
            Err(err) => {
                Box::pin(async move { Err(err.into()) })
            }
        }
    }
}

impl<S> ApiKeyMiddlewareService<S> {
    /// Check if API key validation should be skipped for this path
    fn should_skip_api_key_check(&self, path: &str) -> bool {
        // Check if path starts with any excluded path
        self.exclude_paths.iter().any(|excluded| path.starts_with(excluded))
    }
    
    /// Validate API key from request headers
    fn validate_api_key(&self, req: &ServiceRequest) -> Result<ApiKeyInfo, AppError> {
        // First look for API key in X-API-KEY header
        let api_key = if let Some(key) = req.headers().get("X-API-KEY") {
            if let Ok(key_str) = key.to_str() {
                Some(key_str.to_string())
            } else {
                None
            }
        } else {
            // Then try to get from authorization header with "ApiKey" prefix
            if let Some(auth) = req.headers().get(header::AUTHORIZATION) {
                if let Ok(auth_str) = auth.to_str() {
                    if auth_str.starts_with("ApiKey ") {
                        Some(auth_str[7..].to_string())
                    } else {
                        None
                    }
                } else {
                    None
                }
            } else {
                None
            }
        };
        
        // If no API key found, return error
        let api_key = api_key.ok_or_else(|| {
            AppError::Authentication("API key required".to_string())
        })?;
        
        // TODO: Implement actual API key validation against database
        // For now, accept any non-empty API key for development
        if api_key.is_empty() {
            return Err(AppError::Authentication("Invalid API key".to_string()));
        }
        
        // Create and return API key info
        Ok(ApiKeyInfo {
            key: api_key,
            client_id: "development".to_string(),
            client_name: "Development Client".to_string(),
            scopes: vec!["read".to_string(), "write".to_string()],
        })
    }
}

/// API key information stored in request extensions
#[derive(Debug, Clone)]
pub struct ApiKeyInfo {
    pub key: String,
    pub client_id: String,
    pub client_name: String,
    pub scopes: Vec<String>,
}

impl ApiKeyInfo {
    /// Check if the API key has a specific scope
    pub fn has_scope(&self, scope: &str) -> bool {
        self.scopes.contains(&scope.to_string())
    }
}