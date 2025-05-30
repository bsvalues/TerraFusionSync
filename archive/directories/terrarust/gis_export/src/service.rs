use crate::models::*;
use crate::{ExportFormat, GisExportConfig};
use sqlx::{PgPool, Row};
use uuid::Uuid;
use chrono::Utc;
use std::path::PathBuf;
use tokio::fs;
use std::collections::HashMap;
use anyhow::{Result, anyhow};

/// High-performance GIS Export Service
pub struct GisExportService {
    config: GisExportConfig,
    db_pool: PgPool,
}

impl GisExportService {
    /// Create a new GIS Export Service instance
    pub async fn new(config: GisExportConfig, db_pool: PgPool) -> Result<Self> {
        // Ensure storage directory exists
        fs::create_dir_all(&config.storage_path).await?;
        
        // Test database connection
        sqlx::query("SELECT 1").execute(&db_pool).await?;
        
        log::info!("GIS Export Service initialized with storage path: {:?}", config.storage_path);
        
        Ok(Self {
            config,
            db_pool,
        })
    }

    /// Create a new export job
    pub async fn create_job(&self, request: CreateJobRequest) -> Result<CreateJobResponse> {
        // Validate export format
        let export_format: ExportFormat = request.export_format.parse()
            .map_err(|e| anyhow!("Invalid export format: {}", e))?;

        // Validate layers
        if request.layers.is_empty() {
            return Err(anyhow!("At least one layer must be specified"));
        }

        // Generate unique job ID
        let job_id = Uuid::new_v4();
        let now = Utc::now();

        // Convert layers to JSON
        let layers_json = serde_json::to_value(&request.layers)?;
        let parameters_json = request.parameters.map(|p| serde_json::to_value(p)).transpose()?;

        // Insert job into database
        let job = sqlx::query_as::<_, GisExportJob>(
            r#"
            INSERT INTO gis_export_jobs (
                job_id, county_id, username, export_format, area_of_interest, 
                layers, parameters, status, message, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            "#
        )
        .bind(job_id)
        .bind(&request.county_id)
        .bind(&request.username)
        .bind(export_format.as_str())
        .bind(&request.area_of_interest)
        .bind(layers_json)
        .bind(parameters_json)
        .bind("PENDING")
        .bind("Export job created and queued for processing")
        .bind(now)
        .fetch_one(&self.db_pool)
        .await?;

        log::info!("Created GIS export job {} for county {}", job_id, request.county_id);
        
        Ok(job.into())
    }

    /// Get job status by ID
    pub async fn get_job_status(&self, job_id: Uuid) -> Result<JobStatusResponse> {
        let job = sqlx::query_as::<_, GisExportJob>(
            "SELECT * FROM gis_export_jobs WHERE job_id = $1"
        )
        .bind(job_id)
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| anyhow!("Job not found: {}", job_id))?;

        Ok(job.into())
    }

    /// List jobs with optional filtering
    pub async fn list_jobs(&self, params: ListJobsParams) -> Result<JobListResponse> {
        let limit = params.limit.unwrap_or(50).min(1000); // Cap at 1000
        let offset = params.offset.unwrap_or(0);

        // Build dynamic query with filters
        let mut query = "SELECT * FROM gis_export_jobs WHERE 1=1".to_string();
        let mut bind_count = 0;
        let mut binds: Vec<Box<dyn sqlx::Encode<'_, sqlx::Postgres> + Send + 'static>> = Vec::new();

        if let Some(county_id) = &params.county_id {
            bind_count += 1;
            query.push_str(&format!(" AND county_id = ${}", bind_count));
            binds.push(Box::new(county_id.clone()));
        }

        if let Some(username) = &params.username {
            bind_count += 1;
            query.push_str(&format!(" AND username = ${}", bind_count));
            binds.push(Box::new(username.clone()));
        }

        if let Some(status) = &params.status {
            bind_count += 1;
            query.push_str(&format!(" AND status = ${}", bind_count));
            binds.push(Box::new(status.clone()));
        }

        query.push_str(" ORDER BY created_at DESC");
        
        bind_count += 1;
        query.push_str(&format!(" LIMIT ${}", bind_count));
        binds.push(Box::new(limit));
        
        bind_count += 1;
        query.push_str(&format!(" OFFSET ${}", bind_count));
        binds.push(Box::new(offset));

        // Execute query (simplified for now - in production would use proper parameter binding)
        let jobs = sqlx::query_as::<_, GisExportJob>(&query)
            .fetch_all(&self.db_pool)
            .await?;

        // Get total count for pagination
        let total_query = "SELECT COUNT(*) as count FROM gis_export_jobs WHERE 1=1".to_string();
        let total: i64 = sqlx::query(&total_query)
            .fetch_one(&self.db_pool)
            .await?
            .get("count");

        let job_responses: Vec<JobStatusResponse> = jobs.into_iter().map(|job| job.into()).collect();

        Ok(JobListResponse {
            jobs: job_responses,
            total,
            limit,
            offset,
        })
    }

