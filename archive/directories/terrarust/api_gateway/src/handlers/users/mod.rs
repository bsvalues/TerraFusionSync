use actix_web::{web, HttpResponse, Responder};
use common::error::{Error, Result};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::handlers::auth::{get_current_user_from_session, CurrentUser};
use crate::middleware::auth::Claims;

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub username: String,
    pub email: String,
    pub role: String,
    pub county_id: String,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UserResponse {
    pub user: User,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UsersResponse {
    pub users: Vec<User>,
    pub total_count: i64,
}

#[derive(Debug, Deserialize)]
pub struct UserQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
    pub role: Option<String>,
    pub county_id: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub email: String,
    pub password: String,
    pub role: String,
    pub county_id: String,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUserRequest {
    pub email: Option<String>,
    pub role: Option<String>,
    pub county_id: Option<String>,
    pub password: Option<String>,
}

/// Get all users with optional filtering
pub async fn get_all_users(
    query: web::Query<UserQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    let users = vec![
        User {
            id: Uuid::parse_str("12345678-1234-1234-1234-123456789012").unwrap(),
            username: "admin".to_string(),
            email: "admin@example.com".to_string(),
            role: "admin".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            created_at: "2023-05-01T12:00:00Z".to_string(),
            updated_at: "2023-05-01T12:00:00Z".to_string(),
        },
        User {
            id: Uuid::parse_str("87654321-4321-4321-4321-210987654321").unwrap(),
            username: "user".to_string(),
            email: "user@example.com".to_string(),
            role: "user".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            created_at: "2023-05-02T14:30:00Z".to_string(),
            updated_at: "2023-05-02T14:30:00Z".to_string(),
        },
    ];
    
    HttpResponse::Ok().json(UsersResponse {
        users,
        total_count: users.len() as i64,
    })
}

/// Create a new user
pub async fn create_user(
    req: web::Json<CreateUserRequest>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Ensure only admins can create users
    if claims.role != "admin" {
        return HttpResponse::Forbidden().json(web::Json(
            serde_json::json!({
                "error": "Only administrators can create users",
                "status": 403
            })
        ));
    }
    
    // In a real implementation, this would validate and store the user
    // For now, return a created response with mock data
    let new_user = User {
        id: Uuid::new_v4(),
        username: req.username.clone(),
        email: req.email.clone(),
        role: req.role.clone(),
        county_id: req.county_id.clone(),
        created_at: chrono::Utc::now().to_rfc3339(),
        updated_at: chrono::Utc::now().to_rfc3339(),
    };
    
    // Create audit log
    // In a real implementation, this would store in the database
    log::info!(
        "User {} created by admin {}",
        new_user.username,
        claims.sub
    );
    
    HttpResponse::Created().json(UserResponse {
        user: new_user,
    })
}

/// Get the current user
pub async fn get_current_user(
    session: actix_session::Session,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // In a real implementation, this would look up the user in the database
    // For now, return a user based on JWT claims
    let user = User {
        id: Uuid::parse_str("12345678-1234-1234-1234-123456789012").unwrap(),
        username: claims.sub.clone(),
        email: format!("{}@example.com", claims.sub),
        role: claims.role.clone(),
        county_id: claims.county_id.clone(),
        created_at: "2023-05-01T12:00:00Z".to_string(),
        updated_at: "2023-05-01T12:00:00Z".to_string(),
    };
    
    HttpResponse::Ok().json(UserResponse {
        user,
    })
}

/// Get a specific user by ID
pub async fn get_user(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Ensure only admins can get other users
    if claims.role != "admin" && claims.sub != "admin" {
        return HttpResponse::Forbidden().json(web::Json(
            serde_json::json!({
                "error": "Only administrators can view other user details",
                "status": 403
            })
        ));
    }
    
    // In a real implementation, this would look up the user in the database
    // For now, return a stub response
    if *id == Uuid::parse_str("12345678-1234-1234-1234-123456789012").unwrap() {
        let user = User {
            id: *id,
            username: "admin".to_string(),
            email: "admin@example.com".to_string(),
            role: "admin".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            created_at: "2023-05-01T12:00:00Z".to_string(),
            updated_at: "2023-05-01T12:00:00Z".to_string(),
        };
        
        HttpResponse::Ok().json(UserResponse {
            user,
        })
    } else if *id == Uuid::parse_str("87654321-4321-4321-4321-210987654321").unwrap() {
        let user = User {
            id: *id,
            username: "user".to_string(),
            email: "user@example.com".to_string(),
            role: "user".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            created_at: "2023-05-02T14:30:00Z".to_string(),
            updated_at: "2023-05-02T14:30:00Z".to_string(),
        };
        
        HttpResponse::Ok().json(UserResponse {
            user,
        })
    } else {
        HttpResponse::NotFound().json(web::Json(
            serde_json::json!({
                "error": format!("User not found: {}", id),
                "status": 404
            })
        ))
    }
}

/// Update a user
pub async fn update_user(
    id: web::Path<Uuid>,
    req: web::Json<UpdateUserRequest>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Ensure users can only update themselves, or admins can update any user
    if claims.role != "admin" && claims.sub != "admin" && 
       *id != Uuid::parse_str("12345678-1234-1234-1234-123456789012").unwrap() {
        return HttpResponse::Forbidden().json(web::Json(
            serde_json::json!({
                "error": "You can only update your own user profile",
                "status": 403
            })
        ));
    }
    
    // In a real implementation, this would update the user in the database
    // For now, return a stub response
    if *id == Uuid::parse_str("12345678-1234-1234-1234-123456789012").unwrap() {
        let user = User {
            id: *id,
            username: "admin".to_string(),
            email: req.email.clone().unwrap_or("admin@example.com".to_string()),
            role: req.role.clone().unwrap_or("admin".to_string()),
            county_id: req.county_id.clone().unwrap_or("TEST_COUNTY".to_string()),
            created_at: "2023-05-01T12:00:00Z".to_string(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        };
        
        // Create audit log
        // In a real implementation, this would store in the database
        log::info!(
            "User {} updated by {}",
            user.username,
            claims.sub
        );
        
        HttpResponse::Ok().json(UserResponse {
            user,
        })
    } else if *id == Uuid::parse_str("87654321-4321-4321-4321-210987654321").unwrap() {
        let user = User {
            id: *id,
            username: "user".to_string(),
            email: req.email.clone().unwrap_or("user@example.com".to_string()),
            role: req.role.clone().unwrap_or("user".to_string()),
            county_id: req.county_id.clone().unwrap_or("TEST_COUNTY".to_string()),
            created_at: "2023-05-02T14:30:00Z".to_string(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        };
        
        // Create audit log
        // In a real implementation, this would store in the database
        log::info!(
            "User {} updated by {}",
            user.username,
            claims.sub
        );
        
        HttpResponse::Ok().json(UserResponse {
            user,
        })
    } else {
        HttpResponse::NotFound().json(web::Json(
            serde_json::json!({
                "error": format!("User not found: {}", id),
                "status": 404
            })
        ))
    }
}