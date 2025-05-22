use common::error::{Error, Result};
use common::models::sync_operation::{SyncOperation, NewSyncOperation, SyncOperationUpdate};
use common::models::sync_pair::{SyncPair, NewSyncPair, SyncPairUpdate};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone)]
pub struct SyncServiceClient {
    base_url: String,
    client: reqwest::Client,
}

impl SyncServiceClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }
    
    // Sync Pair Operations
    
    pub async fn get_sync_pairs(
        &self,
        page: Option<i64>,
        per_page: Option<i64>,
        source_system: Option<&str>,
        target_system: Option<&str>,
        is_active: Option<bool>,
        county_id: Option<&str>,
    ) -> Result<(Vec<SyncPair>, i64)> {
        // Build query parameters
        let mut params = Vec::new();
        if let Some(p) = page {
            params.push(("page", p.to_string()));
        }
        if let Some(pp) = per_page {
            params.push(("per_page", pp.to_string()));
        }
        if let Some(ss) = source_system {
            params.push(("source_system", ss.to_string()));
        }
        if let Some(ts) = target_system {
            params.push(("target_system", ts.to_string()));
        }
        if let Some(ia) = is_active {
            params.push(("is_active", ia.to_string()));
        }
        if let Some(cid) = county_id {
            params.push(("county_id", cid.to_string()));
        }
        
        // Make request to SyncService
        let response = self.client
            .get(format!("{}/sync/pairs", self.base_url))
            .query(&params)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let sync_pairs = response_body.get("sync_pairs")
            .and_then(|v| serde_json::from_value::<Vec<SyncPair>>(v.clone()).ok())
            .unwrap_or_default();
            
        let total_count = response_body.get("total_count")
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
            
        Ok((sync_pairs, total_count))
    }
    
    pub async fn create_sync_pair(&self, new_pair: NewSyncPair) -> Result<SyncPair> {
        // Make request to SyncService
        let response = self.client
            .post(format!("{}/sync/pairs", self.base_url))
            .json(&new_pair)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let sync_pair = response_body.get("sync_pair")
            .and_then(|v| serde_json::from_value::<SyncPair>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(sync_pair)
    }
    
    pub async fn get_sync_pair(&self, id: Uuid) -> Result<SyncPair> {
        // Make request to SyncService
        let response = self.client
            .get(format!("{}/sync/pairs/{}", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("Sync pair not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let sync_pair = response_body.get("sync_pair")
            .and_then(|v| serde_json::from_value::<SyncPair>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(sync_pair)
    }
    
    pub async fn update_sync_pair(&self, id: Uuid, update: SyncPairUpdate) -> Result<SyncPair> {
        // Make request to SyncService
        let response = self.client
            .put(format!("{}/sync/pairs/{}", self.base_url, id))
            .json(&update)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("Sync pair not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let sync_pair = response_body.get("sync_pair")
            .and_then(|v| serde_json::from_value::<SyncPair>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(sync_pair)
    }
    
    // Sync Operation Methods
    
    pub async fn get_sync_operations(
        &self,
        page: Option<i64>,
        per_page: Option<i64>,
        sync_pair_id: Option<Uuid>,
        status: Option<&str>,
        created_by: Option<&str>,
        from_date: Option<&str>,
        to_date: Option<&str>,
    ) -> Result<(Vec<SyncOperation>, i64)> {
        // Build query parameters
        let mut params = Vec::new();
        if let Some(p) = page {
            params.push(("page", p.to_string()));
        }
        if let Some(pp) = per_page {
            params.push(("per_page", pp.to_string()));
        }
        if let Some(sp) = sync_pair_id {
            params.push(("sync_pair_id", sp.to_string()));
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
        
        // Make request to SyncService
        let response = self.client
            .get(format!("{}/sync/operations", self.base_url))
            .query(&params)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let operations = response_body.get("operations")
            .and_then(|v| serde_json::from_value::<Vec<SyncOperation>>(v.clone()).ok())
            .unwrap_or_default();
            
        let total_count = response_body.get("total_count")
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
            
        Ok((operations, total_count))
    }
    
    pub async fn create_sync_operation(&self, new_operation: NewSyncOperation) -> Result<SyncOperation> {
        // Make request to SyncService
        let response = self.client
            .post(format!("{}/sync/operations", self.base_url))
            .json(&new_operation)
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let operation = response_body.get("operation")
            .and_then(|v| serde_json::from_value::<SyncOperation>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(operation)
    }
    
    pub async fn get_sync_operation(&self, id: i32) -> Result<SyncOperation> {
        // Make request to SyncService
        let response = self.client
            .get(format!("{}/sync/operations/{}", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("Sync operation not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let operation = response_body.get("operation")
            .and_then(|v| serde_json::from_value::<SyncOperation>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(operation)
    }
    
    pub async fn cancel_sync_operation(&self, id: i32) -> Result<SyncOperation> {
        // Make request to SyncService
        let response = self.client
            .post(format!("{}/sync/operations/{}/cancel", self.base_url, id))
            .send()
            .await
            .map_err(|e| Error::InternalServer(format!("Failed to contact SyncService: {}", e)))?;
            
        if response.status() == reqwest::StatusCode::NOT_FOUND {
            return Err(Error::NotFound(format!("Sync operation not found: {}", id)));
        }
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await
                .unwrap_or_else(|_| "Unknown error".to_string());
                
            return Err(Error::InternalServer(format!(
                "SyncService returned error {}: {}",
                status,
                error_text
            )));
        }
        
        // Parse response
        let response_body = response.json::<serde_json::Value>().await
            .map_err(|e| Error::InternalServer(format!("Failed to parse SyncService response: {}", e)))?;
            
        let operation = response_body.get("operation")
            .and_then(|v| serde_json::from_value::<SyncOperation>(v.clone()).ok())
            .ok_or_else(|| Error::InternalServer("SyncService returned invalid response".to_string()))?;
            
        Ok(operation)
    }
}