    /// Process an export job
    pub async fn process_job(&self, job_id: Uuid) -> Result<JobStatusResponse> {
        // Load job
        let mut job = sqlx::query_as::<_, GisExportJob>(
            "SELECT * FROM gis_export_jobs WHERE job_id = $1"
        )
        .bind(job_id)
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| anyhow!("Job not found: {}", job_id))?;

        // Validate job can be processed
        if job.status != "PENDING" {
            return Err(anyhow!("Job {} is not in PENDING status", job_id));
        }

        // Update job to PROCESSING
        sqlx::query(
            "UPDATE gis_export_jobs SET status = $1, started_at = $2, message = $3 WHERE job_id = $4"
        )
        .bind("PROCESSING")
        .bind(Utc::now())
        .bind("Processing export...")
        .bind(job_id)
        .execute(&self.db_pool)
        .await?;

        log::info!("Processing GIS export job {}", job_id);

        // Process the export
        match self.generate_export(&job).await {
            Ok((file_path, file_size)) => {
                // Update job as completed
                let download_url = format!("/api/v1/gis-export/download/{}", job_id);
                
                sqlx::query(
                    r#"
                    UPDATE gis_export_jobs 
                    SET status = $1, completed_at = $2, message = $3, file_path = $4, 
                        file_size = $5, download_url = $6 
                    WHERE job_id = $7
                    "#
                )
                .bind("COMPLETED")
                .bind(Utc::now())
                .bind("Export completed successfully")
                .bind(file_path.to_string_lossy().to_string())
                .bind(file_size as i64)
                .bind(download_url)
                .bind(job_id)
                .execute(&self.db_pool)
                .await?;

                log::info!("Completed GIS export job {}", job_id);
            }
            Err(e) => {
                // Update job as failed
                sqlx::query(
                    "UPDATE gis_export_jobs SET status = $1, completed_at = $2, message = $3 WHERE job_id = $4"
                )
                .bind("FAILED")
                .bind(Utc::now())
                .bind(format!("Export failed: {}", e))
                .bind(job_id)
                .execute(&self.db_pool)
                .await?;

                log::error!("Failed GIS export job {}: {}", job_id, e);
                return Err(e);
            }
        }

