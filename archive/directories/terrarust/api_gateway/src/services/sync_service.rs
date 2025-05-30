use common::error::{Error, Result};
use common::models::sync_operation::{
    SyncOperation, SyncPair, SyncDiff, SyncStats,
    CreateSyncOperationParams, CreateSyncPairParams
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Client for interacting with the SyncService
#[derive(Clone)]
pub struct SyncServiceClient {
    base_url: String,
    client: Client,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncOperationResponse {
    operation: SyncOperation,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncOperationsResponse {
    operations: Vec<SyncOperation>,
    total_count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncPairResponse {
    sync_pair: SyncPair,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncPairsResponse {
    sync_pairs: Vec<SyncPair>,
    total_count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncDiffResponse {
    diff: SyncDiff,
}

#[derive(Debug, Serialize, Deserialize)]
struct SyncDiffsResponse {
    diffs: Vec<SyncDiff>,
    total_count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct ErrorResponse {
    error: String,
    status: u16,
}

impl SyncServiceClient {
    pub fn new(base_url: &str, client: Client) -> Self {
        Self {
            base_url: base_url.to_string(),
            client,
        }
    }
    
    /// Get all sync operations with optional filtering
    pub async fn get_operations(
        &self,
        sync_pair_id: Option<Uuid>,
        county_id: Option<&str>,
        status: Option<&str>,
        page: Option<i64>,
        per_page: Option<i64>,
    ) -> Result<(Vec<SyncOperation>, i64)> {
        // Build the URL with query parameters
        let mut url = format!("{}/sync-operations", self.base_url);
        
        // Add query parameters if provided
        let mut query_params = Vec::new();
        
        if let Some(id) = sync_pair_id {
            query_params.push(format!("sync_pair_id={}", id));
        }
        
        if let Some(county) = county_id {
            query_params.push(format!("county_id={}", county));
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
            .map_err(|e| Error::External(format!("Failed to get sync operations: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncOperationsResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync operations response: {}", e)))?;
        
        Ok((response.operations, response.total_count))
    }
    
    /// Start a new sync operation
    pub async fn start_operation(&self, params: CreateSyncOperationParams) -> Result<SyncOperation> {
        let url = format!("{}/sync-operations", self.base_url);
        
        // Make the request
        let response = self.client.post(&url)
            .json(&params)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to start sync operation: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncOperationResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync operation response: {}", e)))?;
        
        Ok(response.operation)
    }
    
    /// Get a specific sync operation by ID
    pub async fn get_operation(&self, id: Uuid) -> Result<SyncOperation> {
        let url = format!("{}/sync-operations/{}", self.base_url, id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get sync operation: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncOperationResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync operation response: {}", e)))?;
        
        Ok(response.operation)
    }
    
    /// Cancel a sync operation
    pub async fn cancel_operation(&self, id: Uuid) -> Result<SyncOperation> {
        let url = format!("{}/sync-operations/{}/cancel", self.base_url, id);
        
        // Make the request
        let response = self.client.post(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to cancel sync operation: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncOperationResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync operation response: {}", e)))?;
        
        Ok(response.operation)
    }
    
    /// Get all sync pairs with optional filtering
    pub async fn get_sync_pairs(
        &self,
        county_id: Option<&str>,
        source_system: Option<&str>,
        target_system: Option<&str>,
        is_active: Option<bool>,
        page: Option<i64>,
        per_page: Option<i64>,
    ) -> Result<(Vec<SyncPair>, i64)> {
        // Build the URL with query parameters
        let mut url = format!("{}/sync-pairs", self.base_url);
        
        // Add query parameters if provided
        let mut query_params = Vec::new();
        
        if let Some(county) = county_id {
            query_params.push(format!("county_id={}", county));
        }
        
        if let Some(source) = source_system {
            query_params.push(format!("source_system={}", source));
        }
        
        if let Some(target) = target_system {
            query_params.push(format!("target_system={}", target));
        }
        
        if let Some(active) = is_active {
            query_params.push(format!("is_active={}", active));
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
            .map_err(|e| Error::External(format!("Failed to get sync pairs: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncPairsResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync pairs response: {}", e)))?;
        
        Ok((response.sync_pairs, response.total_count))
    }
    
    /// Create a new sync pair
    pub async fn create_sync_pair(&self, params: CreateSyncPairParams) -> Result<SyncPair> {
        let url = format!("{}/sync-pairs", self.base_url);
        
        // Make the request
        let response = self.client.post(&url)
            .json(&params)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to create sync pair: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncPairResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync pair response: {}", e)))?;
        
        Ok(response.sync_pair)
    }
    
    /// Get a specific sync pair by ID
    pub async fn get_sync_pair(&self, id: Uuid) -> Result<SyncPair> {
        let url = format!("{}/sync-pairs/{}", self.base_url, id);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get sync pair: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncPairResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync pair response: {}", e)))?;
        
        Ok(response.sync_pair)
    }
    
    /// Toggle a sync pair's active status
    pub async fn toggle_sync_pair(&self, id: Uuid, is_active: bool) -> Result<SyncPair> {
        let url = format!("{}/sync-pairs/{}/toggle", self.base_url, id);
        
        // Make the request
        let response = self.client.post(&url)
            .json(&serde_json::json!({
                "is_active": is_active
            }))
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to toggle sync pair: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncPairResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync pair response: {}", e)))?;
        
        Ok(response.sync_pair)
    }
    
    /// Get sync diffs for a specific operation
    pub async fn get_diffs(
        &self,
        operation_id: Uuid,
        entity_type: Option<&str>,
        change_type: Option<&str>,
        sync_status: Option<&str>,
        has_error: Option<bool>,
        page: Option<i64>,
        per_page: Option<i64>,
    ) -> Result<(Vec<SyncDiff>, i64)> {
        // Build the URL with query parameters
        let mut url = format!("{}/sync-diffs", self.base_url);
        
        // Add query parameters
        let mut query_params = vec![format!("sync_operation_id={}", operation_id)];
        
        if let Some(entity) = entity_type {
            query_params.push(format!("entity_type={}", entity));
        }
        
        if let Some(change) = change_type {
            query_params.push(format!("change_type={}", change));
        }
        
        if let Some(status) = sync_status {
            query_params.push(format!("sync_status={}", status));
        }
        
        if let Some(error) = has_error {
            query_params.push(format!("has_error={}", error));
        }
        
        if let Some(p) = page {
            query_params.push(format!("page={}", p));
        }
        
        if let Some(pp) = per_page {
            query_params.push(format!("per_page={}", pp));
        }
        
        url = format!("{}?{}", url, query_params.join("&"));
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to get sync diffs: {}", e)))?;
        
        // Check for errors
        if !response.status().is_success() {
            let error: ErrorResponse = response.json().await
                .map_err(|e| Error::External(format!("Failed to parse error response: {}", e)))?;
            
            return Err(Error::External(format!("SyncService error: {}", error.error)));
        }
        
        // Parse the response
        let response: SyncDiffsResponse = response.json().await
            .map_err(|e| Error::External(format!("Failed to parse sync diffs response: {}", e)))?;
        
        Ok((response.diffs, response.total_count))
    }
    
    /// Check the health of the SyncService
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("{}/health", self.base_url);
        
        // Make the request
        let response = self.client.get(&url)
            .send()
            .await
            .map_err(|e| Error::External(format!("Failed to check SyncService health: {}", e)))?;
        
        // Check if the status is OK
        Ok(response.status().is_success())
    }
}