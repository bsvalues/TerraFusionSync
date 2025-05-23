use std::future::{ready, Ready};
use std::rc::Rc;
use std::task::{Context, Poll};
use std::time::Instant;
use actix_web::{
    dev::{Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use futures_util::future::LocalBoxFuture;
use log::{debug, info, warn, error};
use serde_json::json;

/// Enhanced logging middleware beyond the standard Actix logger
pub struct LoggingMiddleware {
    pub log_request_body: bool,
    pub log_response_body: bool,
    pub max_body_size: usize,
}

impl Default for LoggingMiddleware {
    fn default() -> Self {
        Self {
            log_request_body: false,
            log_response_body: false,
            max_body_size: 1024, // 1KB max logged body size
        }
    }
}

impl<S, B> Transform<S, ServiceRequest> for LoggingMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = LoggingMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(LoggingMiddlewareService {
            service: Rc::new(service),
            log_request_body: self.log_request_body,
            log_response_body: self.log_response_body,
            max_body_size: self.max_body_size,
        }))
    }
}

pub struct LoggingMiddlewareService<S> {
    service: Rc<S>,
    log_request_body: bool,
    log_response_body: bool,
    max_body_size: usize,
}

impl<S, B> Service<ServiceRequest> for LoggingMiddlewareService<S>
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
        // Create a request ID or get it from headers if it exists
        let request_id = req
            .headers()
            .get("X-Request-ID")
            .and_then(|h| h.to_str().ok())
            .unwrap_or_else(|| {
                // Generate a random request ID
                let uuid = uuid::Uuid::new_v4().to_string();
                req.extensions_mut().insert(RequestId(uuid.clone()));
                &uuid
            })
            .to_string();
        
        // Start timing the request
        let start_time = Instant::now();
        
        // Get request data
        let method = req.method().to_string();
        let path = req.path().to_string();
        let remote_addr = req
            .connection_info()
            .realip_remote_addr()
            .unwrap_or("unknown")
            .to_string();
        
        // Get user info if available
        let user_id = if let Some(claims) = req.extensions().get::<crate::middlewares::auth::Claims>() {
            Some(claims.sub.clone())
        } else {
            None
        };
        
        // Log request start
        info!(
            "Request started: {} {} from {} [{}]{}",
            method,
            path,
            remote_addr,
            request_id,
            if let Some(id) = &user_id {
                format!(" user={}", id)
            } else {
                String::new()
            }
        );
        
        // TODO: Log request body if enabled
        // This requires more complex body extraction and would need to modify the request
        
        // Clone values needed in the future
        let method_clone = method.clone();
        let path_clone = path.clone();
        let request_id_clone = request_id.clone();
        let user_id_clone = user_id.clone();
        
        // Call the next service
        let fut = self.service.call(req);
        Box::pin(async move {
            // Wait for the response
            let result = fut.await;
            
            // Calculate request duration
            let duration = start_time.elapsed();
            let duration_ms = duration.as_millis();
            
            match &result {
                Ok(res) => {
                    // Get response status
                    let status = res.status().as_u16();
                    
                    // Log based on status code
                    if status < 400 {
                        info!(
                            "Request completed: {} {} {} in {}ms [{}]{}",
                            method_clone,
                            path_clone,
                            status,
                            duration_ms,
                            request_id_clone,
                            if let Some(id) = &user_id_clone {
                                format!(" user={}", id)
                            } else {
                                String::new()
                            }
                        );
                    } else if status < 500 {
                        warn!(
                            "Request error: {} {} {} in {}ms [{}]{}",
                            method_clone,
                            path_clone,
                            status,
                            duration_ms,
                            request_id_clone,
                            if let Some(id) = &user_id_clone {
                                format!(" user={}", id)
                            } else {
                                String::new()
                            }
                        );
                    } else {
                        error!(
                            "Request failed: {} {} {} in {}ms [{}]{}",
                            method_clone,
                            path_clone,
                            status,
                            duration_ms,
                            request_id_clone,
                            if let Some(id) = &user_id_clone {
                                format!(" user={}", id)
                            } else {
                                String::new()
                            }
                        );
                    }
                    
                    // TODO: Log response body if enabled
                    // This requires more complex body extraction and would need to modify the response
                }
                Err(e) => {
                    // Log error
                    error!(
                        "Request error: {} {} failed in {}ms: {} [{}]{}",
                        method_clone,
                        path_clone,
                        duration_ms,
                        e,
                        request_id_clone,
                        if let Some(id) = &user_id_clone {
                            format!(" user={}", id)
                        } else {
                            String::new()
                        }
                    );
                }
            }
            
            // Return the result
            result
        })
    }
}

/// Request ID holder for request extensions
#[derive(Debug, Clone)]
pub struct RequestId(pub String);