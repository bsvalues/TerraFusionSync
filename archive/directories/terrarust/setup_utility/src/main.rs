use clap::{Parser, Subcommand};
use anyhow::{Result, Context};
use std::path::PathBuf;
use log::{info, warn, error};

mod database;
mod services;
mod firewall;
mod config;
mod validation;

#[derive(Parser)]
#[command(name = "terrafusion-setup")]
#[command(about = "TerraFusion Platform Setup Utility")]
#[command(version = "1.0.0")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
    
    /// Enable verbose logging
    #[arg(short, long)]
    verbose: bool,
    
    /// Installation directory
    #[arg(long, default_value = "C:\\Program Files\\TerraFusion Platform")]
    install_dir: PathBuf,
}

#[derive(Subcommand)]
enum Commands {
    /// Create and initialize the database
    CreateDatabase {
        /// County identifier
        #[arg(long)]
        county: String,
        
        /// Database password (generated if not provided)
        #[arg(long)]
        password: Option<String>,
    },
    
    /// Start all TerraFusion services
    StartServices,
    
    /// Stop all TerraFusion services  
    StopServices,
    
    /// Configure Windows firewall rules
    ConfigureFirewall {
        /// Web interface port
        #[arg(long, default_value = "8000")]
        port: u16,
    },
    
    /// Validate system requirements
    ValidateSystem,
    
    /// Generate configuration files
    GenerateConfig {
        /// County identifier
        #[arg(long)]
        county: String,
        
        /// Administrator email
        #[arg(long)]
        admin_email: String,
    },
    
    /// Complete installation setup
    Setup {
        /// County identifier
        #[arg(long)]
        county: String,
        
        /// Administrator email
        #[arg(long)]
        admin_email: String,
        
        /// Web interface port
        #[arg(long, default_value = "8000")]
        port: u16,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    
    // Initialize logging
    let log_level = if cli.verbose { "debug" } else { "info" };
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level)).init();
    
    info!("TerraFusion Platform Setup Utility v1.0.0");
    info!("Installation directory: {}", cli.install_dir.display());
    
    match cli.command {
        Commands::CreateDatabase { county, password } => {
            info!("Creating database for county: {}", county);
            database::create_database(&cli.install_dir, &county, password.as_deref()).await?;
            info!("Database created successfully");
        },
        
        Commands::StartServices => {
            info!("Starting TerraFusion services...");
            services::start_all_services(&cli.install_dir).await?;
            info!("All services started successfully");
        },
        
        Commands::StopServices => {
            info!("Stopping TerraFusion services...");
            services::stop_all_services().await?;
            info!("All services stopped successfully");
        },
        
        Commands::ConfigureFirewall { port } => {
            info!("Configuring Windows firewall for port range {}-{}", port, port + 2);
            firewall::configure_firewall_rules(port).await?;
            info!("Firewall configured successfully");
        },
        
        Commands::ValidateSystem => {
            info!("Validating system requirements...");
            validation::validate_system_requirements(&cli.install_dir).await?;
            info!("System validation completed successfully");
        },
        
        Commands::GenerateConfig { county, admin_email } => {
            info!("Generating configuration for county: {}", county);
            config::generate_configuration(&cli.install_dir, &county, &admin_email).await?;
            info!("Configuration generated successfully");
        },
        
        Commands::Setup { county, admin_email, port } => {
            info!("Running complete setup for county: {}", county);
            run_complete_setup(&cli.install_dir, &county, &admin_email, port).await?;
            info!("Setup completed successfully");
        },
    }
    
    Ok(())
}

/// Run complete setup process
async fn run_complete_setup(
    install_dir: &PathBuf,
    county: &str,
    admin_email: &str,
    port: u16,
) -> Result<()> {
    // Step 1: Validate system requirements
    info!("Step 1/6: Validating system requirements...");
    validation::validate_system_requirements(install_dir).await
        .context("System validation failed")?;
    
    // Step 2: Generate configuration
    info!("Step 2/6: Generating configuration...");
    config::generate_configuration(install_dir, county, admin_email).await
        .context("Configuration generation failed")?;
    
    // Step 3: Create database
    info!("Step 3/6: Setting up database...");
    database::create_database(install_dir, county, None).await
        .context("Database setup failed")?;
    
    // Step 4: Configure firewall
    info!("Step 4/6: Configuring firewall...");
    firewall::configure_firewall_rules(port).await
        .context("Firewall configuration failed")?;
    
    // Step 5: Start services
    info!("Step 5/6: Starting services...");
    services::start_all_services(install_dir).await
        .context("Service startup failed")?;
    
    // Step 6: Validate installation
    info!("Step 6/6: Validating installation...");
    validation::validate_installation(install_dir, port).await
        .context("Installation validation failed")?;
    
    // Display success message with access information
    println!("\n🎉 TerraFusion Platform setup completed successfully!");
    println!("🌐 Web Interface: http://localhost:{}", port);
    println!("📧 Administrator: {}", admin_email);
    println!("🏛️ County: {}", county);
    println!("\nThe platform is now ready for use!");
    
    Ok(())
}