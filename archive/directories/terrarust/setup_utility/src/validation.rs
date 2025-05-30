use anyhow::{Result, Context};
use std::path::PathBuf;
use std::process::Command;
use tokio::fs;
use log::{info, warn, error};

/// Validate system requirements for TerraFusion Platform
pub async fn validate_system_requirements(install_dir: &PathBuf) -> Result<()> {
    info!("Validating system requirements...");
    
    // Check operating system
    validate_operating_system().await?;
    
    // Check available disk space
    validate_disk_space(install_dir).await?;
    
    // Check available memory
    validate_memory().await?;
    
    // Check network connectivity
    validate_network_connectivity().await?;
    
    // Check required ports availability
    validate_port_availability().await?;
    
    // Check administrator privileges
    validate_administrator_privileges().await?;
    
    // Check Windows services permissions
    validate_service_permissions().await?;
    
    info!("All system requirements validated successfully");
    Ok(())
}

/// Validate the installation after setup is complete
pub async fn validate_installation(install_dir: &PathBuf, web_port: u16) -> Result<()> {
    info!("Validating TerraFusion Platform installation...");
    
    // Check if all required files are present
    validate_installation_files(install_dir).await?;
    
    // Check if configuration files are valid
    validate_configuration_files(install_dir).await?;
    
    // Check if database is accessible
    validate_database_connection().await?;
    
    // Check if services are running
    validate_services_running().await?;
    
    // Check if web interface is accessible
    validate_web_interface(web_port).await?;
    
    // Run basic functionality tests
    validate_basic_functionality(web_port).await?;
    
    info!("Installation validation completed successfully");
    Ok(())
}

/// Validate operating system compatibility
async fn validate_operating_system() -> Result<()> {
    info!("Checking operating system compatibility...");
    
    // Check if running on Windows
    if !cfg!(target_os = "windows") {
        anyhow::bail!("TerraFusion Platform requires Windows Server 2016+ or Windows 10+");
    }
    
    // Get Windows version information
    let output = Command::new("cmd")
        .args(&["/c", "ver"])
        .output()
        .context("Failed to get Windows version")?;
    
    if output.status.success() {
        let version_info = String::from_utf8_lossy(&output.stdout);
        info!("Operating system: {}", version_info.trim());
        
        // Basic version check (could be enhanced with more specific checks)
        if version_info.contains("Windows") {
            info!("✅ Operating system compatibility confirmed");
        } else {
            warn!("⚠️ Could not verify Windows version, proceeding with installation");
        }
    } else {
        warn!("⚠️ Could not determine operating system version");
    }
    
    Ok(())
}

/// Validate available disk space
async fn validate_disk_space(install_dir: &PathBuf) -> Result<()> {
    info!("Checking available disk space...");
    
    // Get the drive letter from install directory
    let drive = install_dir
        .to_string_lossy()
        .chars()
        .take(2)
        .collect::<String>();
    
    let output = Command::new("dir")
        .args(&[&drive, "/-c"])
        .output()
        .context("Failed to check disk space")?;
    
    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        
        // Parse free space (simplified parsing)
        if let Some(line) = output_str.lines().last() {
            if line.contains("bytes free") {
                info!("✅ Disk space information: {}", line.trim());
                
                // Extract free space in bytes (simplified extraction)
                if let Some(free_space_str) = line.split_whitespace().nth(2) {
                    if let Ok(free_space) = free_space_str.replace(",", "").parse::<u64>() {
                        let free_space_gb = free_space / (1024 * 1024 * 1024);
                        
                        if free_space_gb < 10 {
                            anyhow::bail!("Insufficient disk space. Required: 10GB, Available: {}GB", free_space_gb);
                        }
                        
                        info!("✅ Sufficient disk space available: {}GB", free_space_gb);
                    }
                }
            }
        }
    } else {
        warn!("⚠️ Could not check disk space, proceeding with installation");
    }
    
    Ok(())
}

/// Validate available memory
async fn validate_memory() -> Result<()> {
    info!("Checking available memory...");
    
    let output = Command::new("wmic")
        .args(&["computersystem", "get", "TotalPhysicalMemory", "/value"])
        .output()
        .context("Failed to check memory")?;
    
    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        
        for line in output_str.lines() {
            if line.starts_with("TotalPhysicalMemory=") {
                if let Some(memory_str) = line.split('=').nth(1) {
                    if let Ok(memory_bytes) = memory_str.trim().parse::<u64>() {
                        let memory_gb = memory_bytes / (1024 * 1024 * 1024);
                        
                        if memory_gb < 4 {
                            anyhow::bail!("Insufficient memory. Required: 4GB, Available: {}GB", memory_gb);
                        }
                        
                        info!("✅ Sufficient memory available: {}GB", memory_gb);
                        return Ok(());
                    }
                }
            }
        }
    }
    
    warn!("⚠️ Could not verify memory requirements, proceeding with installation");
    Ok(())
}

