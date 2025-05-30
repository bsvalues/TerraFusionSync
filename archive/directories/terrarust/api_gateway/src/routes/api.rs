use actix_web::{web, HttpRequest, HttpResponse, Result};
use serde_json::Value;
use crate::AppState;

/// Configure API routes that proxy to Python services
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/gis-export")
            .route("/jobs", web::get().to(list_gis_jobs))
            .route("/jobs", web::post().to(create_gis_job))
            .route("/jobs/{job_id}", web::get().to(get_gis_job))
            .route("/jobs/{job_id}/cancel", web::post().to(cancel_gis_job))
            .route("/download/{job_id}", web::get().to(download_gis_export))
    )
    .service(
        web::scope("/district-lookup")
            .route("/coordinates", web::get().to(lookup_coordinates))
            .route("/address", web::get().to(lookup_address))
            .route("/districts", web::get().to(list_districts))
            .route("/districts/{district_type}/{district_id}", web::get().to(get_district_info))
            .route("", web::get().to(district_lookup_info))
    )
    .service(
        web::scope("/sync")
            .route("/jobs", web::get().to(list_sync_jobs))
            .route("/jobs", web::post().to(create_sync_job))
            .route("/jobs/{job_id}", web::get().to(get_sync_job))
    );
}

/// Proxy GIS export job listing to Python service
async fn list_gis_jobs(
    req: HttpRequest,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let query_string = req.query_string();
    let url = format!("http://localhost:5000/api/v1/gis-export/jobs?{}", query_string);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "GIS Export service unavailable"
        })))
    }
}

/// Proxy GIS export job creation to Python service
async fn create_gis_job(
    req_body: web::Json<Value>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let url = "http://localhost:5000/api/v1/gis-export/jobs";
    
    let client = reqwest::Client::new();
    match client.post(url)
        .json(&req_body.into_inner())
        .send()
        .await
    {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "GIS Export service unavailable"
        })))
    }
}

/// Proxy GIS job status check to Python service
async fn get_gis_job(
    path: web::Path<String>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let job_id = path.into_inner();
    let url = format!("http://localhost:5000/api/v1/gis-export/jobs/{}", job_id);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "GIS Export service unavailable"
        })))
    }
}

/// Proxy GIS job cancellation to Python service
async fn cancel_gis_job(
    path: web::Path<String>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let job_id = path.into_inner();
    let url = format!("http://localhost:5000/api/v1/gis-export/jobs/{}/cancel", job_id);
    
    let client = reqwest::Client::new();
    match client.post(&url).send().await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "GIS Export service unavailable"
        })))
    }
}

/// Proxy GIS export download to Python service
async fn download_gis_export(
    path: web::Path<String>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let job_id = path.into_inner();
    let url = format!("http://localhost:5000/api/v1/gis-export/download/{}", job_id);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let headers = response.headers().clone();
            let body = response.bytes().await.unwrap_or_default();
            
            let mut http_response = HttpResponse::build(status);
            
            // Copy relevant headers
            if let Some(content_type) = headers.get("content-type") {
                http_response.insert_header(("content-type", content_type));
            }
            if let Some(content_disposition) = headers.get("content-disposition") {
                http_response.insert_header(("content-disposition", content_disposition));
            }
            
            Ok(http_response.body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "GIS Export service unavailable"
        })))
    }
}

/// Proxy district lookup by coordinates to Python service
async fn lookup_coordinates(
    req: HttpRequest,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let query_string = req.query_string();
    let url = format!("http://localhost:5000/api/v1/district-lookup/coordinates?{}", query_string);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "District lookup service unavailable"
        })))
    }
}

/// Proxy district lookup by address to Python service
async fn lookup_address(
    req: HttpRequest,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let query_string = req.query_string();
    let url = format!("http://localhost:5000/api/v1/district-lookup/address?{}", query_string);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "District lookup service unavailable"
        })))
    }
}

/// Proxy district listing to Python service
async fn list_districts(
    req: HttpRequest,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let query_string = req.query_string();
    let url = format!("http://localhost:5000/api/v1/district-lookup/districts?{}", query_string);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "District lookup service unavailable"
        })))
    }
}

/// Proxy district info lookup to Python service
async fn get_district_info(
    path: web::Path<(String, String)>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let (district_type, district_id) = path.into_inner();
    let url = format!("http://localhost:5000/api/v1/district-lookup/districts/{}/{}", district_type, district_id);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "District lookup service unavailable"
        })))
    }
}

/// Proxy district lookup service info to Python service
async fn district_lookup_info(
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let url = "http://localhost:5000/api/v1/district-lookup";
    
    match reqwest::get(url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "District lookup service unavailable"
        })))
    }
}

/// Proxy sync job listing to SyncService
async fn list_sync_jobs(
    req: HttpRequest,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let query_string = req.query_string();
    let url = format!("http://localhost:8080/operations?{}", query_string);
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "Sync service unavailable"
        })))
    }
}

/// Proxy sync job creation to SyncService
async fn create_sync_job(
    req_body: web::Json<Value>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    // Extract sync parameters from request
    let pair_id = req_body.get("pair_id").and_then(|v| v.as_str()).unwrap_or("1");
    let sync_type = req_body.get("sync_type").and_then(|v| v.as_str()).unwrap_or("incremental");
    
    let url = format!("http://localhost:8080/sync/{}/start?sync_type={}", pair_id, sync_type);
    
    let client = reqwest::Client::new();
    match client.post(&url).send().await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "Sync service unavailable"
        })))
    }
}

/// Proxy sync job status check to SyncService
async fn get_sync_job(
    path: web::Path<String>,
    data: web::Data<AppState>
) -> Result<HttpResponse> {
    let job_id = path.into_inner();
    let url = format!("http://localhost:8080/operations");
    
    match reqwest::get(&url).await {
        Ok(response) => {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            Ok(HttpResponse::build(status).body(body))
        }
        Err(_) => Ok(HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": "Sync service unavailable"
        })))
    }
}