use anyhow::{Result, Context};
use std::path::PathBuf;
use std::process::Command;
use tokio::time::{sleep, Duration};
use log::{info, warn, error};

/// Start all TerraFusion services
pub async fn start_all_services(install_dir: &PathBuf) -> Result<()> {
    info!("Starting TerraFusion Platform services...");
    
    // Start PostgreSQL database service
    start_database_service(install_dir).await?;
    
    // Wait for database to be ready
    sleep(Duration::from_secs(5)).await;
    
    // Start the main TerraFusion Windows service
    start_terrafusion_service().await?;
    
    // Verify all services are running
    verify_services_running().await?;
    
    info!("All services started successfully");
    Ok(())
}

/// Stop all TerraFusion services
pub async fn stop_all_services() -> Result<()> {
    info!("Stopping TerraFusion Platform services...");
    
    // Stop TerraFusion service
    stop_terrafusion_service().await?;
    
    // Stop database service
    stop_database_service().await?;
    
    info!("All services stopped successfully");
    Ok(())
}

/// Start the PostgreSQL database service
async fn start_database_service(install_dir: &PathBuf) -> Result<()> {
    info!("Starting PostgreSQL database service...");
    
    let db_dir = install_dir.join("database");
    let data_dir = db_dir.join("data");
    let postgres_exe = db_dir.join("bin").join("postgres.exe");
    
    // Check if PostgreSQL is already running
    if is_postgres_running().await {
        info!("PostgreSQL is already running");
        return Ok(());
    }
    
    // Start PostgreSQL as a background process
    let _child = tokio::process::Command::new(postgres_exe)
        .args(&[
            "-D", &data_dir.to_string_lossy(),
            "-k", &db_dir.to_string_lossy(),
        ])
        .spawn()
        .context("Failed to start PostgreSQL service")?;
    
    // Wait for PostgreSQL to be ready
    let mut attempts = 0;
    while attempts < 30 {
        if is_postgres_running().await {
            info!("PostgreSQL service started successfully");
            return Ok(());
        }
        sleep(Duration::from_secs(1)).await;
        attempts += 1;
    }
    
    anyhow::bail!("PostgreSQL failed to start within 30 seconds");
}

/// Stop the PostgreSQL database service
async fn stop_database_service() -> Result<()> {
    info!("Stopping PostgreSQL database service...");
    
    // Find and terminate PostgreSQL processes
    let output = Command::new("taskkill")
        .args(&["/F", "/IM", "postgres.exe"])
        .output()
        .context("Failed to stop PostgreSQL service")?;
    
    if output.status.success() {
        info!("PostgreSQL service stopped successfully");
    } else {
        warn!("PostgreSQL service may not have been running");
    }
    
    Ok(())
}

/// Start the main TerraFusion Windows service
async fn start_terrafusion_service() -> Result<()> {
    info!("Starting TerraFusion Platform service...");
    
    let output = Command::new("sc")
        .args(&["start", "TerraFusionPlatform"])
        .output()
        .context("Failed to start TerraFusion service")?;
    
    if output.status.success() {
        info!("TerraFusion Platform service started successfully");
        
        // Wait for service to initialize
        sleep(Duration::from_secs(10)).await;
        
        // Verify service is running
        if is_terrafusion_service_running().await {
            info!("TerraFusion Platform service is running and ready");
        } else {
            anyhow::bail!("TerraFusion Platform service failed to start properly");
        }
    } else {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Failed to start TerraFusion service: {}", error_msg);
    }
    
    Ok(())
}

/// Stop the main TerraFusion Windows service
async fn stop_terrafusion_service() -> Result<()> {
    info!("Stopping TerraFusion Platform service...");
    
    let output = Command::new("sc")
        .args(&["stop", "TerraFusionPlatform"])
        .output()
        .context("Failed to stop TerraFusion service")?;
    
    if output.status.success() {
        info!("TerraFusion Platform service stopped successfully");
    } else {
        warn!("TerraFusion Platform service may not have been running");
    }
    
    Ok(())
}

/// Check if PostgreSQL is running
async fn is_postgres_running() -> bool {
    let output = Command::new("tasklist")
        .args(&["/FI", "IMAGENAME eq postgres.exe"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            output_str.contains("postgres.exe")
        }
        Err(_) => false,
    }
}

/// Check if TerraFusion service is running
async fn is_terrafusion_service_running() -> bool {
    let output = Command::new("sc")
        .args(&["query", "TerraFusionPlatform"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            output_str.contains("RUNNING")
        }
        Err(_) => false,
    }
}

/// Verify all services are running and healthy
async fn verify_services_running() -> Result<()> {
    info!("Verifying service health...");
    
    // Check PostgreSQL
    if !is_postgres_running().await {
        anyhow::bail!("PostgreSQL service is not running");
    }
    
    // Check TerraFusion service
    if !is_terrafusion_service_running().await {
        anyhow::bail!("TerraFusion Platform service is not running");
    }
    
    // Test database connectivity
    test_database_connectivity().await?;
    
    // Test web interface availability
    test_web_interface().await?;
    
    info!("All services are running and healthy");
    Ok(())
}

/// Test database connectivity
async fn test_database_connectivity() -> Result<()> {
    info!("Testing database connectivity...");
    
    // Simple database connection test
    let output = Command::new("psql")
        .args(&[
            "-h", "localhost",
            "-p", "5433",
            "-U", "terrafusion",
            "-d", "terrafusion",
            "-c", "SELECT 1;"
        ])
        .env("PGPASSWORD", "terrafusion")
        .output();
    
    match output {
        Ok(output) if output.status.success() => {
            info!("Database connectivity test passed");
            Ok(())
        }
        Ok(output) => {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Database connectivity test failed: {}", error_msg);
        }
        Err(e) => {
            anyhow::bail!("Failed to test database connectivity: {}", e);
        }
    }
}

/// Test web interface availability
async fn test_web_interface() -> Result<()> {
    info!("Testing web interface availability...");
    
    let client = reqwest::Client::new();
    let mut attempts = 0;
    
    while attempts < 30 {
        match client.get("http://localhost:8000/system/health").send().await {
            Ok(response) if response.status().is_success() => {
                info!("Web interface is available and responding");
                return Ok(());
            }
            Ok(_) => {
                warn!("Web interface returned non-success status, retrying...");
            }
            Err(_) => {
                // Service may still be starting up
            }
        }
        
        sleep(Duration::from_secs(2)).await;
        attempts += 1;
    }
    
    anyhow::bail!("Web interface failed to become available within 60 seconds");
}

/// Get service status information
pub async fn get_service_status() -> Result<ServiceStatus> {
    let postgres_running = is_postgres_running().await;
    let terrafusion_running = is_terrafusion_service_running().await;
    
    let web_accessible = match reqwest::get("http://localhost:8000/system/health").await {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    };
    
    Ok(ServiceStatus {
        postgres_running,
        terrafusion_running,
        web_accessible,
        overall_healthy: postgres_running && terrafusion_running && web_accessible,
    })
}

/// Service status structure
#[derive(Debug)]
pub struct ServiceStatus {
    pub postgres_running: bool,
    pub terrafusion_running: bool,
    pub web_accessible: bool,
    pub overall_healthy: bool,
}