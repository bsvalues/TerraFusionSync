use common::error::{Error, Result};
use common::models::gis_export::{GisExport, CountyConfiguration, LayerDefinition};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Client for interacting with the GIS Export service
#[derive(Clone)]
pub struct GisExportClient {
    base_url: String,
    client: Client,
}

#[derive(Debug, Serialize, Deserialize)]
struct GisExportResponse {
    export: GisExport,
}

#[derive(Debug, Serialize, Deserialize)]
struct GisExportsResponse {
    exports: Vec<GisExport>,
    total_count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct ErrorResponse {
    error: String,
    status: u16,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateExportRequest {
    pub county_id: String,
    pub export_format: String,
    pub area_of_interest: Option<serde_json::Value>,
    pub layers: Vec<String>,
    pub parameters: serde_json::Value,
}

impl GisExportClient {
    pub fn new(base_url: &str, client: Client) -> Self {
        Self {
            base_url: base_url.to_string(),
            client,
        }
    }
    
    /// Get all GIS exports with optional filtering
    pub async fn get_exports(
        &self,
        county_id: Option<&str>,
        export_format: Option<&str>,
        status: Option<&str>,
        page: Option<i64>,
        per_page: Option<i64>,
    ) -> Result<(Vec<GisExport>, i64)> {
        // Build the URL with query parameters
        let mut url = format!("{}/exports", self.base_url);
        
        // Add query parameters if provided
        let mut query_params = Vec::new();
        
        if let Some(county) = county_id {
            query_params.push(format!("county_id={}", county));
        }
        
        if let Some(format) = export_format {
            query_params.push(format!("export_format={}", format));
        }
        
        if let Some(s) = status {
            query_params.push(format!("status={}", s));
        }
        
        if let Some(p) = page {
            query_params.push(format!("page={}", p));
        }
        
        if let Some(pp) = per_page {
            query_params.push(format!("per_page={}", pp));
        }
        
        if !query_params.is_empty() {
            url = format!("{}?{}", url, query_params.join("&"));
        }
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get GIS exports: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        // Parse the response
        let response: GisExportsResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse GIS exports response: {}", e)))?;
        
        Ok((response.exports, response.total_count))
    }
    
    /// Create a new GIS export
    pub async fn create_export(&self, req: CreateExportRequest) -> Result<GisExport> {
        let url = format!("{}/exports", self.base_url);
        
        // Make the request
        let response = self.client.post(&url)
            .json(&req)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to create GIS export: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        // Parse the response
        let response: GisExportResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse GIS export response: {}", e)))?;
        
        Ok(response.export)
    }
    
    /// Get a specific GIS export by ID
    pub async fn get_export(&self, id: Uuid) -> Result<GisExport> {
        let url = format!("{}/exports/{}", self.base_url, id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get GIS export: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        // Parse the response
        let response: GisExportResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse GIS export response: {}", e)))?;
        
        Ok(response.export)
    }
    
    /// Cancel a GIS export
    pub async fn cancel_export(&self, id: Uuid) -> Result<()> {
        let url = format!("{}/exports/{}/cancel", self.base_url, id);
        
        // Make the request
        let response = self.client.post(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to cancel GIS export: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        Ok(())
    }
    
    /// Download a GIS export
    pub async fn download_export(&self, id: Uuid) -> Result<Vec<u8>> {
        let url = format!("{}/exports/{}/download", self.base_url, id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to download GIS export: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
            
            return Err(Error::External(format!("GIS Export service error: {}", error_text)));
        }
        
        // Get the bytes
        let bytes = response.bytes().await
            .map_err(|e| Error::External(format!("Failed to read GIS export data: {}", e)))?;
        
        Ok(bytes.to_vec())
    }
    
    /// Get county configuration
    pub async fn get_county_config(&self, county_id: &str) -> Result<CountyConfiguration> {
        let url = format!("{}/counties/{}/config", self.base_url, county_id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get county configuration: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        // Parse the response
        let config: CountyConfiguration = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse county configuration response: {}", e)))?;
        
        Ok(config)
    }
    
    /// Get county layers
    pub async fn get_county_layers(&self, county_id: &str) -> Result<Vec<LayerDefinition>> {
        let url = format!("{}/counties/{}/layers", self.base_url, county_id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get county layers: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("GIS Export service error: {}", error.error)));
        }
        
        // Parse the response
        let layers: Vec<LayerDefinition> = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse county layers response: {}", e)))?;
        
        Ok(layers)
    }
    
    /// Check the health of the GIS Export service
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("{}/health", self.base_url);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to check GIS Export service health: {}", e)))?;
        
        // Check if the status is OK
        Ok(response.status().is_success())
    }
}