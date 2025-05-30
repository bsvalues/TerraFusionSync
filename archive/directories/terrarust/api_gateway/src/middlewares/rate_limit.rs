use std::future::{ready, Ready};
use std::rc::Rc;
use std::task::{Context, Poll};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::time::{Duration, Instant};
use actix_web::{
    dev::{Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpResponse,
};
use futures_util::future::LocalBoxFuture;
use crate::errors::AppError;

/// Rate limiter implementation using token bucket algorithm
#[derive(Debug, Clone)]
struct TokenBucket {
    capacity: usize,
    refill_rate: usize,
    tokens: usize,
    last_refill: Instant,
}

impl TokenBucket {
    fn new(capacity: usize, refill_rate: usize) -> Self {
        Self {
            capacity,
            refill_rate,
            tokens: capacity,
            last_refill: Instant::now(),
        }
    }
    
    fn refill(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill);
        let tokens_to_add = (elapsed.as_secs_f64() * self.refill_rate as f64) as usize;
        
        if tokens_to_add > 0 {
            self.tokens = (self.tokens + tokens_to_add).min(self.capacity);
            self.last_refill = now;
        }
    }
    
    fn consume(&mut self, tokens: usize) -> bool {
        self.refill();
        
        if self.tokens >= tokens {
            self.tokens -= tokens;
            true
        } else {
            false
        }
    }
}

/// Storage for rate limiter buckets
#[derive(Debug, Clone)]
struct RateLimitStore {
    buckets: Arc<Mutex<HashMap<String, TokenBucket>>>,
}

impl RateLimitStore {
    fn new() -> Self {
        Self {
            buckets: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    fn get_bucket(&self, key: &str, capacity: usize, refill_rate: usize) -> Option<bool> {
        let mut buckets = self.buckets.lock().unwrap();
        
        if !buckets.contains_key(key) {
            buckets.insert(key.to_string(), TokenBucket::new(capacity, refill_rate));
        }
        
        if let Some(bucket) = buckets.get_mut(key) {
            Some(bucket.consume(1))
        } else {
            None
        }
    }
}

/// Middleware for rate limiting requests
pub struct RateLimitMiddleware {
    pub requests_per_second: usize,
    pub burst_size: usize,
    pub exclude_paths: Vec<String>,
}

impl Default for RateLimitMiddleware {
    fn default() -> Self {
        Self {
            requests_per_second: 10,
            burst_size: 20,
            exclude_paths: vec![
                "/static".to_string(),
                "/system/health".to_string(),
                "/system/metrics".to_string(),
            ],
        }
    }
}

impl<S, B> Transform<S, ServiceRequest> for RateLimitMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = RateLimitMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(RateLimitMiddlewareService {
            service: Rc::new(service),
            store: RateLimitStore::new(),
            requests_per_second: self.requests_per_second,
            burst_size: self.burst_size,
            exclude_paths: self.exclude_paths.clone(),
        }))
    }
}

pub struct RateLimitMiddlewareService<S> {
    service: Rc<S>,
    store: RateLimitStore,
    requests_per_second: usize,
    burst_size: usize,
    exclude_paths: Vec<String>,
}

impl<S, B> Service<ServiceRequest> for RateLimitMiddlewareService<S>
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
        
        // Skip rate limiting for excluded paths
        if self.should_skip_rate_limit(&path) {
            let fut = self.service.call(req);
            return Box::pin(async move {
                let res = fut.await?;
                Ok(res)
            });
        }
        
        // Get client IP for rate limiting key
        let client_ip = req
            .connection_info()
            .realip_remote_addr()
            .unwrap_or("unknown")
            .to_string();
        
        // Perform rate limiting check
        let key = format!("{}:{}", client_ip, req.path());
        let allowed = self.store.get_bucket(&key, self.burst_size, self.requests_per_second).unwrap_or(false);
        
        if allowed {
            // Request is allowed, continue
            let fut = self.service.call(req);
            Box::pin(async move {
                let res = fut.await?;
                Ok(res)
            })
        } else {
            // Rate limit exceeded
            let error = AppError::ServiceUnavailable("Rate limit exceeded. Try again later.".to_string());
            Box::pin(async move {
                let response = HttpResponse::TooManyRequests()
                    .append_header(("Retry-After", "5"))
                    .json(serde_json::json!({
                        "error": {
                            "code": 429,
                            "message": "Rate limit exceeded. Try again later.",
                            "type": "rate_limit_exceeded"
                        }
                    }));
                
                Err(actix_web::error::InternalError::from_response(
                    error,
                    response,
                ).into())
            })
        }
    }
}

impl<S> RateLimitMiddlewareService<S> {
    /// Check if rate limiting should be skipped for this path
    fn should_skip_rate_limit(&self, path: &str) -> bool {
        self.exclude_paths.iter().any(|excluded| path.starts_with(excluded))
    }
}