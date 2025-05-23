use crate::errors::{Error, Result, DatabaseError};
use sqlx::{PgPool, Postgres, Transaction};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use std::time::Duration;
use log::{info, warn, error};

/// Migration status
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MigrationStatus {
    Pending,
    Running,
    Completed,
    Failed,
}

impl std::fmt::Display for MigrationStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MigrationStatus::Pending => write!(f, "pending"),
            MigrationStatus::Running => write!(f, "running"),
            MigrationStatus::Completed => write!(f, "completed"),
            MigrationStatus::Failed => write!(f, "failed"),
        }
    }
}

/// Migration record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Migration {
    pub version: String,
    pub name: String,
    pub status: MigrationStatus,
    pub applied_at: Option<DateTime<Utc>>,
    pub duration_ms: Option<i64>,
    pub error: Option<String>,
}

/// Migration handler
#[derive(Debug)]
pub struct Migrator {
    pool: PgPool,
    migrations: HashMap<String, Box<dyn MigrationFn>>,
}

/// Migration function trait
pub trait MigrationFn: Send + Sync + 'static {
    fn up(&self, tx: &mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>>;
    fn down(&self, tx: &mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>>;
}

impl Migrator {
    /// Create a new migrator
    pub fn new(pool: PgPool) -> Self {
        Self {
            pool,
            migrations: HashMap::new(),
        }
    }
    
    /// Register a migration
    pub fn register_migration(
        &mut self,
        version: &str,
        name: &str,
        up_fn: impl Fn(&mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> + Send + Sync + 'static,
        down_fn: impl Fn(&mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> + Send + Sync + 'static,
    ) {
        let key = format!("{}_{}", version, name);
        
        struct MigrationImpl<U, D> {
            up_fn: U,
            down_fn: D,
        }
        
        impl<U, D> MigrationFn for MigrationImpl<U, D>
        where
            U: Fn(&mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> + Send + Sync + 'static,
            D: Fn(&mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> + Send + Sync + 'static,
        {
            fn up(&self, tx: &mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> {
                (self.up_fn)(tx)
            }
            
            fn down(&self, tx: &mut Transaction<'_, Postgres>) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + Send + '_>> {
                (self.down_fn)(tx)
            }
        }
        
        self.migrations.insert(
            key,
            Box::new(MigrationImpl { up_fn, down_fn }),
        );
    }
    
    /// Initialize the migrations table
    pub async fn init(&self) -> Result<()> {
        // Create the migrations table if it doesn't exist
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS migrations (
                version VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                applied_at TIMESTAMPTZ,
                duration_ms BIGINT,
                error TEXT,
                PRIMARY KEY (version, name)
            )
            "#,
        )
        .execute(&self.pool)
        .await
        .map_err(|e| Error::Database(DatabaseError::Migration(format!("Failed to create migrations table: {}", e))))?;
        
        Ok(())
    }
    
    /// Get all migrations with their status
    pub async fn get_migrations(&self) -> Result<Vec<Migration>> {
        // Get all migrations from the database
        let db_migrations = sqlx::query_as!(
            DbMigration,
            r#"
            SELECT 
                version, 
                name, 
                status, 
                applied_at, 
                duration_ms, 
                error
            FROM migrations
            ORDER BY version ASC, name ASC
            "#,
        )
        .fetch_all(&self.pool)
        .await
        .map_err(|e| Error::Database(DatabaseError::Migration(format!("Failed to fetch migrations: {}", e))))?;
        
        // Convert database migrations to our model
        let mut migrations = Vec::new();
        for m in db_migrations {
            migrations.push(Migration {
                version: m.version,
                name: m.name,
                status: match m.status.as_str() {
                    "pending" => MigrationStatus::Pending,
                    "running" => MigrationStatus::Running,
                    "completed" => MigrationStatus::Completed,
                    "failed" => MigrationStatus::Failed,
                    _ => MigrationStatus::Pending,
                },
                applied_at: m.applied_at,
                duration_ms: m.duration_ms,
                error: m.error,
            });
        }
        
        // Add any migrations not in the database
        for (key, _) in &self.migrations {
            let parts: Vec<&str> = key.splitn(2, '_').collect();
            if parts.len() == 2 {
                let version = parts[0].to_string();
                let name = parts[1].to_string();
                
                if !migrations.iter().any(|m| m.version == version && m.name == name) {
                    migrations.push(Migration {
                        version,
                        name,
                        status: MigrationStatus::Pending,
                        applied_at: None,
                        duration_ms: None,
                        error: None,
                    });
                }
            }
        }
        
        // Sort migrations by version and name
        migrations.sort_by(|a, b| {
            if a.version != b.version {
                a.version.cmp(&b.version)
            } else {
                a.name.cmp(&b.name)
            }
        });
        
        Ok(migrations)
    }
    
    /// Run pending migrations
    pub async fn run_pending_migrations(&self) -> Result<Vec<Migration>> {
        // Initialize migrations table
        self.init().await?;
        
        // Get all migrations
        let migrations = self.get_migrations().await?;
        
        // Find pending migrations
        let pending_migrations: Vec<Migration> = migrations
            .into_iter()
            .filter(|m| m.status == MigrationStatus::Pending)
            .collect();
        
        if pending_migrations.is_empty() {
            info!("No pending migrations to run");
            return Ok(Vec::new());
        }
        
        info!("Running {} pending migrations", pending_migrations.len());
        
        let mut results = Vec::new();
        
        // Run each pending migration
        for migration in pending_migrations {
            let key = format!("{}_{}", migration.version, migration.name);
            
            // Check if we have a registered migration with this key
            if let Some(migration_fn) = self.migrations.get(&key) {
                info!("Running migration {}: {}", migration.version, migration.name);
                
                // Mark migration as running
                self.update_migration_status(
                    &migration.version,
                    &migration.name,
                    MigrationStatus::Running,
                    None,
                    None,
                ).await?;
                
                // Start timing the migration
                let start_time = std::time::Instant::now();
                
                // Run the migration
                let result = self.run_migration(&migration.version, &migration.name, |tx| migration_fn.up(tx)).await;
                
                // Calculate duration
                let duration = start_time.elapsed();
                let duration_ms = duration.as_millis() as i64;
                
                match result {
                    Ok(_) => {
                        // Mark migration as completed
                        self.update_migration_status(
                            &migration.version,
                            &migration.name,
                            MigrationStatus::Completed,
                            Some(duration_ms),
                            None,
                        ).await?;
                        
                        info!("Migration {}_{} completed in {}ms", migration.version, migration.name, duration_ms);
                        
                        results.push(Migration {
                            version: migration.version,
                            name: migration.name,
                            status: MigrationStatus::Completed,
                            applied_at: Some(Utc::now()),
                            duration_ms: Some(duration_ms),
                            error: None,
                        });
                    }
                    Err(e) => {
                        // Mark migration as failed
                        let error_msg = e.to_string();
                        self.update_migration_status(
                            &migration.version,
                            &migration.name,
                            MigrationStatus::Failed,
                            Some(duration_ms),
                            Some(&error_msg),
                        ).await?;
                        
                        error!("Migration {}_{} failed in {}ms: {}", migration.version, migration.name, duration_ms, error_msg);
                        
                        results.push(Migration {
                            version: migration.version,
                            name: migration.name,
                            status: MigrationStatus::Failed,
                            applied_at: Some(Utc::now()),
                            duration_ms: Some(duration_ms),
                            error: Some(error_msg),
                        });
                        
                        return Err(Error::Database(DatabaseError::Migration(format!(
                            "Migration {}_{} failed: {}",
                            migration.version, migration.name, e
                        ))));
                    }
                }
            } else {
                warn!("No migration function found for {}_{}", migration.version, migration.name);
            }
        }
        
        Ok(results)
    }
    
    /// Run a specific migration in a transaction
    async fn run_migration<F, Fut>(&self, version: &str, name: &str, f: F) -> Result<()>
    where
        F: FnOnce(&mut Transaction<'_, Postgres>) -> Fut,
        Fut: std::future::Future<Output = Result<()>> + Send,
    {
        let mut tx = self.pool
            .begin()
            .await
            .map_err(|e| Error::Database(DatabaseError::Transaction(e.to_string())))?;
        
        match f(&mut tx).await {
            Ok(_) => {
                tx.commit()
                    .await
                    .map_err(|e| Error::Database(DatabaseError::Transaction(e.to_string())))?;
                Ok(())
            }
            Err(e) => {
                let _ = tx.rollback().await;
                Err(e)
            }
        }
    }
    
    /// Update migration status in the database
    async fn update_migration_status(
        &self,
        version: &str,
        name: &str,
        status: MigrationStatus,
        duration_ms: Option<i64>,
        error: Option<&str>,
    ) -> Result<()> {
        let status_str = status.to_string();
        let now = Utc::now();
        
        sqlx::query(
            r#"
            INSERT INTO migrations (version, name, status, applied_at, duration_ms, error)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (version, name) DO UPDATE SET
                status = $3,
                applied_at = $4,
                duration_ms = $5,
                error = $6
            "#,
        )
        .bind(version)
        .bind(name)
        .bind(status_str)
        .bind(now)
        .bind(duration_ms)
        .bind(error)
        .execute(&self.pool)
        .await
        .map_err(|e| Error::Database(DatabaseError::Migration(format!("Failed to update migration status: {}", e))))?;
        
        Ok(())
    }
}

/// Database migration record
#[derive(Debug)]
struct DbMigration {
    version: String,
    name: String,
    status: String,
    applied_at: Option<DateTime<Utc>>,
    duration_ms: Option<i64>,
    error: Option<String>,
}