use common::error::{Error, Result};
use common::database::Database;
use common::telemetry::TelemetryService;
use common::models::sync_pair::SyncPair;
use common::models::sync_operation::SyncOperation;
use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::Instant;
use tokio::sync::RwLock;
use uuid::Uuid;
use chrono::Utc;
use std::time::Duration;
use prometheus::Histogram;

/// The SyncEngine is responsible for executing data synchronization operations
/// between source and target systems based on configured sync pairs.
#[derive(Clone)]
pub struct SyncEngine {
    database: Database,
    telemetry: Arc<TelemetryService>,
    active_operations: Arc<RwLock<HashSet<i32>>>,
    cancellation_requests: Arc<RwLock<HashSet<i32>>>,
}

impl SyncEngine {
    pub fn new(database: Database, telemetry: Arc<TelemetryService>) -> Self {
        Self {
            database,
            telemetry,
            active_operations: Arc::new(RwLock::new(HashSet::new())),
            cancellation_requests: Arc::new(RwLock::new(HashSet::new())),
        }
    }
    
    /// Run a sync operation by its ID
    pub async fn run_sync_operation(&self, operation_id: i32) -> Result<()> {
        // Get operation details
        let operation = crate::database::sync_operations::get_sync_operation_by_id(
            &self.database, 
            operation_id
        ).await?;
        
        // Get the associated sync pair
        let sync_pair = crate::database::sync_pairs::get_sync_pair_by_id(
            &self.database,
            operation.sync_pair_id
        ).await?;
        
        // Start operation
        crate::database::sync_operations::start_sync_operation(
            &self.database,
            operation_id
        ).await?;
        
        // Add to active operations
        {
            let mut active_ops = self.active_operations.write().await;
            active_ops.insert(operation_id);
        }
        
        // Track start time for metrics
        let start_time = Instant::now();
        
        // Record metrics
        let sync_duration_timer = self.telemetry.gis_export_duration.start_timer();
        
        // Use a Result to track success/failure
        let result: Result<(i32, i32, i32, Option<serde_json::Value>)> = async {
            // Check if sync pair is active
            if !sync_pair.is_active {
                return Err(Error::InvalidInput(
                    format!("Cannot run operation on inactive sync pair: {}", sync_pair.id)
                ));
            }
            
            // Extract sync configuration
            let source_system = &sync_pair.source_system;
            let target_system = &sync_pair.target_system;
            let source_config = &sync_pair.source_config;
            let target_config = &sync_pair.target_config;
            let field_mappings = &sync_pair.field_mappings;
            
            // Log the operation start
            log::info!(
                "Starting sync operation {} for pair {} ({} -> {})",
                operation_id,
                sync_pair.id,
                source_system,
                target_system
            );
            
            // Initialize counters
            let mut records_processed = 0;
            let mut records_succeeded = 0;
            let mut records_failed = 0;
            let mut execution_details = HashMap::new();
            
            // Connect to source and target systems
            // In a real implementation, we would use connectors based on source_system and target_system
            // For this demo, we'll simulate the process
            
            // 1. Extract data from source
            let source_data = self.extract_data_from_source(
                source_system,
                source_config
            ).await?;
            
            records_processed = source_data.len() as i32;
            execution_details.insert("source_record_count", source_data.len());
            
            // 2. Transform data based on field mappings
            let transformed_data = self.transform_data(
                source_data,
                field_mappings,
                &sync_pair
            ).await?;
            
            // Check for cancellation
            if self.is_operation_cancelled(operation_id).await {
                return Err(Error::SyncOperation("Operation was cancelled".to_string()));
            }
            
            // 3. Load data into target
            let load_result = self.load_data_to_target(
                transformed_data,
                target_system,
                target_config
            ).await?;
            
            records_succeeded = load_result.success_count;
            records_failed = load_result.error_count;
            
            execution_details.insert("target_success_count", load_result.success_count as usize);
            execution_details.insert("target_error_count", load_result.error_count as usize);
            
            if !load_result.errors.is_empty() {
                execution_details.insert("errors", load_result.errors);
            }
            
            Ok((
                records_processed,
                records_succeeded,
                records_failed,
                Some(serde_json::to_value(execution_details).unwrap_or(serde_json::Value::Null))
            ))
        }.await;
        
        // Stop the timer for metrics
        sync_duration_timer.observe_duration();
        
        // Remove from active operations
        {
            let mut active_ops = self.active_operations.write().await;
            active_ops.remove(&operation_id);
        }
        
        // Remove from cancellation requests if present
        {
            let mut cancellation_reqs = self.cancellation_requests.write().await;
            cancellation_reqs.remove(&operation_id);
        }
        
        // Update operation status based on result
        match result {
            Ok((records_processed, records_succeeded, records_failed, execution_details)) => {
                // Operation completed successfully
                crate::database::sync_operations::complete_sync_operation(
                    &self.database,
                    operation_id,
                    records_processed,
                    records_succeeded,
                    records_failed,
                    execution_details
                ).await?;
                
                log::info!(
                    "Completed sync operation {}: processed {}, succeeded {}, failed {}",
                    operation_id,
                    records_processed,
                    records_succeeded,
                    records_failed
                );
                
                Ok(())
            },
            Err(e) => {
                // Operation failed
                let is_cancelled = matches!(e, Error::SyncOperation(ref msg) if msg == "Operation was cancelled");
                
                let status = if is_cancelled { "cancelled" } else { "failed" };
                let error_message = format!("{}", e);
                
                if is_cancelled {
                    log::info!("Sync operation {} was cancelled", operation_id);
                } else {
                    log::error!("Sync operation {} failed: {}", operation_id, error_message);
                    self.telemetry.sync_operations_failed.inc();
                }
                
                crate::database::sync_operations::fail_sync_operation(
                    &self.database,
                    operation_id,
                    error_message,
                    None,
                    None,
                    None,
                    None
                ).await?;
                
                Err(e)
            }
        }
    }
    
