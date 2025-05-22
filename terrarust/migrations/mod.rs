use diesel::{Connection, PgConnection};
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use std::env;
use std::error::Error;

// Embed migrations
pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!("migrations");

/// Run migrations on the database
pub fn run_migrations() -> Result<(), Box<dyn Error>> {
    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    
    let mut conn = PgConnection::establish(&database_url)?;
    
    // Run migrations
    conn.run_pending_migrations(MIGRATIONS)?;
    
    Ok(())
}

/// Revert the last migration
pub fn revert_last_migration() -> Result<(), Box<dyn Error>> {
    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    
    let mut conn = PgConnection::establish(&database_url)?;
    
    // Revert the last migration
    conn.revert_last_migration(MIGRATIONS)?;
    
    Ok(())
}