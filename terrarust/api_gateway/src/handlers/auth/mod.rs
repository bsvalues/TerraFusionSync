use actix_session::Session;
use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;
use crate::middleware::auth::{generate_token, Claims};

/// Login form data
#[derive(Debug, Deserialize)]
pub struct LoginForm {
    pub username: String,
    pub password: String,
}

/// Login page template data
#[derive(Debug, Serialize)]
struct LoginPageData {
    title: String,
    error_message: Option<String>,
}

/// Current user information
#[derive(Debug, Serialize)]
pub struct CurrentUser {
    pub username: String,
    pub role: String,
    pub county_id: String,
}

/// Login page handler
pub async fn login_page(
    query: web::Query<Option<LoginQuery>>,
    hb: web::Data<handlebars::Handlebars<'_>>,
) -> impl Responder {
    let error_message = query
        .as_ref()
        .and_then(|q| q.error.clone());
    
    let data = LoginPageData {
        title: "TerraFusion Platform - Login".to_string(),
        error_message,
    };
    
    let body = hb.render("login", &data).unwrap_or_else(|err| {
        format!("Template rendering error: {}", err)
    });
    
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(body)
}

/// Query parameters for login page
#[derive(Debug, Deserialize)]
pub struct LoginQuery {
    pub error: Option<String>,
}

/// Login handler
pub async fn login(
    form: web::Form<LoginForm>,
    session: Session,
    state: web::Data<AppState>,
) -> impl Responder {
    // Here we would validate credentials against the database
    // For demonstration, we'll use hardcoded values
    // In a real system, this would use bcrypt or similar for password verification
    
    // Simple login check
    let conn = match state.database.get_connection() {
        Ok(conn) => conn,
        Err(_) => {
            return HttpResponse::Found()
                .append_header(("Location", "/login?error=Database+connection+failed"))
                .finish();
        }
    };
    
    // Placeholder for actual database authentication logic
    // In a real system, this would query the users table and verify password hash
    let valid = form.username == "admin" && form.password == "password";
    
    if valid {
        // Create JWT token
        let token = match generate_token(
            &form.username,
            "admin",
            "TEST_COUNTY",
            60 * 8, // 8 hours
        ) {
            Ok(t) => t,
            Err(_) => {
                return HttpResponse::Found()
                    .append_header(("Location", "/login?error=Token+generation+failed"))
                    .finish();
            }
        };
        
        // Store token in session
        if let Err(_) = session.insert("jwt", token) {
            return HttpResponse::Found()
                .append_header(("Location", "/login?error=Session+storage+failed"))
                .finish();
        }
        
        // Store user information in session
        let _ = session.insert("username", form.username.clone());
        let _ = session.insert("role", "admin");
        let _ = session.insert("county_id", "TEST_COUNTY");
        
        // Redirect to dashboard
        HttpResponse::Found()
            .append_header(("Location", "/dashboard"))
            .finish()
    } else {
        // Failed login
        HttpResponse::Found()
            .append_header(("Location", "/login?error=Invalid+username+or+password"))
            .finish()
    }
}

/// Logout handler
pub async fn logout(session: Session) -> impl Responder {
    // Clear the session
    session.purge();
    
    // Redirect to login page
    HttpResponse::Found()
        .append_header(("Location", "/login"))
        .finish()
}

/// Get the current user from the session
pub fn get_current_user_from_session(session: &Session) -> Option<CurrentUser> {
    let username = session.get::<String>("username").ok()??;
    let role = session.get::<String>("role").ok()??;
    let county_id = session.get::<String>("county_id").ok()??;
    
    Some(CurrentUser {
        username,
        role,
        county_id,
    })
}

/// Get the current user from JWT claims
pub fn get_current_user_from_claims(claims: &Claims) -> CurrentUser {
    CurrentUser {
        username: claims.sub.clone(),
        role: claims.role.clone(),
        county_id: claims.county_id.clone(),
    }
}