    /// Request cancellation of an active sync operation
    pub async fn cancel_operation(&self, operation_id: i32) -> Result<()> {
        // Check if operation exists and is active
        let operation = crate::database::sync_operations::get_sync_operation_by_id(
            &self.database, 
            operation_id
        ).await?;
        
        if operation.status != "in_progress" {
            return Err(Error::InvalidInput(
                format!("Cannot cancel operation {} that is not in progress (current status: {})",
                    operation_id, operation.status)
            ));
        }
        
        // Add to cancellation requests
        {
            let mut cancellation_reqs = self.cancellation_requests.write().await;
            cancellation_reqs.insert(operation_id);
        }
        
        log::info!("Requested cancellation of sync operation {}", operation_id);
        
        Ok(())
    }
    
    /// Check if an operation has been requested to be cancelled
    async fn is_operation_cancelled(&self, operation_id: i32) -> bool {
        let cancellation_reqs = self.cancellation_requests.read().await;
        cancellation_reqs.contains(&operation_id)
    }
    
    /// Extract data from a source system based on the source configuration
    async fn extract_data_from_source(
        &self,
        source_system: &str,
        source_config: &serde_json::Value,
    ) -> Result<Vec<serde_json::Value>> {
        // In a real implementation, we would use a connector factory to get
        // a connector for the specific source system type
        
        // For this demo, we'll simulate extracting data
        match source_system {
            "file" => {
                // Simulate file data extraction
                Ok(vec![
                    serde_json::json!({
                        "id": "record1",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "age": 30,
                        "address": {
                            "city": "New York",
                            "state": "NY"
                        }
                    }),
                    serde_json::json!({
                        "id": "record2",
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "age": 28,
                        "address": {
                            "city": "Boston",
                            "state": "MA"
                        }
                    }),
                    serde_json::json!({
                        "id": "record3",
                        "name": "Bob Johnson",
                        "email": "bob@example.com",
                        "age": 35,
                        "address": {
                            "city": "Chicago",
                            "state": "IL"
                        }
                    }),
                ])
            },
            "database" => {
                // Simulate database extraction
                Ok(vec![
                    serde_json::json!({
                        "user_id": 1001,
                        "username": "john_doe",
                        "email_address": "john@example.com",
                        "user_age": 30,
                        "location": "New York, NY"
                    }),
                    serde_json::json!({
                        "user_id": 1002,
                        "username": "jane_smith",
                        "email_address": "jane@example.com",
                        "user_age": 28,
                        "location": "Boston, MA"
                    }),
                    serde_json::json!({
                        "user_id": 1003,
                        "username": "bob_johnson",
                        "email_address": "bob@example.com",
                        "user_age": 35,
                        "location": "Chicago, IL"
                    }),
                ])
            },
            "api" => {
                // Simulate API extraction
                Ok(vec![
                    serde_json::json!({
                        "userId": "U1001",
                        "displayName": "John Doe",
                        "contactInfo": {
                            "email": "john@example.com",
                            "phone": "555-1234"
                        },
                        "demographics": {
                            "age": 30,
                            "location": "New York"
                        }
                    }),
                    serde_json::json!({
                        "userId": "U1002",
                        "displayName": "Jane Smith",
                        "contactInfo": {
                            "email": "jane@example.com",
                            "phone": "555-5678"
                        },
                        "demographics": {
                            "age": 28,
                            "location": "Boston"
                        }
                    }),
                ])
            },
            _ => {
                Err(Error::InvalidInput(format!("Unsupported source system: {}", source_system)))
            }
        }
    }
    
