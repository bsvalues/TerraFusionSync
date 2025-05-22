use actix_session::Session;
use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage, HttpResponse,
};
use chrono::{Duration, Utc};
use futures::future::{ok, Either, Ready};
use futures::Future;
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::pin::Pin;
use std::rc::Rc;
use std::task::{Context, Poll};

// Public routes that don't require authentication
const PUBLIC_ROUTES: [&str; 8] = [
    "/",
    "/login",
    "/logout",
    "/health",
    "/metrics",
    "/static",
    "/api/v1/status",
    "/api/v1/health",
];

// Define the JWT claims structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,          // Subject (username)
    pub exp: usize,           // Expiration time
    pub iat: usize,           // Issued at
    pub role: String,         // User role
    pub county_id: String,    // County ID
}

// Auth middleware
pub struct AuthMiddleware;

// Middleware factory implementation
impl<S, B> Transform<S, ServiceRequest> for AuthMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = AuthMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ok(AuthMiddlewareService(Rc::new(service)))
    }
}

pub struct AuthMiddlewareService<S>(Rc<S>);

impl<S, B> Service<ServiceRequest> for AuthMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>>>>;

    forward_ready!(S);

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let path = req.path().to_string();
        
        // Check if the path is public
        let is_public = PUBLIC_ROUTES.iter().any(|route| {
            path.starts_with(route)
        });
        
        if is_public {
            // For public routes, pass through without auth check
            let service = Rc::clone(&self.0);
            return Box::pin(async move {
                service.call(req).await
            });
        }
        
        // Check for JWT token in session
        let session = req.get_session();
        let jwt_result = session.get::<String>("jwt");
        
        match jwt_result {
            Ok(Some(token)) => {
                // Validate JWT token
                match validate_token(&token) {
                    Ok(claims) => {
                        // Token is valid, store claims in request extensions
                        req.extensions_mut().insert(claims);
                        
                        // Pass the request to the next middleware/handler
                        let service = Rc::clone(&self.0);
                        Box::pin(async move {
                            service.call(req).await
                        })
                    },
                    Err(_) => {
                        // Token is invalid or expired, redirect to login
                        Box::pin(async {
                            Ok(req.into_response(
                                HttpResponse::Found()
                                    .append_header(("Location", "/login"))
                                    .finish()
                                    .into_body(),
                            ))
                        })
                    }
                }
            },
            _ => {
                // No JWT token found, redirect to login
                Box::pin(async {
                    Ok(req.into_response(
                        HttpResponse::Found()
                            .append_header(("Location", "/login"))
                            .finish()
                            .into_body(),
                    ))
                })
            }
        }
    }
}

// Function to validate a JWT token
pub fn validate_token(token: &str) -> Result<Claims, jsonwebtoken::errors::Error> {
    // In a real implementation, this would use a proper secret key
    let secret = "development_secret_key_change_in_production";
    
    // Decode and validate the token
    let validation = Validation::default();
    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )?;
    
    Ok(token_data.claims)
}

// Function to generate a JWT token
pub fn generate_token(
    username: &str,
    role: &str,
    county_id: &str,
    expiration_minutes: i64,
) -> Result<String, jsonwebtoken::errors::Error> {
    // In a real implementation, this would use a proper secret key
    let secret = "development_secret_key_change_in_production";
    
    let now = Utc::now();
    let expiration = now + Duration::minutes(expiration_minutes);
    
    let claims = Claims {
        sub: username.to_string(),
        exp: expiration.timestamp() as usize,
        iat: now.timestamp() as usize,
        role: role.to_string(),
        county_id: county_id.to_string(),
    };
    
    // Encode the token
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
}