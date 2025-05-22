use common::error::{Error, Result};
use common::models::gis_export::{CountyConfiguration, GisExport, NewGisExport, GisExportUpdate};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone)]
pub struct GisExportClient {
    base_url: String,
    client: reqwest::Client,
}

impl GisExportClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }
    
    pub async fn get_exports(
        &self,
        page: Option<i64>,
        per_page: Option<i64>,
        county_id: Option<&str>,
        export_format: Option<&str>,
        status: Option<&str>,
        created_by: Option<&str>,
        from_date: Option<&str>,
        to_date: Option<&str>,
    ) -> Result<(Vec<GisExport>, i64)> {
        // Build query parameters
        let mut params = Vec::new();
        if let Some(p) = page {
            params.push(("page", p.to_string()));
        }
        if let Some(pp) = per_page {
            params.push(("per_page", pp.to_string()));
        }
        if let Some(cid) = county_id {
            params.push(("county_id", cid.to_string()));
        }
        if let Some(fmt) = export_format {
            params.push(("export_format", fmt.to_string()));
        }
        if let Some(s) = status {
            params.push(("status", s.to_string()));
        }
        if let Some(cb) = created_by {
            params.push(("created_by", cb.to_string()));
        }
        if let Some(fd) = from_date {
            params.push(("from_date", fd.to_string()));
        }
        if let Some(td) = to_date {
            params.push(("to_date", td.to_string()));
        }
        
        // Make request to GIS Export service
        let response = self.client
            .get(format!("{}/exports", self.base_url))
            .query(&params)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse GIS Export service response: {}", e)))?;
            
        let exports = response_body.get("exports")
            .and_then(|v| serde_json::from_value::<Vec<GisExport>>(v.clone()).ok())
            .unwrap_or_default();
            
        let total_count = response_body.get("total_count")
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
            
        Ok((exports, total_count))
    }
    
    pub async fn create_export(
        &self,
        county_id: &str,
        export_format: &str,
        area_of_interest: Option<serde_json::Value>,
        layers: Vec<String>,
        parameters: serde_json::Value,
        created_by: &str,
    ) -> Result<GisExport> {
        // Create request payload
        let layers_json = serde_json::to_value(&layers).unwrap_or(serde_json::Value::Array(vec![]));
        
        let new_export = NewGisExport {
            county_id: county_id.to_string(),
            export_format: export_format.to_string(),
            status: "pending".to_string(),
            area_of_interest,
            layers: layers_json,
            parameters,
            created_by: created_by.to_string(),
        };
        
        // Make request to GIS Export service
        let response = self.client
            .post(format!("{}/exports", self.base_url))
            .json(&new_export)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse GIS Export service response: {}", e)))?;
            
        let export = response_body.get("export")
            .and_then(|v| serde_json::from_value::<GisExport>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("GIS Export service returned invalid response".to_string()))?;
            
        Ok(export)
    }
    
    pub async fn get_export(&self, id: Uuid) -> Result<GisExport> {
        // Make request to GIS Export service
        let response = self.client
            .get(format!("{}/exports/{}", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("GIS export not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse GIS Export service response: {}", e)))?;
            
        let export = response_body.get("export")
            .and_then(|v| serde_json::from_value::<GisExport>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("GIS Export service returned invalid response".to_string()))?;
            
        Ok(export)
    }
    
    pub async fn cancel_export(&self, id: Uuid) -> Result<GisExport> {
        // Make request to GIS Export service
        let response = self.client
            .post(format!("{}/exports/{}/cancel", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("GIS export not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse GIS Export service response: {}", e)))?;
            
        let export = response_body.get("export")
            .and_then(|v| serde_json::from_value::<GisExport>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("GIS Export service returned invalid response".to_string()))?;
            
        Ok(export)
    }
    
    pub async fn get_county_config(&self, county_id: &str) -> Result<CountyConfiguration> {
        // Make request to GIS Export service
        let response = self.client
            .get(format!("{}/counties/{}/config", self.base_url, county_id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("County configuration not found: {}", county_id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let county_config = response.json::<CountyConfiguration>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse GIS Export service response: {}", e)))?;
            
        Ok(county_config)
    }
    
    pub async fn download_export(&self, id: Uuid) -> Result<Vec<u8>> {
        // Make request to GIS Export service
        let response = self.client
            .get(format!("{}/exports/{}/download", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact GIS Export service: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("GIS export not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "GIS Export service returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Get response bytes
        let bytes = response.bytes().await
            .map_err(|e| Error::InternalServer(format!("Failed to download export file: {}", e)))?;
            
        Ok(bytes.to_vec())
    }
}