/// Validate network connectivity
async fn validate_network_connectivity() -> Result<()> {
    info!("Checking network connectivity...");
    
    // Test basic network connectivity
    let result = Command::new("ping")
        .args(&["-n", "2", "8.8.8.8"])
        .output()
        .context("Failed to test network connectivity")?;
    
    if result.status.success() {
        info!("✅ Network connectivity confirmed");
    } else {
        warn!("⚠️ Limited network connectivity detected, some features may not work");
    }
    
    Ok(())
}

/// Validate port availability
async fn validate_port_availability() -> Result<()> {
    info!("Checking port availability...");
    
    let required_ports = vec![8000, 8001, 8002, 5433];
    
    for port in required_ports {
        if is_port_in_use(port).await {
            anyhow::bail!("Port {} is already in use. Please free this port before installation.", port);
        } else {
            info!("✅ Port {} is available", port);
        }
    }
    
    Ok(())
}

/// Check if a port is in use
async fn is_port_in_use(port: u16) -> bool {
    let output = Command::new("netstat")
        .args(&["-an"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            let port_pattern = format!(":{}", port);
            output_str.lines().any(|line| {
                line.contains(&port_pattern) && 
                (line.contains("LISTENING") || line.contains("ESTABLISHED"))
            })
        }
        Err(_) => false,
    }
}

/// Validate administrator privileges
async fn validate_administrator_privileges() -> Result<()> {
    info!("Checking administrator privileges...");
    
    // Try to create a test file in a restricted location
    let test_path = PathBuf::from("C:\\Windows\\Temp\\terrafusion_admin_test.txt");
    
    match fs::write(&test_path, "test").await {
        Ok(_) => {
            // Clean up test file
            let _ = fs::remove_file(&test_path).await;
            info!("✅ Administrator privileges confirmed");
            Ok(())
        }
        Err(_) => {
            anyhow::bail!("Administrator privileges required. Please run the installer as Administrator.");
        }
    }
}

/// Validate Windows service permissions
async fn validate_service_permissions() -> Result<()> {
    info!("Checking Windows service permissions...");
    
    // Test if we can query services (requires appropriate permissions)
    let output = Command::new("sc")
        .args(&["query", "type=", "service", "state=", "all"])
        .output()
        .context("Failed to query Windows services")?;
    
    if output.status.success() {
        info!("✅ Windows service permissions confirmed");
    } else {
        anyhow::bail!("Insufficient permissions to manage Windows services");
    }
    
    Ok(())
}

/// Validate installation files are present
async fn validate_installation_files(install_dir: &PathBuf) -> Result<()> {
    info!("Checking installation files...");
    
    let required_files = vec![
        "bin/terrafusion-api-gateway.exe",
        "bin/terrafusion-sync-service.exe", 
        "bin/terrafusion-gis-export.exe",
        "bin/terrafusion-setup.exe",
        "bin/terrafusion-console.exe",
        "config/app.toml",
        "config/logging.toml",
    ];
    
    for file_path in required_files {
        let full_path = install_dir.join(file_path);
        if !full_path.exists() {
            anyhow::bail!("Required file missing: {}", file_path);
        }
    }
    
    info!("✅ All required installation files are present");
    Ok(())
}

/// Validate configuration files
async fn validate_configuration_files(install_dir: &PathBuf) -> Result<()> {
    info!("Validating configuration files...");
    
    let config_dir = install_dir.join("config");
    
    // Check main application config
    let app_config_path = config_dir.join("app.toml");
    if app_config_path.exists() {
        let config_content = fs::read_to_string(&app_config_path).await
            .context("Failed to read app configuration")?;
        
        // Basic TOML syntax validation
        if let Err(e) = toml::from_str::<toml::Value>(&config_content) {
            anyhow::bail!("Invalid app configuration: {}", e);
        }
    } else {
        anyhow::bail!("Missing app configuration file");
    }
    
    // Check environment file
    let env_path = config_dir.join(".env");
    if !env_path.exists() {
        anyhow::bail!("Missing environment configuration file");
    }
    
    info!("✅ Configuration files are valid");
    Ok(())
}

