use diesel::prelude::*;
use diesel::r2d2::{self, ConnectionManager, Pool, PoolError, PooledConnection};
use diesel::pg::PgConnection;
use std::time::Duration;

use crate::error::{Error, Result};

// Database wrapper for managing connections
#[derive(Clone)]
pub struct Database {
    pool: Pool<ConnectionManager<PgConnection>>,
}

impl Database {
    pub fn new(
        username: &str,
        password: &str,
        host: &str,
        port: u16,
        database_name: &str,
        max_connections: u32,
    ) -> Result<Self> {
        let database_url = format!(
            "postgres://{}:{}@{}:{}/{}",
            username, password, host, port, database_name
        );
        
        let manager = ConnectionManager::<PgConnection>::new(database_url);
        
        let pool = r2d2::Pool::builder()
            .max_size(max_connections)
            .connection_timeout(Duration::from_secs(30))
            .build(manager)
            .map_err(|e| Error::DatabaseError(format!("Failed to create connection pool: {}", e)))?;
        
        Ok(Self { pool })
    }
    
    pub fn get_connection(&self) -> Result<PooledConnection<ConnectionManager<PgConnection>>> {
        self.pool
            .get()
            .map_err(|e| Error::DatabaseError(format!("Failed to get database connection: {}", e)))
    }
    
    // Execute a query within a transaction
    pub fn transaction<F, T>(&self, f: F) -> Result<T>
    where
        F: FnOnce(&PgConnection) -> Result<T>,
    {
        let conn = self.get_connection()?;
        
        conn.transaction(|c| {
            f(c).map_err(|e| {
                diesel::result::Error::RollbackTransaction
            })
        })
        .map_err(|e| {
            if let diesel::result::Error::RollbackTransaction = e {
                // Transaction was explicitly rolled back, the original error will be propagated
                return Error::DatabaseError("Transaction rolled back".to_string());
            }
            
            Error::DatabaseError(format!("Transaction error: {}", e))
        })
    }
    
    // Test database connection
    pub fn test_connection(&self) -> Result<()> {
        let conn = self.get_connection()?;
        
        diesel::sql_query("SELECT 1")
            .execute(&conn)
            .map_err(|e| Error::DatabaseError(format!("Connection test failed: {}", e)))?;
        
        Ok(())
    }
}