use std::collections::HashMap;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use terrafusion_common::{Result, Error};
use terrafusion_common::models::sync::*;

/// Conflict resolution service for handling data conflicts during sync
pub struct ConflictResolver {
    resolution_strategies: HashMap<SyncConflictStrategy, Box<dyn ConflictResolutionStrategy>>,
}

/// Trait for conflict resolution strategies
pub trait ConflictResolutionStrategy: Send + Sync {
    fn resolve_conflict(
        &self,
        source_data: &serde_json::Value,
        target_data: &serde_json::Value,
        context: &ConflictContext,
    ) -> Result<ConflictResolution>;
}

/// Context information for conflict resolution
#[derive(Debug, Clone)]
pub struct ConflictContext {
    pub sync_pair_id: Uuid,
    pub operation_id: Uuid,
    pub field_path: String,
    pub source_timestamp: Option<DateTime<Utc>>,
    pub target_timestamp: Option<DateTime<Utc>>,
    pub user_preferences: Option<serde_json::Value>,
}

/// Result of conflict resolution
#[derive(Debug, Clone)]
pub struct ConflictResolution {
    pub resolution_type: SyncConflictResolution,
    pub resolved_value: Option<serde_json::Value>,
    pub reason: String,
    pub requires_manual_review: bool,
}

impl ConflictResolver {
    /// Create a new conflict resolver with default strategies
    pub fn new() -> Self {
        let mut resolver = Self {
            resolution_strategies: HashMap::new(),
        };
        
        // Register default resolution strategies
        resolver.register_strategy(SyncConflictStrategy::SourceWins, Box::new(SourceWinsStrategy));
        resolver.register_strategy(SyncConflictStrategy::TargetWins, Box::new(TargetWinsStrategy));
        resolver.register_strategy(SyncConflictStrategy::NewerWins, Box::new(NewerWinsStrategy));
        resolver.register_strategy(SyncConflictStrategy::Manual, Box::new(ManualResolutionStrategy));
        
        resolver
    }
    
    /// Register a custom conflict resolution strategy
    pub fn register_strategy(
        &mut self,
        strategy_type: SyncConflictStrategy,
        strategy: Box<dyn ConflictResolutionStrategy>,
    ) {
        self.resolution_strategies.insert(strategy_type, strategy);
    }
    
    /// Resolve a conflict using the specified strategy
    pub fn resolve_conflict(
        &self,
        strategy: SyncConflictStrategy,
        source_data: &serde_json::Value,
        target_data: &serde_json::Value,
        context: &ConflictContext,
    ) -> Result<ConflictResolution> {
        let resolver = self.resolution_strategies.get(&strategy)
            .ok_or_else(|| Error::Internal(format!("No resolver found for strategy: {:?}", strategy)))?;
        
        resolver.resolve_conflict(source_data, target_data, context)
    }
    
    /// Detect conflicts between source and target data
    pub fn detect_conflicts(
        &self,
        source_data: &serde_json::Value,
        target_data: &serde_json::Value,
    ) -> Vec<FieldConflict> {
        let mut conflicts = Vec::new();
        
        // Compare JSON objects recursively
        if let (Some(source_obj), Some(target_obj)) = (source_data.as_object(), target_data.as_object()) {
            for (key, source_value) in source_obj {
                if let Some(target_value) = target_obj.get(key) {
                    if source_value != target_value {
                        conflicts.push(FieldConflict {
                            field_path: key.clone(),
                            source_value: source_value.clone(),
                            target_value: target_value.clone(),
                            conflict_type: self.classify_conflict_type(source_value, target_value),
                        });
                    }
                } else {
                    // Field exists in source but not in target
                    conflicts.push(FieldConflict {
                        field_path: key.clone(),
                        source_value: source_value.clone(),
                        target_value: serde_json::Value::Null,
                        conflict_type: ConflictType::MissingField,
                    });
                }
            }
            
            // Check for fields that exist in target but not in source
            for (key, target_value) in target_obj {
                if !source_obj.contains_key(key) {
                    conflicts.push(FieldConflict {
                        field_path: key.clone(),
                        source_value: serde_json::Value::Null,
                        target_value: target_value.clone(),
                        conflict_type: ConflictType::ExtraField,
                    });
                }
            }
        }
        
        conflicts
    }
    
