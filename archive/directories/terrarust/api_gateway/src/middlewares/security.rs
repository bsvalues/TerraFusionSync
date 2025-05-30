use std::future::{ready, Ready};
use std::rc::Rc;
use std::task::{Context, Poll};
use actix_web::{
    dev::{Service, ServiceRequest, ServiceResponse, Transform},
    Error, http::header,
};
use futures_util::future::LocalBoxFuture;

/// Middleware for adding security-related HTTP headers
pub struct SecurityHeadersMiddleware {
    pub content_security_policy: Option<String>,
}

impl Default for SecurityHeadersMiddleware {
    fn default() -> Self {
        Self {
            content_security_policy: Some(
                "default-src 'self'; \
                 script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; \
                 style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; \
                 img-src 'self' data: https:; \
                 font-src 'self' https://cdn.jsdelivr.net; \
                 connect-src 'self';"
                    .to_string(),
            ),
        }
    }
}

impl<S, B> Transform<S, ServiceRequest> for SecurityHeadersMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = SecurityHeadersMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(SecurityHeadersMiddlewareService {
            service: Rc::new(service),
            content_security_policy: self.content_security_policy.clone(),
        }))
    }
}

pub struct SecurityHeadersMiddlewareService<S> {
    service: Rc<S>,
    content_security_policy: Option<String>,
}

impl<S, B> Service<ServiceRequest> for SecurityHeadersMiddlewareService<S>
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
        let fut = self.service.call(req);
        let csp = self.content_security_policy.clone();
        
        Box::pin(async move {
            let mut res = fut.await?;
            
            // Add security headers to response
            let headers = res.headers_mut();
            
            // X-XSS-Protection
            headers.insert(
                header::HeaderName::from_static("x-xss-protection"),
                header::HeaderValue::from_static("1; mode=block"),
            );
            
            // X-Content-Type-Options
            headers.insert(
                header::HeaderName::from_static("x-content-type-options"),
                header::HeaderValue::from_static("nosniff"),
            );
            
            // X-Frame-Options
            headers.insert(
                header::HeaderName::from_static("x-frame-options"),
                header::HeaderValue::from_static("SAMEORIGIN"),
            );
            
            // Referrer-Policy
            headers.insert(
                header::HeaderName::from_static("referrer-policy"),
                header::HeaderValue::from_static("strict-origin-when-cross-origin"),
            );
            
            // Strict-Transport-Security
            headers.insert(
                header::HeaderName::from_static("strict-transport-security"),
                header::HeaderValue::from_static("max-age=31536000; includeSubDomains"),
            );
            
            // Content-Security-Policy
            if let Some(csp) = csp {
                headers.insert(
                    header::HeaderName::from_static("content-security-policy"),
                    header::HeaderValue::from_str(&csp).unwrap_or_else(|_| {
                        header::HeaderValue::from_static(
                            "default-src 'self'; script-src 'self'",
                        )
                    }),
                );
            }
            
            // Permissions-Policy
            headers.insert(
                header::HeaderName::from_static("permissions-policy"),
                header::HeaderValue::from_static(
                    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), \
                     microphone=(), payment=(), usb=()",
                ),
            );
            
            Ok(res)
        })
    }
}