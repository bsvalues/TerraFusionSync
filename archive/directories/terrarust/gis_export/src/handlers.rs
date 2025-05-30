use actix_web::{web, HttpResponse, Result, HttpRequest};
use actix_files::NamedFile;
use uuid::Uuid;
use crate::models::*;
use crate::service::GisExportService;
use std::sync::Arc;

/// Application state containing the GIS export service
pub struct AppState {
    pub gis_service: Arc<GisExportService>,
}

/// Create a new GIS export job
pub async fn create_job(
    data: web::Data<AppState>,
    request: web::Json<CreateJobRequest>,
) -> Result<HttpResponse> {
    match data.gis_service.create_job(request.into_inner()).await {
        Ok(response) => Ok(HttpResponse::Created().json(response)),
        Err(e) => {
            log::error!("Failed to create export job: {}", e);
            Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": e.to_string()
            })))
        }
    }
}

/// Get job status by ID
pub async fn get_job_status(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> Result<HttpResponse> {
    let job_id_str = path.into_inner();
    
    let job_id = match Uuid::parse_str(&job_id_str) {
        Ok(id) => id,
        Err(_) => {
            return Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": "Invalid job ID format"
            })));
        }
    };

    match data.gis_service.get_job_status(job_id).await {
        Ok(response) => Ok(HttpResponse::Ok().json(response)),
        Err(e) => {
            log::error!("Failed to get job status: {}", e);
            Ok(HttpResponse::NotFound().json(serde_json::json!({
                "error": "Job not found"
            })))
        }
    }
}

/// List export jobs with optional filtering
pub async fn list_jobs(
    data: web::Data<AppState>,
    query: web::Query<ListJobsParams>,
) -> Result<HttpResponse> {
    match data.gis_service.list_jobs(query.into_inner()).await {
        Ok(response) => Ok(HttpResponse::Ok().json(response)),
        Err(e) => {
            log::error!("Failed to list jobs: {}", e);
            Ok(HttpResponse::InternalServerError().json(serde_json::json!({
                "error": "Failed to retrieve jobs"
            })))
        }
    }
}

/// Process a job (start the export)
pub async fn process_job(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> Result<HttpResponse> {
    let job_id_str = path.into_inner();
    
    let job_id = match Uuid::parse_str(&job_id_str) {
        Ok(id) => id,
        Err(_) => {
            return Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": "Invalid job ID format"
            })));
        }
    };

    // Start processing in background
    let service = data.gis_service.clone();
    tokio::spawn(async move {
        if let Err(e) = service.process_job(job_id).await {
            log::error!("Background job processing failed for {}: {}", job_id, e);
        }
    });

    Ok(HttpResponse::Accepted().json(serde_json::json!({
        "message": "Job processing started",
        "job_id": job_id
    })))
}

/// Cancel an export job
pub async fn cancel_job(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> Result<HttpResponse> {
    let job_id_str = path.into_inner();
    
    let job_id = match Uuid::parse_str(&job_id_str) {
        Ok(id) => id,
        Err(_) => {
            return Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": "Invalid job ID format"
            })));
        }
    };

    match data.gis_service.cancel_job(job_id).await {
        Ok(response) => Ok(HttpResponse::Ok().json(response)),
        Err(e) => {
            log::error!("Failed to cancel job: {}", e);
            Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": e.to_string()
            })))
        }
    }
}

/// Download completed export file
pub async fn download_export(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> Result<HttpResponse> {
    let job_id_str = path.into_inner();
    
    let job_id = match Uuid::parse_str(&job_id_str) {
        Ok(id) => id,
        Err(_) => {
            return Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": "Invalid job ID format"
            })));
        }
    };

    match data.gis_service.get_export_file(job_id).await {
        Ok(file_path) => {
            match NamedFile::open(&file_path) {
                Ok(file) => {
                    // Get job details for proper filename
                    if let Ok(job_status) = data.gis_service.get_job_status(job_id).await {
                        let filename = format!("{}_{}.{}", 
                            job_status.county_id,
                            job_id.simple(),
                            job_status.export_format
                        );
                        Ok(file.set_content_disposition(
                            actix_web::http::header::ContentDisposition {
                                disposition: actix_web::http::header::DispositionType::Attachment,
                                parameters: vec![
                                    actix_web::http::header::DispositionParam::Filename(filename)
                                ],
                            }
                        ).into_response(&HttpRequest::from_parts(
                            actix_web::dev::RequestHead::default(),
                            actix_web::dev::Payload::None
                        )))
                    } else {
                        Ok(file.into_response(&HttpRequest::from_parts(
                            actix_web::dev::RequestHead::default(),
                            actix_web::dev::Payload::None
                        )))
                    }
                }
                Err(e) => {
                    log::error!("Failed to open export file: {}", e);
                    Ok(HttpResponse::InternalServerError().json(serde_json::json!({
                        "error": "Export file not accessible"
                    })))
                }
            }
        }
        Err(e) => {
            log::error!("Failed to get export file: {}", e);
            Ok(HttpResponse::NotFound().json(serde_json::json!({
                "error": "Export file not found"
            })))
        }
    }
}

/// Health check endpoint
pub async fn health_check() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "service": "TerraFusion GIS Export (Rust)",
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "supported_formats": [
            "shapefile",
            "geojson",
            "kml", 
            "geopackage",
            "csv"
        ]
    })))
}

/// Service metrics endpoint
pub async fn metrics(data: web::Data<AppState>) -> Result<HttpResponse> {
    // Get basic job statistics
    let job_stats = match data.gis_service.list_jobs(ListJobsParams {
        county_id: None,
        username: None,
        status: None,
        limit: Some(1000),
        offset: Some(0),
    }).await {
        Ok(jobs) => {
            let total_jobs = jobs.total;
            let completed_jobs = jobs.jobs.iter()
                .filter(|j| j.status == "COMPLETED")
                .count() as i64;
            let failed_jobs = jobs.jobs.iter()
                .filter(|j| j.status == "FAILED")
                .count() as i64;
            let pending_jobs = jobs.jobs.iter()
                .filter(|j| j.status == "PENDING")
                .count() as i64;
            let processing_jobs = jobs.jobs.iter()
                .filter(|j| j.status == "PROCESSING")
                .count() as i64;

            serde_json::json!({
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "pending_jobs": pending_jobs,
                "processing_jobs": processing_jobs,
                "success_rate": if total_jobs > 0 { 
                    (completed_jobs as f64 / total_jobs as f64 * 100.0).round() 
                } else { 
                    0.0 
                }
            })
        }
        Err(_) => serde_json::json!({
            "total_jobs": 0,
            "error": "Unable to fetch job statistics"
        })
    };

    Ok(HttpResponse::Ok().json(serde_json::json!({
        "service": "TerraFusion GIS Export (Rust)",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "job_statistics": job_stats,
        "system": {
            "memory_usage": "N/A", // Could add system metrics here
            "cpu_usage": "N/A"
        }
    })))
}

/// Configure the routes for the GIS Export service
pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/gis-export")
            .route("/health", web::get().to(health_check))
            .route("/metrics", web::get().to(metrics))
            .route("/jobs", web::get().to(list_jobs))
            .route("/jobs", web::post().to(create_job))
            .route("/jobs/{job_id}", web::get().to(get_job_status))
            .route("/jobs/{job_id}/process", web::post().to(process_job))
            .route("/jobs/{job_id}/cancel", web::post().to(cancel_job))
            .route("/download/{job_id}", web::get().to(download_export))
    );
}