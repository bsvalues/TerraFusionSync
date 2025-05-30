use crate::error::{Error, Result};
use chrono::{DateTime, Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,         // Subject (user ID)
    pub name: Option<String>, // User's full name
    pub email: Option<String>, // User's email
    pub roles: Vec<String>,  // User's roles
    pub counties: Vec<String>, // Counties the user has access to
    pub exp: i64,            // Expiration time (as UTC timestamp)
    pub iat: i64,            // Issued at (as UTC timestamp)
}

pub fn generate_token(
    user_id: &str,
    name: Option<&str>,
    email: Option<&str>,
    roles: Vec<String>,
    counties: Vec<String>,
    jwt_secret: &str,
    expiration: i64,
) -> Result<String> {
    let now = Utc::now();
    let expires_at = now + Duration::minutes(expiration);
    
    let claims = Claims {
        sub: user_id.to_string(),
        name: name.map(|s| s.to_string()),
        email: email.map(|s| s.to_string()),
        roles,
        counties,
        exp: expires_at.timestamp(),
        iat: now.timestamp(),
    };
    
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(jwt_secret.as_bytes()),
    )
    .map_err(|e| Error::Authentication(format!("Failed to create token: {}", e)))?;
    
    Ok(token)
}

pub fn validate_token(token: &str, jwt_secret: &str) -> Result<Claims> {
    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(jwt_secret.as_bytes()),
        &Validation::default(),
    )
    .map_err(|e| Error::Authentication(format!("Invalid token: {}", e)))?;
    
    Ok(token_data.claims)
}

pub fn is_token_expired(exp: i64) -> bool {
    let now = Utc::now().timestamp();
    exp < now
}