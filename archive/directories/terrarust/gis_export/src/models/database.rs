use sqlx::{FromRow, Type};
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Database model for GIS exports
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct GisExportRow {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub county_id: String,
    pub export_format: String,
    pub status: String,
    pub layers: serde_json::Value,
    pub area_of_interest: Option<serde_json::Value>,
    pub parameters: serde_json::Value,
    pub created_by: String,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub result_url: Option<String>,
    pub error_message: Option<String>,
    pub file_size_bytes: Option<i64>,
}

/// Database model for GIS layers
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct GisLayerRow {
    pub id: String,
    pub name: String,
    pub description: String,
    pub geometry_type: String,
    pub is_enabled: bool,
    pub county_id: String,
    pub source_table: Option<String>,
    pub source_query: Option<String>,
    pub style: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Database model for county GIS configuration
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct CountyGisConfigRow {
    pub county_id: String,
    pub name: String,
    pub supported_formats: serde_json::Value,
    pub default_projection: String,
    pub available_projections: serde_json::Value,
    pub max_export_area_sq_km: Option<f64>,
    pub max_export_features: Option<i32>,
    pub default_parameters: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Database queries for GIS exports
pub struct GisExportQueries;

impl GisExportQueries {
    /// Create a new GIS export
    pub async fn create(
        pool: &sqlx::PgPool,
        export: &GisExportRow,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            INSERT INTO gis_exports (
                id, created_at, updated_at, county_id, export_format, status,
                layers, area_of_interest, parameters, created_by, started_at,
                completed_at, result_url, error_message, file_size_bytes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            "#,
            export.id,
            export.created_at,
            export.updated_at,
            export.county_id,
            export.export_format,
            export.status,
            export.layers,
            export.area_of_interest,
            export.parameters,
            export.created_by,
            export.started_at,
            export.completed_at,
            export.result_url,
            export.error_message,
            export.file_size_bytes
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Update GIS export status
    pub async fn update_status(
        pool: &sqlx::PgPool,
        export_id: Uuid,
        status: &str,
        completed_at: Option<DateTime<Utc>>,
        result_url: Option<&str>,
        error_message: Option<&str>,
        file_size_bytes: Option<i64>,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE gis_exports 
            SET status = $2, completed_at = $3, result_url = $4, 
                error_message = $5, file_size_bytes = $6, updated_at = NOW()
            WHERE id = $1
            "#,
            export_id,
            status,
            completed_at,
            result_url,
            error_message,
            file_size_bytes
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Get GIS export by ID
    pub async fn get_by_id(
        pool: &sqlx::PgPool,
        export_id: Uuid,
    ) -> Result<Option<GisExportRow>, sqlx::Error> {
        let export = sqlx::query_as!(
            GisExportRow,
            "SELECT * FROM gis_exports WHERE id = $1",
            export_id
        )
        .fetch_optional(pool)
        .await?;
        
        Ok(export)
    }
    
    /// List GIS exports with pagination and filtering
    pub async fn list(
        pool: &sqlx::PgPool,
        county_id: Option<&str>,
        status: Option<&str>,
        offset: i64,
        limit: i64,
    ) -> Result<Vec<GisExportRow>, sqlx::Error> {
        let exports = sqlx::query_as!(
            GisExportRow,
            r#"
            SELECT * FROM gis_exports 
            WHERE ($1::text IS NULL OR county_id = $1)
            AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            "#,
            county_id,
            status,
            limit,
            offset
        )
        .fetch_all(pool)
        .await?;
        
        Ok(exports)
    }
    
    /// Delete old exports
    pub async fn delete_old_exports(
        pool: &sqlx::PgPool,
        cutoff_date: DateTime<Utc>,
    ) -> Result<i64, sqlx::Error> {
        let result = sqlx::query!(
            "DELETE FROM gis_exports WHERE created_at < $1",
            cutoff_date
        )
        .execute(pool)
        .await?;
        
        Ok(result.rows_affected() as i64)
    }
}

/// Database queries for GIS layers
pub struct GisLayerQueries;

impl GisLayerQueries {
    /// Get layers for a county
    pub async fn get_by_county(
        pool: &sqlx::PgPool,
        county_id: &str,
    ) -> Result<Vec<GisLayerRow>, sqlx::Error> {
        let layers = sqlx::query_as!(
            GisLayerRow,
            "SELECT * FROM gis_layers WHERE county_id = $1 AND is_enabled = true ORDER BY name",
            county_id
        )
        .fetch_all(pool)
        .await?;
        
        Ok(layers)
    }
    
    /// Get layer by ID and county
    pub async fn get_by_id(
        pool: &sqlx::PgPool,
        layer_id: &str,
        county_id: &str,
    ) -> Result<Option<GisLayerRow>, sqlx::Error> {
        let layer = sqlx::query_as!(
            GisLayerRow,
            "SELECT * FROM gis_layers WHERE id = $1 AND county_id = $2",
            layer_id,
            county_id
        )
        .fetch_optional(pool)
        .await?;
        
        Ok(layer)
    }
}

/// Database queries for county GIS configuration
pub struct CountyGisConfigQueries;

impl CountyGisConfigQueries {
    /// Get county configuration
    pub async fn get_by_county(
        pool: &sqlx::PgPool,
        county_id: &str,
    ) -> Result<Option<CountyGisConfigRow>, sqlx::Error> {
        let config = sqlx::query_as!(
            CountyGisConfigRow,
            "SELECT * FROM county_gis_configs WHERE county_id = $1",
            county_id
        )
        .fetch_optional(pool)
        .await?;
        
        Ok(config)
    }
    
    /// List all county configurations
    pub async fn list_all(
        pool: &sqlx::PgPool,
    ) -> Result<Vec<CountyGisConfigRow>, sqlx::Error> {
        let configs = sqlx::query_as!(
            CountyGisConfigRow,
            "SELECT * FROM county_gis_configs ORDER BY name"
        )
        .fetch_all(pool)
        .await?;
        
        Ok(configs)
    }
}