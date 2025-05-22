use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use common::utils::jwt::{Claims, validate_token};
use futures::future::{ready, LocalBoxFuture, Ready};
use std::future::Future;
use std::pin::Pin;
use std::rc::Rc;
use std::task::{Context, Poll};

// Define user info struct that will be attached to requests
pub struct UserInfo {
    pub user_id: String,
    pub name: Option<String>,
    pub email: Option<String>,
    pub roles: Vec<String>,
    pub counties: Vec<String>,
}

// Paths that don't require authentication
const PUBLIC_PATHS: [&str; 3] = [
    "/health",
    "/metrics",
    "/api/auth/login",
];

pub struct AuthMiddleware {
    jwt_secret: String,
}

impl AuthMiddleware {
    pub fn new(jwt_secret: String) -> Self {
        Self { jwt_secret }
    }
}

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
        ready(Ok(AuthMiddlewareService {
            service: Rc::new(service),
            jwt_secret: self.jwt_secret.clone(),
        }))
    }
}

pub struct AuthMiddlewareService<S> {
    service: Rc<S>,
    jwt_secret: String,
}

impl<S, B> Service<ServiceRequest> for AuthMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    forward_ready!(service);

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let is_public_path = PUBLIC_PATHS.iter().any(|path| {
            req.path().starts_with(path)
        });
        
        // Skip auth for public paths
        if is_public_path {
            let service = Rc::clone(&self.service);
            return Box::pin(async move {
                service.call(req).await
            });
        }
        
        // Extract JWT token from header
        let auth_header = req.headers().get("Authorization");
        let jwt_secret = self.jwt_secret.clone();
        let service = Rc::clone(&self.service);
        
        Box::pin(async move {
            if let Some(header_value) = auth_header {
                if let Ok(header_str) = header_value.to_str() {
                    if header_str.starts_with("Bearer ") {
                        let token = header_str.trim_start_matches("Bearer ").trim();
                        
                        match validate_token(token, &jwt_secret) {
                            Ok(claims) => {
                                // Set user info in request extensions
                                req.extensions_mut().insert(UserInfo {
                                    user_id: claims.sub,
                                    name: claims.name,
                                    email: claims.email,
                                    roles: claims.roles,
                                    counties: claims.counties,
                                });
                                
                                return service.call(req).await;
                            }
                            Err(e) => {
                                return Ok(req.error_response(actix_web::error::ErrorUnauthorized(
                                    format!("Invalid token: {}", e),
                                )));
                            }
                        }
                    }
                }
            }
            
            // No token or invalid format
            Ok(req.error_response(actix_web::error::ErrorUnauthorized(
                "Authorization header missing or invalid format",
            )))
        })
    }
}