        // Return updated job status
        self.get_job_status(job_id).await
    }

    /// Cancel a job
    pub async fn cancel_job(&self, job_id: Uuid) -> Result<JobStatusResponse> {
        let job = sqlx::query_as::<_, GisExportJob>(
            "SELECT * FROM gis_export_jobs WHERE job_id = $1"
        )
        .bind(job_id)
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| anyhow!("Job not found: {}", job_id))?;

        if job.status == "COMPLETED" {
            return Err(anyhow!("Cannot cancel completed job"));
        }

        sqlx::query(
            "UPDATE gis_export_jobs SET status = $1, completed_at = $2, message = $3 WHERE job_id = $4"
        )
        .bind("CANCELLED")
        .bind(Utc::now())
        .bind("Job cancelled by user")
        .bind(job_id)
        .execute(&self.db_pool)
        .await?;

        log::info!("Cancelled GIS export job {}", job_id);
        
        self.get_job_status(job_id).await
    }

    /// Generate the actual export file
    async fn generate_export(&self, job: &GisExportJob) -> Result<(PathBuf, u64)> {
        let export_format: ExportFormat = job.export_format.parse()?;
        let layers: Vec<String> = serde_json::from_value(job.layers.clone())?;

        // Create filename
        let filename = format!("{}_{}.{}", 
            job.county_id, 
            job.job_id.simple(),
            export_format.file_extension()
        );
        let file_path = self.config.storage_path.join(&filename);

        // Query geospatial data from database
        let features = self.query_features(job, &layers).await?;

        // Generate export based on format
        match export_format {
            ExportFormat::Geojson => {
                self.generate_geojson(&file_path, &features).await?;
            }
            ExportFormat::Csv => {
                self.generate_csv(&file_path, &features).await?;
            }
            ExportFormat::Shapefile => {
                self.generate_shapefile(&file_path, &features).await?;
            }
            ExportFormat::Kml => {
                self.generate_kml(&file_path, &features).await?;
            }
            ExportFormat::Geopackage => {
                self.generate_geopackage(&file_path, &features).await?;
            }
        }

        // Get file size
        let metadata = fs::metadata(&file_path).await?;
        let file_size = metadata.len();

        Ok((file_path, file_size))
    }

    /// Query features from database
    async fn query_features(&self, job: &GisExportJob, layers: &[String]) -> Result<Vec<HashMap<String, serde_json::Value>>> {
        // For demonstration, generate sample data
        // In production, this would query your actual geospatial database
        let mut features = Vec::new();
        
        for (i, layer) in layers.iter().enumerate() {
            for j in 0..100 { // Generate 100 sample features per layer
                let mut feature = HashMap::new();
                feature.insert("id".to_string(), serde_json::Value::Number((i * 100 + j).into()));
                feature.insert("layer".to_string(), serde_json::Value::String(layer.clone()));
                feature.insert("county_id".to_string(), serde_json::Value::String(job.county_id.clone()));
                feature.insert("geometry".to_string(), serde_json::json!({
                    "type": "Point",
                    "coordinates": [-119.0 + (j as f64 * 0.001), 46.0 + (i as f64 * 0.001)]
                }));
                features.push(feature);
            }
        }

        log::info!("Queried {} features for export", features.len());
        Ok(features)
    }

    /// Generate GeoJSON export
    async fn generate_geojson(&self, file_path: &PathBuf, features: &[HashMap<String, serde_json::Value>]) -> Result<()> {
        let geojson = serde_json::json!({
            "type": "FeatureCollection",
            "features": features.iter().map(|f| {
                serde_json::json!({
                    "type": "Feature",
                    "geometry": f.get("geometry").unwrap_or(&serde_json::Value::Null),
                    "properties": f.iter()
                        .filter(|(k, _)| *k != "geometry")
                        .collect::<HashMap<_, _>>()
                })
            }).collect::<Vec<_>>()
        });

        fs::write(file_path, serde_json::to_string_pretty(&geojson)?).await?;
        Ok(())
    }

    /// Generate CSV export
    async fn generate_csv(&self, file_path: &PathBuf, features: &[HashMap<String, serde_json::Value>]) -> Result<()> {
        if features.is_empty() {
            fs::write(file_path, "").await?;
            return Ok(());
        }

        // Get all unique column names
        let mut columns: std::collections::HashSet<String> = std::collections::HashSet::new();
        for feature in features {
            for key in feature.keys() {
                if key != "geometry" { // Skip geometry for CSV
                    columns.insert(key.clone());
                }
            }
        }
        let mut columns: Vec<String> = columns.into_iter().collect();
        columns.sort();

        // Build CSV content
        let mut csv_content = columns.join(",") + "\n";
        for feature in features {
            let row: Vec<String> = columns.iter().map(|col| {
                feature.get(col)
                    .map(|v| match v {
                        serde_json::Value::String(s) => format!("\"{}\"", s.replace("\"", "\"\"")),
                        serde_json::Value::Number(n) => n.to_string(),
                        serde_json::Value::Bool(b) => b.to_string(),
                        _ => "".to_string(),
                    })
                    .unwrap_or_default()
            }).collect();
            csv_content.push_str(&(row.join(",") + "\n"));
        }

        fs::write(file_path, csv_content).await?;
        Ok(())
    }

    /// Generate Shapefile export (placeholder)
    async fn generate_shapefile(&self, file_path: &PathBuf, features: &[HashMap<String, serde_json::Value>]) -> Result<()> {
        // For now, create a simple ZIP with GeoJSON
        // In production, you'd use GDAL or similar to create proper shapefiles
        let geojson_path = file_path.with_extension("geojson");
        self.generate_geojson(&geojson_path, features).await?;
        
        // Create simple ZIP file (placeholder implementation)
        fs::write(file_path, "Shapefile export placeholder").await?;
        Ok(())
    }

    /// Generate KML export (placeholder)
    async fn generate_kml(&self, file_path: &PathBuf, features: &[HashMap<String, serde_json::Value>]) -> Result<()> {
        fs::write(file_path, "KML export placeholder").await?;
        Ok(())
    }

    /// Generate GeoPackage export (placeholder)
    async fn generate_geopackage(&self, file_path: &PathBuf, features: &[HashMap<String, serde_json::Value>]) -> Result<()> {
        fs::write(file_path, "GeoPackage export placeholder").await?;
        Ok(())
    }

    /// Get file path for download
    pub async fn get_export_file(&self, job_id: Uuid) -> Result<PathBuf> {
        let job = sqlx::query_as::<_, GisExportJob>(
            "SELECT * FROM gis_export_jobs WHERE job_id = $1"
        )
        .bind(job_id)
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| anyhow!("Job not found: {}", job_id))?;

        if job.status != "COMPLETED" {
            return Err(anyhow!("Export not ready for download"));
        }

        let file_path = job.file_path
            .ok_or_else(|| anyhow!("No file path available"))?;
        
        let path = PathBuf::from(file_path);
        if !path.exists() {
            return Err(anyhow!("Export file not found"));
        }

        Ok(path)
    }
}