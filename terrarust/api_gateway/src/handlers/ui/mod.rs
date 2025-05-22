use actix_session::Session;
use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;
use crate::handlers::auth::get_current_user_from_session;

/// Base template data shared across all views
#[derive(Debug, Serialize)]
struct BaseTemplateData {
    title: String,
    username: Option<String>,
    role: Option<String>,
    county_id: Option<String>,
    active_page: String,
}

/// Index page handler
pub async fn index(
    session: Session,
    hb: web::Data<handlebars::Handlebars<'_>>,
) -> impl Responder {
    // If user is logged in, redirect to dashboard
    if get_current_user_from_session(&session).is_some() {
        return HttpResponse::Found()
            .append_header(("Location", "/dashboard"))
            .finish();
    }
    
    // Otherwise show the landing page
    let data = BaseTemplateData {
        title: "TerraFusion Platform".to_string(),
        username: None,
        role: None,
        county_id: None,
        active_page: "home".to_string(),
    };
    
    let body = hb.render("index", &data).unwrap_or_else(|err| {
        format!("Template rendering error: {}", err)
    });
    
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(body)
}

/// Dashboard page data
#[derive(Debug, Serialize)]
struct DashboardData {
    #[serde(flatten)]
    base: BaseTemplateData,
    sync_operations_count: i64,
    active_sync_pairs: i64,
    recent_exports: i64,
    pending_exports: i64,
}

/// Dashboard page handler
pub async fn dashboard(
    session: Session,
    state: web::Data<AppState>,
    hb: web::Data<handlebars::Handlebars<'_>>,
) -> impl Responder {
    // Get current user from session
    let current_user = match get_current_user_from_session(&session) {
        Some(user) => user,
        None => {
            return HttpResponse::Found()
                .append_header(("Location", "/login"))
                .finish();
        }
    };
    
    // Get dashboard statistics
    // In a real implementation, this would query the services for actual data
    let sync_operations_count = 15;
    let active_sync_pairs = 8;
    let recent_exports = 12;
    let pending_exports = 3;
    
    // Prepare template data
    let data = DashboardData {
        base: BaseTemplateData {
            title: "TerraFusion Platform - Dashboard".to_string(),
            username: Some(current_user.username),
            role: Some(current_user.role),
            county_id: Some(current_user.county_id),
            active_page: "dashboard".to_string(),
        },
        sync_operations_count,
        active_sync_pairs,
        recent_exports,
        pending_exports,
    };
    
    // Render template
    let body = hb.render("dashboard", &data).unwrap_or_else(|err| {
        format!("Template rendering error: {}", err)
    });
    
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(body)
}

/// Sync dashboard page data
#[derive(Debug, Serialize)]
struct SyncDashboardData {
    #[serde(flatten)]
    base: BaseTemplateData,
    sync_pairs: Vec<SyncPairView>,
    recent_operations: Vec<SyncOperationView>,
}

/// Sync pair view model
#[derive(Debug, Serialize)]
struct SyncPairView {
    id: String,
    name: String,
    source_system: String,
    target_system: String,
    county_id: String,
    last_sync_time: Option<String>,
    is_active: bool,
}

/// Sync operation view model
#[derive(Debug, Serialize)]
struct SyncOperationView {
    id: String,
    sync_pair_name: String,
    status: String,
    start_time: String,
    end_time: Option<String>,
    records_processed: Option<i32>,
    records_succeeded: Option<i32>,
    records_failed: Option<i32>,
}

