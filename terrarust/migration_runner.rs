use clap::{Parser, Subcommand};
use diesel::prelude::*;
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use dotenv::dotenv;
use std::env;
use std::error::Error;

// Embed migrations
const MIGRATIONS: EmbeddedMigrations = embed_migrations!("./migrations");

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run pending migrations
    Up,
    /// Revert the last migration
    Down,
    /// Show migration status
    Status,
}

fn main() -> Result<(), Box<dyn Error>> {
    // Load environment variables from .env file
    dotenv().ok();

    // Parse command line arguments
    let cli = Cli::parse();

    // Get database URL from environment
    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");

    // Establish connection to the database
    let mut conn = PgConnection::establish(&database_url)?;

    // Execute the appropriate command
    match cli.command {
        Commands::Up => {
            println!("Running pending migrations...");
            conn.run_pending_migrations(MIGRATIONS)?;
            println!("Migrations completed successfully.");
        }
        Commands::Down => {
            println!("Reverting the last migration...");
            conn.revert_last_migration(MIGRATIONS)?;
            println!("Last migration reverted successfully.");
        }
        Commands::Status => {
            // This would be a custom implementation to display migration status
            // For now, just show a message
            println!("Migration status feature not implemented yet.");
        }
    }

    Ok(())
}