use crate::config::DatabaseSettings;
use diesel::pg::PgConnection;
use diesel::r2d2::{ConnectionManager, Pool, PoolError, PooledConnection};
use std::sync::Arc;

pub type DbPool = Pool<ConnectionManager<PgConnection>>;
pub type DbPooledConnection = PooledConnection<ConnectionManager<PgConnection>>;

#[derive(Clone)]
pub struct Database {
    pool: Arc<DbPool>,
}

impl Database {
    pub fn new(config: &DatabaseSettings) -> Result<Self, PoolError> {
        let manager = ConnectionManager::<PgConnection>::new(config.connection_string());
        let pool = Pool::builder()
            .max_size(config.max_connections)
            .build(manager)?;
        
        Ok(Self {
            pool: Arc::new(pool),
        })
    }
    
    pub fn get_connection(&self) -> Result<DbPooledConnection, PoolError> {
        self.pool.get()
    }
}