use clap::{App, Arg, SubCommand};
use std::process;

mod migrations;

fn main() {
    // Parse command line arguments
    let matches = App::new("TerraFusion Database Migrator")
        .version("0.1.0")
        .author("TerraFusion Team")
        .about("Manages database migrations for the TerraFusion platform")
        .subcommand(
            SubCommand::with_name("up")
                .about("Run pending migrations")
        )
        .subcommand(
            SubCommand::with_name("down")
                .about("Revert the last migration")
        )
        .get_matches();

    // Execute the appropriate command
    if let Some(_) = matches.subcommand_matches("up") {
        println!("Running migrations...");
        
        if let Err(e) = migrations::run_migrations() {
            eprintln!("Error running migrations: {}", e);
            process::exit(1);
        }
        
        println!("Migrations completed successfully");
    } else if let Some(_) = matches.subcommand_matches("down") {
        println!("Reverting last migration...");
        
        if let Err(e) = migrations::revert_last_migration() {
            eprintln!("Error reverting migration: {}", e);
            process::exit(1);
        }
        
        println!("Migration reverted successfully");
    } else {
        eprintln!("No command specified. Use --help for available commands");
        process::exit(1);
    }
}