    /// Transform data based on field mappings
    async fn transform_data(
        &self,
        source_data: Vec<serde_json::Value>,
        field_mappings: &serde_json::Value,
        sync_pair: &SyncPair,
    ) -> Result<Vec<serde_json::Value>> {
        // Validate field mappings
        let mappings = field_mappings.as_array()
            .ok_or_else(|| Error::InvalidInput("Field mappings must be an array".to_string()))?;
        
        // Transform each record
        let mut transformed_data = Vec::with_capacity(source_data.len());
        
        for record in source_data {
            let mut transformed_record = serde_json::Map::new();
            
            // Apply each field mapping
            for mapping in mappings {
                let mapping_obj = mapping.as_object()
                    .ok_or_else(|| Error::InvalidInput("Field mapping must be an object".to_string()))?;
                
                let source_field = mapping_obj.get("source_field")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| Error::InvalidInput("source_field is required in mapping".to_string()))?;
                
                let target_field = mapping_obj.get("target_field")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| Error::InvalidInput("target_field is required in mapping".to_string()))?;
                
                // Extract source value
                let source_value = self.get_nested_value(&record, source_field);
                
                // Apply transformation if specified
                let final_value = if let Some(transformation) = mapping_obj.get("transformation").and_then(|v| v.as_str()) {
                    self.apply_transformation(
                        source_value.clone(),
                        transformation,
                        mapping_obj.get("transformation_params")
                    )?
                } else {
                    source_value.clone()
                };
                
                // Set value in target record
                transformed_record.insert(target_field.to_string(), final_value);
            }
            
            transformed_data.push(serde_json::Value::Object(transformed_record));
        }
        
        Ok(transformed_data)
    }
    
    /// Get a nested value from a JSON object by a dot-notation path
    fn get_nested_value(&self, record: &serde_json::Value, path: &str) -> serde_json::Value {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = record;
        
        for part in parts {
            if let Some(obj) = current.as_object() {
                if let Some(value) = obj.get(part) {
                    current = value;
                } else {
                    return serde_json::Value::Null;
                }
            } else if let Some(arr) = current.as_array() {
                if let Ok(index) = part.parse::<usize>() {
                    if index < arr.len() {
                        current = &arr[index];
                    } else {
                        return serde_json::Value::Null;
                    }
                } else {
                    return serde_json::Value::Null;
                }
            } else {
                return serde_json::Value::Null;
            }
        }
        
        current.clone()
    }
    
    /// Apply a transformation to a value
    fn apply_transformation(
        &self,
        value: serde_json::Value,
        transformation: &str,
        transformation_params: Option<&serde_json::Value>,
    ) -> Result<serde_json::Value> {
        match transformation {
            "uppercase" => {
                if let Some(s) = value.as_str() {
                    Ok(serde_json::Value::String(s.to_uppercase()))
                } else {
                    Ok(value)
                }
            },
            "lowercase" => {
                if let Some(s) = value.as_str() {
                    Ok(serde_json::Value::String(s.to_lowercase()))
                } else {
                    Ok(value)
                }
            },
            "concat" => {
                let params = transformation_params
                    .ok_or_else(|| Error::InvalidInput("concat transformation requires parameters".to_string()))?;
                
                let append = params.get("append")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                
                if let Some(s) = value.as_str() {
                    Ok(serde_json::Value::String(format!("{}{}", s, append)))
                } else {
                    Ok(value)
                }
            },
            "split_address" => {
                // Example of a more complex transformation
                if let Some(s) = value.as_str() {
                    // Extract city and state from "City, State" format
                    let parts: Vec<&str> = s.split(',').collect();
                    if parts.len() == 2 {
                        let city = parts[0].trim();
                        let state = parts[1].trim();
                        Ok(serde_json::json!({
                            "city": city,
                            "state": state
                        }))
                    } else {
                        Ok(serde_json::json!({
                            "full_address": s
                        }))
                    }
                } else {
                    Ok(value)
                }
            },
            _ => {
                Err(Error::InvalidInput(format!("Unsupported transformation: {}", transformation)))
            }
        }
    }
    
    /// Load data into the target system
    async fn load_data_to_target(
        &self,
        data: Vec<serde_json::Value>,
        target_system: &str,
        target_config: &serde_json::Value,
    ) -> Result<LoadResult> {
        // In a real implementation, we would use a connector factory to get
        // a connector for the specific target system type
        
        // For this demo, we'll simulate loading data
        // Introduce a small delay to simulate work
        tokio::time::sleep(Duration::from_millis(500)).await;
        
        // Simulate some success and some failures
        let mut success_count = 0;
        let mut error_count = 0;
        let mut errors = Vec::new();
        
        for (i, record) in data.iter().enumerate() {
            // Simulate a 10% error rate
            if i % 10 == 9 {
                error_count += 1;
                errors.push(format!("Error loading record {}: Simulated error", i));
            } else {
                success_count += 1;
            }
        }
        
        Ok(LoadResult {
            success_count,
            error_count,
            errors,
        })
    }
}

/// Result from loading data into a target system
pub struct LoadResult {
    pub success_count: i32,
    pub error_count: i32,
    pub errors: Vec<String>,
}