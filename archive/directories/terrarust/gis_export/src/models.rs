use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use crate::ExportFormat;

/// Status of a GIS export job
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, sqlx::Type)]
#[serde(rename_all = "UPPERCASE")]
#[sqlx(type_name = "text")]
pub enum JobStatus {
    Pending,
    Processing,
    Completed,
    Failed,
    Cancelled,
}

impl std::fmt::Display for JobStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            JobStatus::Pending => write!(f, "PENDING"),
            JobStatus::Processing => write!(f, "PROCESSING"),
            JobStatus::Completed => write!(f, "COMPLETED"),
            JobStatus::Failed => write!(f, "FAILED"),
            JobStatus::Cancelled => write!(f, "CANCELLED"),
        }
    }
}

/// GIS Export Job model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct GisExportJob {
    pub id: i32,
    pub job_id: Uuid,
    pub county_id: String,
    pub username: String,
    pub export_format: String,
    pub area_of_interest: serde_json::Value,
    pub layers: serde_json::Value,
    pub parameters: Option<serde_json::Value>,
    pub status: String,
    pub message: Option<String>,
    pub file_path: Option<String>,
    pub file_size: Option<i64>,
    pub download_url: Option<String>,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
}

/// Request to create a new GIS export job
#[derive(Debug, Deserialize)]
pub struct CreateJobRequest {
    pub county_id: String,
    pub username: String,
    pub export_format: String,
    pub area_of_interest: serde_json::Value,
    pub layers: Vec<String>,
    pub parameters: Option<HashMap<String, serde_json::Value>>,
}

/// Response when creating a GIS export job
#[derive(Debug, Serialize)]
pub struct CreateJobResponse {
    pub job_id: Uuid,
    pub county_id: String,
    pub username: String,
    pub export_format: String,
    pub area_of_interest: serde_json::Value,
    pub layers: serde_json::Value,
    pub parameters: Option<serde_json::Value>,
    pub status: String,
    pub message: String,
    pub created_at: DateTime<Utc>,
}

/// Job status response
#[derive(Debug, Serialize)]
pub struct JobStatusResponse {
    pub job_id: Uuid,
    pub county_id: String,
    pub username: String,
    pub export_format: String,
    pub status: String,
    pub message: Option<String>,
    pub file_path: Option<String>,
    pub file_size: Option<i64>,
    pub download_url: Option<String>,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub progress_percent: Option<f32>,
}

/// List of export jobs with filtering
#[derive(Debug, Serialize)]
pub struct JobListResponse {
    pub jobs: Vec<JobStatusResponse>,
    pub total: i64,
    pub limit: i64,
    pub offset: i64,
}

/// Parameters for listing jobs
#[derive(Debug, Deserialize)]
pub struct ListJobsParams {
    pub county_id: Option<String>,
    pub username: Option<String>,
    pub status: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

impl From<GisExportJob> for JobStatusResponse {
    fn from(job: GisExportJob) -> Self {
        Self {
            job_id: job.job_id,
            county_id: job.county_id,
            username: job.username,
            export_format: job.export_format,
            status: job.status,
            message: job.message,
            file_path: job.file_path,
            file_size: job.file_size,
            download_url: job.download_url,
            created_at: job.created_at,
            started_at: job.started_at,
            completed_at: job.completed_at,
            progress_percent: None, // Calculate based on status if needed
        }
    }
}

impl From<GisExportJob> for CreateJobResponse {
    fn from(job: GisExportJob) -> Self {
        Self {
            job_id: job.job_id,
            county_id: job.county_id,
            username: job.username,
            export_format: job.export_format,
            area_of_interest: job.area_of_interest,
            layers: job.layers,
            parameters: job.parameters,
            status: job.status,
            message: job.message.unwrap_or_else(|| "Export job created successfully".to_string()),
            created_at: job.created_at,
        }
    }
}

/// Export processing statistics
#[derive(Debug, Serialize, Deserialize)]
pub struct ExportStats {
    pub records_processed: u64,
    pub features_exported: u64,
    pub file_size_bytes: u64,
    pub processing_time_seconds: f64,
}

/// Area of Interest geometry types
#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum AreaOfInterest {
    Point {
        coordinates: [f64; 2],
    },
    Polygon {
        coordinates: Vec<Vec<[f64; 2]>>,
    },
    BoundingBox {
        min_x: f64,
        min_y: f64,
        max_x: f64,
        max_y: f64,
    },
}

/// Layer configuration for exports
#[derive(Debug, Serialize, Deserialize)]
pub struct LayerConfig {
    pub name: String,
    pub table_name: String,
    pub geometry_column: String,
    pub attributes: Vec<String>,
    pub filters: Option<HashMap<String, serde_json::Value>>,
}