/// Sync dashboard page handler
pub async fn sync_dashboard(
    session: Session,
    state: web::Data<AppState>,
    hb: web::Data<handlebars::Handlebars<'_>>,
) -> impl Responder {
    // Get current user from session
    let current_user = match get_current_user_from_session(&session) {
        Some(user) => user,
        None => {
            return HttpResponse::Found()
                .append_header(("Location", "/login"))
                .finish();
        }
    };
    
    // Get sync pairs and operations
    // In a real implementation, this would query the SyncService
    // For demonstration, we'll use mock data
    let sync_pairs = vec![
        SyncPairView {
            id: "12345678-1234-1234-1234-123456789012".to_string(),
            name: "County Parcels Sync".to_string(),
            source_system: "Legacy GIS".to_string(),
            target_system: "Modern GIS".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            last_sync_time: Some("2023-05-15T10:30:00Z".to_string()),
            is_active: true,
        },
        SyncPairView {
            id: "87654321-4321-4321-4321-210987654321".to_string(),
            name: "Tax Assessment Sync".to_string(),
            source_system: "Tax System".to_string(),
            target_system: "County Database".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            last_sync_time: Some("2023-05-20T14:45:00Z".to_string()),
            is_active: true,
        },
    ];
    
    let recent_operations = vec![
        SyncOperationView {
            id: "op-12345".to_string(),
            sync_pair_name: "County Parcels Sync".to_string(),
            status: "COMPLETED".to_string(),
            start_time: "2023-05-15T10:30:00Z".to_string(),
            end_time: Some("2023-05-15T10:45:00Z".to_string()),
            records_processed: Some(1250),
            records_succeeded: Some(1245),
            records_failed: Some(5),
        },
        SyncOperationView {
            id: "op-12346".to_string(),
            sync_pair_name: "Tax Assessment Sync".to_string(),
            status: "COMPLETED".to_string(),
            start_time: "2023-05-20T14:45:00Z".to_string(),
            end_time: Some("2023-05-20T15:00:00Z".to_string()),
            records_processed: Some(850),
            records_succeeded: Some(850),
            records_failed: Some(0),
        },
    ];
    
    // Prepare template data
    let data = SyncDashboardData {
        base: BaseTemplateData {
            title: "TerraFusion Platform - Sync Dashboard".to_string(),
            username: Some(current_user.username),
            role: Some(current_user.role),
            county_id: Some(current_user.county_id),
            active_page: "sync_dashboard".to_string(),
        },
        sync_pairs,
        recent_operations,
    };
    
    // Render template
    let body = hb.render("sync_dashboard", &data).unwrap_or_else(|err| {
        format!("Template rendering error: {}", err)
    });
    
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(body)
}

/// GIS Export dashboard page data
#[derive(Debug, Serialize)]
struct GisExportDashboardData {
    #[serde(flatten)]
    base: BaseTemplateData,
    exports: Vec<GisExportView>,
    available_counties: Vec<CountyView>,
    available_formats: Vec<String>,
}

/// GIS Export view model
#[derive(Debug, Serialize)]
struct GisExportView {
    id: String,
    county_id: String,
    export_format: String,
    status: String,
    created_at: String,
    created_by: String,
}

/// County view model
#[derive(Debug, Serialize)]
struct CountyView {
    id: String,
    name: String,
}

/// GIS Export dashboard page handler
pub async fn gis_export_dashboard(
    session: Session,
    state: web::Data<AppState>,
    hb: web::Data<handlebars::Handlebars<'_>>,
) -> impl Responder {
    // Get current user from session
    let current_user = match get_current_user_from_session(&session) {
        Some(user) => user,
        None => {
            return HttpResponse::Found()
                .append_header(("Location", "/login"))
                .finish();
        }
    };
    
    // Get recent exports
    // In a real implementation, this would query the GIS Export service
    // For demonstration, we'll use mock data
    let exports = vec![
        GisExportView {
            id: "exp-12345".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            export_format: "geojson".to_string(),
            status: "COMPLETED".to_string(),
            created_at: "2023-05-18T09:30:00Z".to_string(),
            created_by: "admin".to_string(),
        },
        GisExportView {
            id: "exp-12346".to_string(),
            county_id: "TEST_COUNTY".to_string(),
            export_format: "shapefile".to_string(),
            status: "COMPLETED".to_string(),
            created_at: "2023-05-19T11:45:00Z".to_string(),
            created_by: "admin".to_string(),
        },
    ];
    
    // Get available counties
    let available_counties = vec![
        CountyView {
            id: "TEST_COUNTY".to_string(),
            name: "Test County".to_string(),
        },
        CountyView {
            id: "ANOTHER_COUNTY".to_string(),
            name: "Another County".to_string(),
        },
    ];
    
    // Get available export formats
    let available_formats = vec![
        "geojson".to_string(),
        "shapefile".to_string(),
        "kml".to_string(),
    ];
    
    // Prepare template data
    let data = GisExportDashboardData {
        base: BaseTemplateData {
            title: "TerraFusion Platform - GIS Export".to_string(),
            username: Some(current_user.username),
            role: Some(current_user.role),
            county_id: Some(current_user.county_id),
            active_page: "gis_export".to_string(),
        },
        exports,
        available_counties,
        available_formats,
    };
    
    // Render template
    let body = hb.render("gis_export_dashboard", &data).unwrap_or_else(|err| {
        format!("Template rendering error: {}", err)
    });
    
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(body)
}