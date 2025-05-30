use chrono::{DateTime, Utc};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Identifiable)]
#[diesel(table_name = crate::schema::sync_pairs)]
pub struct SyncPair {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub target_system: String,
    pub source_config: serde_json::Value,
    pub target_config: serde_json::Value,
    pub field_mappings: serde_json::Value,
    pub transformations: Option<serde_json::Value>,
    pub filters: Option<serde_json::Value>,
    pub schedule: Option<serde_json::Value>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: Option<String>,
    pub county_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Insertable)]
#[diesel(table_name = crate::schema::sync_pairs)]
pub struct NewSyncPair {
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub target_system: String,
    pub source_config: serde_json::Value,
    pub target_config: serde_json::Value,
    pub field_mappings: serde_json::Value,
    pub transformations: Option<serde_json::Value>,
    pub filters: Option<serde_json::Value>,
    pub schedule: Option<serde_json::Value>,
    pub is_active: bool,
    pub created_by: Option<String>,
    pub county_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncPairUpdate {
    pub name: Option<String>,
    pub description: Option<String>,
    pub source_config: Option<serde_json::Value>,
    pub target_config: Option<serde_json::Value>,
    pub field_mappings: Option<serde_json::Value>,
    pub transformations: Option<serde_json::Value>,
    pub filters: Option<serde_json::Value>,
    pub schedule: Option<serde_json::Value>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldMapping {
    pub source_field: String,
    pub target_field: String,
    pub data_type: Option<String>,
    pub is_required: Option<bool>,
    pub default_value: Option<serde_json::Value>,
    pub transformation: Option<String>,
    pub transformation_params: Option<HashMap<String, serde_json::Value>>,
    pub validation_rules: Option<Vec<ValidationRule>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationRule {
    pub rule_type: String,
    pub params: Option<serde_json::Value>,
    pub error_message: Option<String>,
    pub severity: Option<String>,
}