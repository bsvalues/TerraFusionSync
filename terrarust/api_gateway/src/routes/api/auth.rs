use actix_web::{web, HttpResponse, Responder, post, get, HttpRequest};
use serde::{Deserialize, Serialize};
use crate::errors::{AppError, AppResult};
use crate::handlers;
use jsonwebtoken::{encode, EncodingKey, Algorithm, Header};
use crate::middlewares::auth::Claims;
use std::time::Duration;

/// Configure auth routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(login)
       .service(logout)
       .service(refresh_token)
       .service(validate_token);
}

/// Login request structure
#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
    #[serde(default)]
    pub remember_me: bool,
}

/// Login response structure
#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub user: UserInfo,
    pub expires_at: i64,
}

/// User information structure
#[derive(Debug, Serialize)]
pub struct UserInfo {
    pub id: String,
    pub username: String,
    pub email: String,
    pub full_name: String,
    pub county_id: String,
    pub roles: Vec<String>,
}

/// Login handler
#[post("/login")]
async fn login(
    login_req: web::Json<LoginRequest>,
    req: HttpRequest,
) -> AppResult<impl Responder> {
    // Call the auth handler to validate credentials
    let auth_result = handlers::auth::authenticate_user(
        &login_req.username,
        &login_req.password
    ).await?;
    
    // If authentication is successful, generate JWT token
    let expiry = if login_req.remember_me {
        Duration::from_secs(30 * 24 * 60 * 60) // 30 days
    } else {
        Duration::from_secs(24 * 60 * 60) // 24 hours
    };
    
    let claims = Claims::new(
        &auth_result.user_id,
        &auth_result.name,
        &auth_result.email,
        auth_result.roles.clone(),
        &auth_result.county_id,
        expiry,
    );
    
    // Get JWT secret from environment
    let jwt_secret = std::env::var("JWT_SECRET")
        .unwrap_or_else(|_| "default_secret_for_development".to_string());
    
    // Encode the JWT token
    let token = encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(jwt_secret.as_bytes()),
    ).map_err(|e| AppError::InternalServerError(format!("Failed to generate token: {}", e)))?;
    
    // Create response with token and user info
    let expires_at = chrono::Utc::now()
        .checked_add_signed(chrono::Duration::seconds(expiry.as_secs() as i64))
        .unwrap_or_else(|| chrono::Utc::now())
        .timestamp();
    
    let response = LoginResponse {
        token,
        user: UserInfo {
            id: auth_result.user_id,
            username: auth_result.username,
            email: auth_result.email,
            full_name: auth_result.name,
            county_id: auth_result.county_id,
            roles: auth_result.roles,
        },
        expires_at,
    };
    
    // Log successful login
    log::info!(
        "User {} logged in successfully from {}",
        login_req.username,
        req.connection_info().realip_remote_addr().unwrap_or("unknown"),
    );
    
    Ok(web::Json(response))
}

/// Logout handler
#[post("/logout")]
async fn logout(req: HttpRequest) -> AppResult<impl Responder> {
    // For JWT-based auth, we don't need to do anything server-side
    // The client should discard the token
    
    // Log logout if we have user info
    if let Some(claims) = req.extensions().get::<Claims>() {
        log::info!(
            "User {} logged out from {}",
            claims.name,
            req.connection_info().realip_remote_addr().unwrap_or("unknown"),
        );
    }
    
    Ok(web::Json(serde_json::json!({
        "success": true,
        "message": "Logged out successfully"
    })))
}

/// Token refresh request
#[derive(Debug, Deserialize)]
pub struct RefreshTokenRequest {
    pub token: String,
}

/// Refresh token handler
#[post("/refresh")]
async fn refresh_token(
    refresh_req: web::Json<RefreshTokenRequest>,
    req: HttpRequest,
) -> AppResult<impl Responder> {
    // Validate the current token and issue a new one
    let auth_result = handlers::auth::refresh_token(&refresh_req.token).await?;
    
    // Generate new token with the same claims but new expiry
    let expiry = Duration::from_secs(24 * 60 * 60); // 24 hours
    
    let claims = Claims::new(
        &auth_result.user_id,
        &auth_result.name,
        &auth_result.email,
        auth_result.roles.clone(),
        &auth_result.county_id,
        expiry,
    );
    
    // Get JWT secret from environment
    let jwt_secret = std::env::var("JWT_SECRET")
        .unwrap_or_else(|_| "default_secret_for_development".to_string());
    
    // Encode the JWT token
    let token = encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(jwt_secret.as_bytes()),
    ).map_err(|e| AppError::InternalServerError(format!("Failed to generate token: {}", e)))?;
    
    // Create response with new token
    let expires_at = chrono::Utc::now()
        .checked_add_signed(chrono::Duration::seconds(expiry.as_secs() as i64))
        .unwrap_or_else(|| chrono::Utc::now())
        .timestamp();
    
    let response = LoginResponse {
        token,
        user: UserInfo {
            id: auth_result.user_id,
            username: auth_result.username,
            email: auth_result.email,
            full_name: auth_result.name,
            county_id: auth_result.county_id,
            roles: auth_result.roles,
        },
        expires_at,
    };
    
    Ok(web::Json(response))
}

/// Token validation request
#[derive(Debug, Deserialize)]
pub struct ValidateTokenRequest {
    pub token: String,
}

/// Validate token handler
#[post("/validate")]
async fn validate_token(
    validate_req: web::Json<ValidateTokenRequest>,
) -> AppResult<impl Responder> {
    // Validate the token
    let validation_result = handlers::auth::validate_token(&validate_req.token).await?;
    
    Ok(web::Json(serde_json::json!({
        "valid": validation_result.is_valid,
        "user": {
            "id": validation_result.user_id,
            "username": validation_result.username,
            "email": validation_result.email,
            "full_name": validation_result.name,
            "county_id": validation_result.county_id,
            "roles": validation_result.roles,
        },
        "expires_at": validation_result.expires_at
    })))
}