/// Validate database connection
async fn validate_database_connection() -> Result<()> {
    info!("Testing database connection...");
    
    // Simple connection test using psql
    let output = Command::new("psql")
        .args(&[
            "-h", "localhost",
            "-p", "5433", 
            "-U", "terrafusion",
            "-d", "terrafusion",
            "-c", "SELECT version();"
        ])
        .env("PGPASSWORD", "terrafusion")
        .output();
    
    match output {
        Ok(output) if output.status.success() => {
            info!("✅ Database connection successful");
            Ok(())
        }
        Ok(output) => {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Database connection failed: {}", error_msg);
        }
        Err(e) => {
            anyhow::bail!("Failed to test database connection: {}", e);
        }
    }
}

/// Validate services are running
async fn validate_services_running() -> Result<()> {
    info!("Checking service status...");
    
    // Check if TerraFusion service is running
    let output = Command::new("sc")
        .args(&["query", "TerraFusionPlatform"])
        .output()
        .context("Failed to query service status")?;
    
    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        if output_str.contains("RUNNING") {
            info!("✅ TerraFusion Platform service is running");
        } else {
            anyhow::bail!("TerraFusion Platform service is not running");
        }
    } else {
        anyhow::bail!("Failed to query TerraFusion Platform service status");
    }
    
    Ok(())
}

/// Validate web interface accessibility
async fn validate_web_interface(port: u16) -> Result<()> {
    info!("Testing web interface accessibility...");
    
    let client = reqwest::Client::new();
    let url = format!("http://localhost:{}/system/health", port);
    
    match client.get(&url).send().await {
        Ok(response) if response.status().is_success() => {
            info!("✅ Web interface is accessible at http://localhost:{}", port);
            Ok(())
        }
        Ok(response) => {
            anyhow::bail!("Web interface returned status: {}", response.status());
        }
        Err(e) => {
            anyhow::bail!("Failed to access web interface: {}", e);
        }
    }
}

/// Validate basic functionality
async fn validate_basic_functionality(port: u16) -> Result<()> {
    info!("Testing basic functionality...");
    
    let client = reqwest::Client::new();
    
    // Test API endpoints
    let endpoints = vec![
        format!("http://localhost:{}/api/system/status", port),
        format!("http://localhost:{}/api/sync/pairs", port),
        format!("http://localhost:{}/api/gis/health", port),
    ];
    
    for endpoint in endpoints {
        match client.get(&endpoint).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    info!("✅ Endpoint {} is responding", endpoint);
                } else {
                    warn!("⚠️ Endpoint {} returned status: {}", endpoint, response.status());
                }
            }
            Err(e) => {
                warn!("⚠️ Failed to test endpoint {}: {}", endpoint, e);
            }
        }
    }
    
    info!("✅ Basic functionality validation completed");
    Ok(())
}

/// Get detailed system information for troubleshooting
pub async fn get_system_info() -> Result<SystemInfo> {
    let os_info = get_os_info().await;
    let memory_info = get_memory_info().await;
    let disk_info = get_disk_info().await;
    let network_info = get_network_info().await;
    
    Ok(SystemInfo {
        os_info,
        memory_info,
        disk_info,
        network_info,
    })
}

async fn get_os_info() -> String {
    let output = Command::new("cmd")
        .args(&["/c", "ver"])
        .output();
    
    match output {
        Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_string(),
        Err(_) => "Unknown".to_string(),
    }
}

async fn get_memory_info() -> String {
    let output = Command::new("wmic")
        .args(&["computersystem", "get", "TotalPhysicalMemory", "/value"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            for line in output_str.lines() {
                if line.starts_with("TotalPhysicalMemory=") {
                    if let Some(memory_str) = line.split('=').nth(1) {
                        if let Ok(memory_bytes) = memory_str.trim().parse::<u64>() {
                            let memory_gb = memory_bytes / (1024 * 1024 * 1024);
                            return format!("{}GB", memory_gb);
                        }
                    }
                }
            }
            "Unknown".to_string()
        }
        Err(_) => "Unknown".to_string(),
    }
}

async fn get_disk_info() -> String {
    let output = Command::new("dir")
        .args(&["C:\\", "/-c"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            if let Some(line) = output_str.lines().last() {
                if line.contains("bytes free") {
                    return line.trim().to_string();
                }
            }
            "Unknown".to_string()
        }
        Err(_) => "Unknown".to_string(),
    }
}

async fn get_network_info() -> String {
    let output = Command::new("ipconfig")
        .args(&["/all"])
        .output();
    
    match output {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            // Extract relevant network information (simplified)
            if output_str.contains("IPv4 Address") {
                "Network available".to_string()
            } else {
                "No network configuration found".to_string()
            }
        }
        Err(_) => "Unknown".to_string(),
    }
}

/// System information structure
#[derive(Debug)]
pub struct SystemInfo {
    pub os_info: String,
    pub memory_info: String,
    pub disk_info: String,
    pub network_info: String,
}