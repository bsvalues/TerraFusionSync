use std::path::{Path, PathBuf};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use terrafusion_common::{Result, Error};
use terrafusion_common::models::geo::GisExportFormat;
use crate::config::Config;

/// File manager for handling export file operations
pub struct FileManager {
    config: Config,
}

impl FileManager {
    /// Create a new file manager
    pub fn new(config: Config) -> Self {
        Self { config }
    }
    
    /// Generate export file path
    pub fn generate_export_path(&self, export_id: Uuid, format: GisExportFormat) -> Result<PathBuf> {
        // Ensure exports directory exists
        self.config.ensure_directories()
            .map_err(|e| Error::Internal(format!("Failed to create directories: {}", e)))?;
        
        let extension = match format {
            GisExportFormat::Shapefile => "zip",
            GisExportFormat::GeoJson => "geojson",
            GisExportFormat::Kml => "kml",
            GisExportFormat::Csv => "csv",
            GisExportFormat::Gpkg => "gpkg",
            GisExportFormat::Geotiff => "tif",
            GisExportFormat::FileGdb => "zip",
        };
        
        let filename = format!("export_{}_{}.{}", 
            export_id.to_string().replace("-", ""), 
            Utc::now().format("%Y%m%d_%H%M%S"),
            extension
        );
        
        Ok(self.config.exports_directory.join(filename))
    }
    
    /// Generate download URL for an export
    pub fn generate_download_url(&self, export_id: Uuid, format: GisExportFormat) -> Result<String> {
        let extension = match format {
            GisExportFormat::Shapefile => "zip",
            GisExportFormat::GeoJson => "geojson",
            GisExportFormat::Kml => "kml",
            GisExportFormat::Csv => "csv",
            GisExportFormat::Gpkg => "gpkg",
            GisExportFormat::Geotiff => "tif",
            GisExportFormat::FileGdb => "zip",
        };
        
        // Generate a secure download path
        let filename = format!("export_{}.{}", export_id, extension);
        let download_url = format!("/exports/{}", filename);
        
        Ok(download_url)
    }
    
    /// Create temporary file path
    pub fn create_temp_path(&self, prefix: &str, extension: &str) -> Result<PathBuf> {
        // Ensure temp directory exists
        self.config.ensure_directories()
            .map_err(|e| Error::Internal(format!("Failed to create directories: {}", e)))?;
        
        let filename = format!("{}_{}.{}", 
            prefix, 
            Uuid::new_v4().to_string().replace("-", ""),
            extension
        );
        
        Ok(self.config.temp_directory.join(filename))
    }
    
    /// Clean up export files for a specific export
    pub async fn cleanup_export_files(&self, export_id: Uuid) -> Result<()> {
        let pattern = format!("export_{}", export_id);
        
        // Clean up from exports directory
        self.cleanup_files_with_pattern(&self.config.exports_directory, &pattern).await?;
        
        // Clean up from temp directory
        self.cleanup_files_with_pattern(&self.config.temp_directory, &pattern).await?;
        
        Ok(())
    }
    
    /// Clean up old export files based on age
    pub async fn cleanup_old_exports(&self) -> Result<usize> {
        let cutoff_time = Utc::now() - chrono::Duration::from_std(self.config.cleanup_age())
            .map_err(|e| Error::Internal(format!("Invalid cleanup age: {}", e)))?;
        
        let mut cleaned_count = 0;
        
        // Clean up exports directory
        cleaned_count += self.cleanup_old_files_in_directory(&self.config.exports_directory, cutoff_time).await?;
        
        // Clean up temp directory
        cleaned_count += self.cleanup_old_files_in_directory(&self.config.temp_directory, cutoff_time).await?;
        
        Ok(cleaned_count)
    }
    
    /// Get file size in bytes
    pub fn get_file_size(&self, path: &Path) -> Result<u64> {
        std::fs::metadata(path)
            .map(|metadata| metadata.len())
            .map_err(|e| Error::Internal(format!("Failed to get file size: {}", e)))
    }
    
    /// Check if file exists
    pub fn file_exists(&self, path: &Path) -> bool {
        path.exists() && path.is_file()
    }
    
    /// Validate file size against limits
    pub fn validate_file_size(&self, path: &Path) -> Result<()> {
        let file_size = self.get_file_size(path)?;
        let max_size = self.config.max_export_size_bytes();
        
        if file_size > max_size {
            return Err(Error::Validation(format!(
                "Export file size ({} bytes) exceeds maximum allowed size ({} bytes)",
                file_size, max_size
            )));
        }
        
        Ok(())
    }
    
    /// Create a secure download token for file access
    pub fn create_download_token(&self, export_id: Uuid, expires_at: DateTime<Utc>) -> String {
        // Simple token generation - in production, use proper JWT or similar
        format!("{}_{}", export_id, expires_at.timestamp())
    }
    
    /// Validate download token
    pub fn validate_download_token(&self, token: &str, export_id: Uuid) -> Result<bool> {
        let parts: Vec<&str> = token.split('_').collect();
        if parts.len() != 2 {
            return Ok(false);
        }
        
        let token_export_id = parts[0];
        let expires_timestamp = parts[1].parse::<i64>().unwrap_or(0);
        
        // Check if export ID matches
        if token_export_id != export_id.to_string() {
            return Ok(false);
        }
        
        // Check if token has expired
        let expires_at = DateTime::from_timestamp(expires_timestamp, 0)
            .ok_or_else(|| Error::Internal("Invalid timestamp in token".to_string()))?;
        
        if Utc::now() > expires_at {
            return Ok(false);
        }
        
        Ok(true)
    }
    
    /// Helper function to clean up files with a specific pattern
    async fn cleanup_files_with_pattern(&self, directory: &Path, pattern: &str) -> Result<()> {
        if !directory.exists() {
            return Ok(());
        }
        
        let entries = std::fs::read_dir(directory)
            .map_err(|e| Error::Internal(format!("Failed to read directory: {}", e)))?;
        
        for entry in entries {
            let entry = entry
                .map_err(|e| Error::Internal(format!("Failed to read directory entry: {}", e)))?;
            
            let file_name = entry.file_name();
            if let Some(name_str) = file_name.to_str() {
                if name_str.contains(pattern) {
                    if let Err(e) = std::fs::remove_file(entry.path()) {
                        log::warn!("Failed to remove file {:?}: {}", entry.path(), e);
                    } else {
                        log::debug!("Cleaned up file: {:?}", entry.path());
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Helper function to clean up old files in a directory
    async fn cleanup_old_files_in_directory(&self, directory: &Path, cutoff_time: DateTime<Utc>) -> Result<usize> {
        if !directory.exists() {
            return Ok(0);
        }
        
        let mut cleaned_count = 0;
        
        let entries = std::fs::read_dir(directory)
            .map_err(|e| Error::Internal(format!("Failed to read directory: {}", e)))?;
        
        for entry in entries {
            let entry = entry
                .map_err(|e| Error::Internal(format!("Failed to read directory entry: {}", e)))?;
            
            let metadata = entry.metadata()
                .map_err(|e| Error::Internal(format!("Failed to get file metadata: {}", e)))?;
            
            if let Ok(modified) = metadata.modified() {
                let modified_utc = DateTime::<Utc>::from(modified);
                
                if modified_utc < cutoff_time {
                    if let Err(e) = std::fs::remove_file(entry.path()) {
                        log::warn!("Failed to remove old file {:?}: {}", entry.path(), e);
                    } else {
                        log::debug!("Cleaned up old file: {:?}", entry.path());
                        cleaned_count += 1;
                    }
                }
            }
        }
        
        Ok(cleaned_count)
    }
}