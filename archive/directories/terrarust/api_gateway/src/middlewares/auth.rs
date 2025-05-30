use std::future::{ready, Ready};
use std::rc::Rc;
use std::task::{Context, Poll};
use actix_web::{
    dev::{Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use futures_util::future::LocalBoxFuture;
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};
use crate::errors::AppError;
use serde::{Deserialize, Serialize};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use actix_web::http::header;

/// AuthMiddleware for handling JWT-based authentication
pub struct AuthMiddleware {
    pub exclude_paths: Vec<String>,
}

impl Default for AuthMiddleware {
    fn default() -> Self {
        Self {
            exclude_paths: vec![
                "/".to_string(),
                "/login".to_string(),
                "/logout".to_string(),
                "/static".to_string(),
                "/api/v1/auth".to_string(),
                "/system/health".to_string(),
                "/system/metrics".to_string(),
            ],
        }
    }
}

impl<S, B> Transform<S, ServiceRequest> for AuthMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = AuthMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(AuthMiddlewareService {
            service: Rc::new(service),
            exclude_paths: self.exclude_paths.clone(),
        }))
    }
}

pub struct AuthMiddlewareService<S> {
    service: Rc<S>,
    exclude_paths: Vec<String>,
}

impl<S, B> Service<ServiceRequest> for AuthMiddlewareService<S>
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
        
        // Skip authentication for excluded paths
        if self.should_skip_auth(&path) {
            let fut = self.service.call(req);
            return Box::pin(async move {
                let res = fut.await?;
                Ok(res)
            });
        }
        
        // Check for JWT token in headers or cookies
        let token = self.extract_token(&req);
        
        match token {
            Some(token) => {
                // Validate the token
                match self.validate_token(&token) {
                    Ok(claims) => {
                        // Store user info in request extensions
                        req.extensions_mut().insert(claims);
                        let fut = self.service.call(req);
                        Box::pin(async move {
                            let res = fut.await?;
                            Ok(res)
                        })
                    }
                    Err(err) => {
                        // Invalid token
                        let error = AppError::Authentication(format!("Invalid token: {}", err));
                        Box::pin(async move { Err(error.into()) })
                    }
                }
            }
            None => {
                // No token found, redirect to login or return unauthorized
                if req.path().starts_with("/api/") {
                    // For API requests, return 401 Unauthorized
                    let error = AppError::Authentication("Authentication required".to_string());
                    Box::pin(async move { Err(error.into()) })
                } else {
                    // For UI requests, redirect to login
                    let fut = self.service.call(req);
                    Box::pin(async move {
                        let res = fut.await?;
                        // TODO: Implement redirect to login page
                        Ok(res)
                    })
                }
            }
        }
    }
}

impl<S> AuthMiddlewareService<S> {
    /// Check if authentication should be skipped for this path
    fn should_skip_auth(&self, path: &str) -> bool {
        self.exclude_paths.iter().any(|excluded| path.starts_with(excluded))
    }
    
    /// Extract JWT token from request headers or cookies
    fn extract_token(&self, req: &ServiceRequest) -> Option<String> {
        // First try Authorization header
        if let Some(auth_header) = req.headers().get(header::AUTHORIZATION) {
            if let Ok(auth_str) = auth_header.to_str() {
                if auth_str.starts_with("Bearer ") {
                    return Some(auth_str[7..].to_string());
                }
            }
        }
        
        // Then try from cookies
        if let Some(cookie) = req.cookie("token") {
            return Some(cookie.value().to_string());
        }
        
        None
    }
    
    /// Validate JWT token and extract claims
    fn validate_token(&self, token: &str) -> Result<Claims, String> {
        // TODO: Get JWT secret from config
        let jwt_secret = std::env::var("JWT_SECRET").unwrap_or_else(|_| "default_secret_for_development".to_string());
        
        let validation = Validation::new(Algorithm::HS256);
        match decode::<Claims>(
            token,
            &DecodingKey::from_secret(jwt_secret.as_bytes()),
            &validation,
        ) {
            Ok(token_data) => Ok(token_data.claims),
            Err(err) => Err(err.to_string()),
        }
    }
}

/// JWT Claims structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,         // Subject (typically user ID)
    pub name: String,        // User's name
    pub email: String,       // User's email
    pub roles: Vec<String>,  // User's roles
    pub county_id: String,   // User's county ID
    pub exp: u64,            // Expiration time (Unix timestamp)
    pub iat: u64,            // Issued at time (Unix timestamp)
}

impl Claims {
    /// Create new claims for a user
    pub fn new(
        user_id: &str,
        name: &str,
        email: &str,
        roles: Vec<String>,
        county_id: &str,
        expiry: Duration,
    ) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        Self {
            sub: user_id.to_string(),
            name: name.to_string(),
            email: email.to_string(),
            roles,
            county_id: county_id.to_string(),
            exp: now + expiry.as_secs(),
            iat: now,
        }
    }
    
    /// Check if the user has a specific role
    pub fn has_role(&self, role: &str) -> bool {
        self.roles.contains(&role.to_string())
    }
    
    /// Check if the claims have expired
    pub fn is_expired(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        self.exp < now
    }
}