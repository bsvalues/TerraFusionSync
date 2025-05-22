use chrono::{DateTime, Utc};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable)]
#[diesel(table_name = crate::schema::audit_entries)]
pub struct AuditEntry {
    pub id: Uuid,
    pub event_type: String,
    pub resource_type: String,
    pub description: String,
    pub resource_id: Option<String>,
    pub operation_id: Option<i32>,
    pub previous_state: Option<serde_json::Value>,
    pub new_state: Option<serde_json::Value>,
    pub severity: String,
    pub user_id: Option<String>,
    pub username: Option<String>,
    pub ip_address: Option<String>,
    pub correlation_id: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewAuditEntry {
    pub event_type: String,
    pub resource_type: String,
    pub description: String,
    pub resource_id: Option<String>,
    pub operation_id: Option<i32>,
    pub previous_state: Option<serde_json::Value>,
    pub new_state: Option<serde_json::Value>,
    pub severity: String,
    pub user_id: Option<String>,
    pub username: Option<String>,
    pub ip_address: Option<String>,
    pub correlation_id: Option<String>,
}

impl NewAuditEntry {
    pub fn to_audit_entry(self) -> AuditEntry {
        AuditEntry {
            id: Uuid::new_v4(),
            event_type: self.event_type,
            resource_type: self.resource_type,
            description: self.description,
            resource_id: self.resource_id,
            operation_id: self.operation_id,
            previous_state: self.previous_state,
            new_state: self.new_state,
            severity: self.severity,
            user_id: self.user_id,
            username: self.username,
            ip_address: self.ip_address,
            correlation_id: self.correlation_id,
            created_at: Utc::now(),
        }
    }
}