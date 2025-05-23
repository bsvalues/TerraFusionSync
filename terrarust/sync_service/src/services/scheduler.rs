use std::sync::Arc;
use std::time::Duration;
use tokio::time::{interval, sleep};
use tokio::sync::RwLock;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use terrafusion_common::{Result, Error, database::DbPool};
use terrafusion_common::models::sync::*;
use super::sync_engine::SyncEngine;

/// Scheduler for automatic sync operations
#[derive(Clone)]
pub struct Scheduler {
    db_pool: DbPool,
    sync_engine: SyncEngine,
    is_running: Arc<RwLock<bool>>,
    interval_duration: Duration,
}

/// Handle for the scheduler task
pub struct SchedulerHandle {
    shutdown_sender: tokio::sync::oneshot::Sender<()>,
}

impl SchedulerHandle {
    /// Shutdown the scheduler gracefully
    pub async fn shutdown(self) {
        let _ = self.shutdown_sender.send(());
    }
}

impl Scheduler {
    /// Create a new scheduler
    pub fn new(db_pool: DbPool, sync_engine: SyncEngine, interval_seconds: u64) -> Self {
        Self {
            db_pool,
            sync_engine,
            is_running: Arc::new(RwLock::new(false)),
            interval_duration: Duration::from_secs(interval_seconds),
        }
    }
    
    /// Start the scheduler
    pub async fn start(&self) -> Result<SchedulerHandle> {
        {
            let mut running = self.is_running.write().await;
            if *running {
                return Err(Error::Internal("Scheduler is already running".to_string()));
            }
            *running = true;
        }
        
        let (shutdown_sender, mut shutdown_receiver) = tokio::sync::oneshot::channel();
        
        let scheduler = self.clone();
        tokio::spawn(async move {
            let mut interval_timer = interval(scheduler.interval_duration);
            
            log::info!("Scheduler started with interval {:?}", scheduler.interval_duration);
            
            loop {
                tokio::select! {
                    _ = interval_timer.tick() => {
                        if let Err(e) = scheduler.run_scheduled_syncs().await {
                            log::error!("Error running scheduled syncs: {}", e);
                        }
                        
                        if let Err(e) = scheduler.cleanup_old_operations().await {
                            log::error!("Error cleaning up old operations: {}", e);
                        }
                    }
                    _ = &mut shutdown_receiver => {
                        log::info!("Scheduler shutdown requested");
                        break;
                    }
                }
            }
            
            // Mark as not running
            {
                let mut running = scheduler.is_running.write().await;
                *running = false;
            }
            
            log::info!("Scheduler stopped");
        });
        
        Ok(SchedulerHandle { shutdown_sender })
    }
    
    /// Run scheduled sync operations
    async fn run_scheduled_syncs(&self) -> Result<()> {
        log::debug!("Checking for scheduled sync operations");
        
        // Get all active sync pairs that are due for sync
        let due_sync_pairs = self.get_due_sync_pairs().await?;
        
        if due_sync_pairs.is_empty() {
            log::debug!("No sync pairs due for execution");
            return Ok(());
        }
        
        log::info!("Found {} sync pairs due for execution", due_sync_pairs.len());
        
        for sync_pair in due_sync_pairs {
            // Check if there's already a running sync for this pair
            if self.is_sync_pair_running(sync_pair.base.id).await? {
                log::debug!("Sync pair {} is already running, skipping", sync_pair.name);
                continue;
            }
            
            // Start sync operation
            match self.sync_engine.start_sync_operation(
                sync_pair.base.id,
                "scheduler".to_string(),
                None,
            ).await {
                Ok(operation_id) => {
                    log::info!(
                        "Started scheduled sync operation {} for pair {}",
                        operation_id,
                        sync_pair.name
                    );
                    
                    // Update last sync time
                    self.update_sync_pair_last_sync(sync_pair.base.id).await?;
                }
                Err(e) => {
                    log::error!(
                        "Failed to start scheduled sync for pair {}: {}",
                        sync_pair.name,
                        e
                    );
                }
            }
        }
        
        Ok(())
    }
    
    /// Clean up old sync operations and records
    async fn cleanup_old_operations(&self) -> Result<()> {
        log::debug!("Running cleanup of old sync operations");
        
        // Define retention periods
        let operation_retention_days = 30;
        let record_retention_days = 7;
        
        // Calculate cutoff dates
        let operation_cutoff = Utc::now() - chrono::Duration::days(operation_retention_days);
        let record_cutoff = Utc::now() - chrono::Duration::days(record_retention_days);
        
        // Clean up old operations
        let operations_deleted = self.delete_old_operations(operation_cutoff).await?;
        if operations_deleted > 0 {
            log::info!("Cleaned up {} old sync operations", operations_deleted);
        }
        
        // Clean up old sync records
        let records_deleted = self.delete_old_sync_records(record_cutoff).await?;
        if records_deleted > 0 {
            log::info!("Cleaned up {} old sync records", records_deleted);
        }
        
        Ok(())
    }
    
    /// Check if the scheduler is running
    pub async fn is_running(&self) -> bool {
        *self.is_running.read().await
    }
    
    // Database helper methods
    async fn get_due_sync_pairs(&self) -> Result<Vec<SyncPair>> {
        // This would query the database for sync pairs that are due for execution
        // based on their sync_interval_minutes and last_sync_time
        
        // For now, return empty list
        // In a real implementation, this would be something like:
        /*
        sqlx::query_as!(
            SyncPair,
            r#"
            SELECT * FROM sync_pairs 
            WHERE is_active = true 
            AND (
                last_sync_time IS NULL 
                OR last_sync_time + INTERVAL sync_interval_minutes MINUTE <= NOW()
            )
            "#
        )
        .fetch_all(&self.db_pool)
        .await
        .map_err(|e| Error::Database(e.into()))
        */
        
        Ok(Vec::new())
    }
    
    async fn is_sync_pair_running(&self, sync_pair_id: Uuid) -> Result<bool> {
        // This would check if there's a running sync operation for the given sync pair
        // For now, return false
        Ok(false)
    }
    
    async fn update_sync_pair_last_sync(&self, sync_pair_id: Uuid) -> Result<()> {
        // This would update the last_sync_time for the sync pair
        // For now, do nothing
        Ok(())
    }
    
    async fn delete_old_operations(&self, cutoff_date: DateTime<Utc>) -> Result<i64> {
        // This would delete old sync operations and their related records
        // For now, return 0
        Ok(0)
    }
    
    async fn delete_old_sync_records(&self, cutoff_date: DateTime<Utc>) -> Result<i64> {
        // This would delete old sync records
        // For now, return 0
        Ok(0)
    }
}

/// Start the scheduler service
pub async fn start_scheduler(
    sync_engine: SyncEngine,
    db_pool: DbPool,
) -> Result<SchedulerHandle> {
    let interval_seconds = std::env::var("SCHEDULER_INTERVAL_SECONDS")
        .unwrap_or_else(|_| "60".to_string())
        .parse::<u64>()
        .unwrap_or(60);
    
    let scheduler = Scheduler::new(db_pool, sync_engine, interval_seconds);
    scheduler.start().await
}