    /// Classify the type of conflict
    fn classify_conflict_type(
        &self,
        source_value: &serde_json::Value,
        target_value: &serde_json::Value,
    ) -> ConflictType {
        match (source_value, target_value) {
            (serde_json::Value::String(_), serde_json::Value::String(_)) => ConflictType::ValueDifference,
            (serde_json::Value::Number(_), serde_json::Value::Number(_)) => ConflictType::ValueDifference,
            (serde_json::Value::Bool(_), serde_json::Value::Bool(_)) => ConflictType::ValueDifference,
            (serde_json::Value::Null, _) => ConflictType::MissingField,
            (_, serde_json::Value::Null) => ConflictType::ExtraField,
            _ => ConflictType::TypeMismatch,
        }
    }
}

/// Represents a field-level conflict
#[derive(Debug, Clone)]
pub struct FieldConflict {
    pub field_path: String,
    pub source_value: serde_json::Value,
    pub target_value: serde_json::Value,
    pub conflict_type: ConflictType,
}

/// Type of conflict detected
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConflictType {
    ValueDifference,
    TypeMismatch,
    MissingField,
    ExtraField,
}

// Implementation of built-in resolution strategies

/// Strategy that always chooses the source value
struct SourceWinsStrategy;

impl ConflictResolutionStrategy for SourceWinsStrategy {
    fn resolve_conflict(
        &self,
        source_data: &serde_json::Value,
        _target_data: &serde_json::Value,
        _context: &ConflictContext,
    ) -> Result<ConflictResolution> {
        Ok(ConflictResolution {
            resolution_type: SyncConflictResolution::UseSource,
            resolved_value: Some(source_data.clone()),
            reason: "Source wins strategy applied".to_string(),
            requires_manual_review: false,
        })
    }
}

/// Strategy that always chooses the target value
struct TargetWinsStrategy;

impl ConflictResolutionStrategy for TargetWinsStrategy {
    fn resolve_conflict(
        &self,
        _source_data: &serde_json::Value,
        target_data: &serde_json::Value,
        _context: &ConflictContext,
    ) -> Result<ConflictResolution> {
        Ok(ConflictResolution {
            resolution_type: SyncConflictResolution::UseTarget,
            resolved_value: Some(target_data.clone()),
            reason: "Target wins strategy applied".to_string(),
            requires_manual_review: false,
        })
    }
}

/// Strategy that chooses the newer value based on timestamps
struct NewerWinsStrategy;

impl ConflictResolutionStrategy for NewerWinsStrategy {
    fn resolve_conflict(
        &self,
        source_data: &serde_json::Value,
        target_data: &serde_json::Value,
        context: &ConflictContext,
    ) -> Result<ConflictResolution> {
        match (context.source_timestamp, context.target_timestamp) {
            (Some(source_ts), Some(target_ts)) => {
                if source_ts > target_ts {
                    Ok(ConflictResolution {
                        resolution_type: SyncConflictResolution::UseSource,
                        resolved_value: Some(source_data.clone()),
                        reason: format!("Source is newer ({} > {})", source_ts, target_ts),
                        requires_manual_review: false,
                    })
                } else {
                    Ok(ConflictResolution {
                        resolution_type: SyncConflictResolution::UseTarget,
                        resolved_value: Some(target_data.clone()),
                        reason: format!("Target is newer ({} >= {})", target_ts, source_ts),
                        requires_manual_review: false,
                    })
                }
            }
            (Some(_), None) => {
                Ok(ConflictResolution {
                    resolution_type: SyncConflictResolution::UseSource,
                    resolved_value: Some(source_data.clone()),
                    reason: "Source has timestamp, target does not".to_string(),
                    requires_manual_review: false,
                })
            }
            (None, Some(_)) => {
                Ok(ConflictResolution {
                    resolution_type: SyncConflictResolution::UseTarget,
                    resolved_value: Some(target_data.clone()),
                    reason: "Target has timestamp, source does not".to_string(),
                    requires_manual_review: false,
                })
            }
            (None, None) => {
                // No timestamps available, fall back to source wins
                Ok(ConflictResolution {
                    resolution_type: SyncConflictResolution::UseSource,
                    resolved_value: Some(source_data.clone()),
                    reason: "No timestamps available, defaulting to source".to_string(),
                    requires_manual_review: true,
                })
            }
        }
    }
}

/// Strategy that requires manual resolution
struct ManualResolutionStrategy;

impl ConflictResolutionStrategy for ManualResolutionStrategy {
    fn resolve_conflict(
        &self,
        _source_data: &serde_json::Value,
        _target_data: &serde_json::Value,
        _context: &ConflictContext,
    ) -> Result<ConflictResolution> {
        Ok(ConflictResolution {
            resolution_type: SyncConflictResolution::Skip,
            resolved_value: None,
            reason: "Manual resolution required".to_string(),
            requires_manual_review: true,
        })
    }
}