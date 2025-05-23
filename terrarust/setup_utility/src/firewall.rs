use anyhow::{Result, Context};
use std::process::Command;
use log::{info, warn};

/// Configure Windows firewall rules for TerraFusion Platform
pub async fn configure_firewall_rules(web_port: u16) -> Result<()> {
    info!("Configuring Windows firewall rules...");
    
    // Define port ranges
    let api_gateway_port = web_port;
    let sync_service_port = web_port + 1;
    let gis_export_port = web_port + 2;
    let database_port = 5433;
    
    // Remove any existing TerraFusion firewall rules
    remove_existing_rules().await?;
    
    // Add inbound rules for TerraFusion services
    add_firewall_rule(
        "TerraFusion-API-Gateway-In",
        api_gateway_port,
        "Inbound rule for TerraFusion API Gateway web interface"
    ).await?;
    
    add_firewall_rule(
        "TerraFusion-Sync-Service-In", 
        sync_service_port,
        "Inbound rule for TerraFusion Sync Service API"
    ).await?;
    
    add_firewall_rule(
        "TerraFusion-GIS-Export-In",
        gis_export_port,
        "Inbound rule for TerraFusion GIS Export Service API"
    ).await?;
    
    // Add database rule (localhost only)
    add_database_firewall_rule(
        "TerraFusion-Database-In",
        database_port,
        "Inbound rule for TerraFusion PostgreSQL database (localhost only)"
    ).await?;
    
    // Add outbound rules for external API access
    add_outbound_rule(
        "TerraFusion-HTTP-Out",
        80,
        "Outbound rule for TerraFusion HTTP access"
    ).await?;
    
    add_outbound_rule(
        "TerraFusion-HTTPS-Out",
        443,
        "Outbound rule for TerraFusion HTTPS access"
    ).await?;
    
    info!("Windows firewall configured successfully");
    Ok(())
}

/// Add a firewall rule for inbound traffic
async fn add_firewall_rule(name: &str, port: u16, description: &str) -> Result<()> {
    info!("Adding firewall rule: {} (port {})", name, port);
    
    let output = Command::new("netsh")
        .args(&[
            "advfirewall", "firewall", "add", "rule",
            &format!("name={}", name),
            "dir=in",
            "action=allow",
            "protocol=TCP",
            &format!("localport={}", port),
            "profile=domain,private",
            &format!("description={}", description)
        ])
        .output()
        .context("Failed to execute netsh command")?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Failed to add firewall rule {}: {}", name, error_msg);
    }
    
    Ok(())
}

/// Add a database-specific firewall rule (localhost only)
async fn add_database_firewall_rule(name: &str, port: u16, description: &str) -> Result<()> {
    info!("Adding database firewall rule: {} (port {})", name, port);
    
    let output = Command::new("netsh")
        .args(&[
            "advfirewall", "firewall", "add", "rule",
            &format!("name={}", name),
            "dir=in",
            "action=allow",
            "protocol=TCP",
            &format!("localport={}", port),
            "remoteip=127.0.0.1,::1",
            "profile=domain,private,public",
            &format!("description={}", description)
        ])
        .output()
        .context("Failed to execute netsh command")?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Failed to add database firewall rule {}: {}", name, error_msg);
    }
    
    Ok(())
}

/// Add an outbound firewall rule
async fn add_outbound_rule(name: &str, port: u16, description: &str) -> Result<()> {
    info!("Adding outbound firewall rule: {} (port {})", name, port);
    
    let output = Command::new("netsh")
        .args(&[
            "advfirewall", "firewall", "add", "rule",
            &format!("name={}", name),
            "dir=out",
            "action=allow",
            "protocol=TCP",
            &format!("remoteport={}", port),
            "profile=domain,private",
            &format!("description={}", description)
        ])
        .output()
        .context("Failed to execute netsh command")?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        warn!("Failed to add outbound firewall rule {}: {}", name, error_msg);
        // Don't fail on outbound rules as they're less critical
    }
    
    Ok(())
}

/// Remove existing TerraFusion firewall rules
async fn remove_existing_rules() -> Result<()> {
    info!("Removing any existing TerraFusion firewall rules...");
    
    let rule_names = vec![
        "TerraFusion-API-Gateway-In",
        "TerraFusion-Sync-Service-In", 
        "TerraFusion-GIS-Export-In",
        "TerraFusion-Database-In",
        "TerraFusion-HTTP-Out",
        "TerraFusion-HTTPS-Out"
    ];
    
    for rule_name in rule_names {
        let output = Command::new("netsh")
            .args(&[
                "advfirewall", "firewall", "delete", "rule",
                &format!("name={}", rule_name)
            ])
            .output()
            .context("Failed to execute netsh command")?;
        
        if output.status.success() {
            info!("Removed existing firewall rule: {}", rule_name);
        }
        // Don't fail if rule doesn't exist
    }
    
    Ok(())
}

/// Check if Windows firewall is enabled
pub async fn is_firewall_enabled() -> Result<bool> {
    let output = Command::new("netsh")
        .args(&["advfirewall", "show", "allprofiles", "state"])
        .output()
        .context("Failed to check firewall status")?;
    
    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        Ok(output_str.contains("State                                 ON"))
    } else {
        Ok(false)
    }
}

/// Test if firewall rules are working correctly
pub async fn test_firewall_rules(web_port: u16) -> Result<()> {
    info!("Testing firewall rules...");
    
    // Test if we can bind to the configured ports
    let test_ports = vec![web_port, web_port + 1, web_port + 2];
    
    for port in test_ports {
        if let Err(e) = test_port_binding(port).await {
            warn!("Port {} may not be accessible: {}", port, e);
        } else {
            info!("Port {} is accessible", port);
        }
    }
    
    Ok(())
}

/// Test if a port can be bound to
async fn test_port_binding(port: u16) -> Result<()> {
    use std::net::{TcpListener, SocketAddr};
    
    let addr: SocketAddr = format!("127.0.0.1:{}", port).parse()
        .context("Invalid socket address")?;
    
    let listener = TcpListener::bind(addr)
        .context("Failed to bind to port")?;
    
    // Immediately drop the listener to free the port
    drop(listener);
    
    Ok(())
}

/// Get current firewall status and rules
pub async fn get_firewall_status() -> Result<FirewallStatus> {
    let enabled = is_firewall_enabled().await?;
    let rules = get_terrafusion_rules().await?;
    
    Ok(FirewallStatus {
        enabled,
        rules_configured: !rules.is_empty(),
        rule_count: rules.len(),
        rules,
    })
}

/// Get existing TerraFusion firewall rules
async fn get_terrafusion_rules() -> Result<Vec<String>> {
    let output = Command::new("netsh")
        .args(&[
            "advfirewall", "firewall", "show", "rule", 
            "name=all", "dir=in"
        ])
        .output()
        .context("Failed to query firewall rules")?;
    
    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        let rules: Vec<String> = output_str
            .lines()
            .filter(|line| line.contains("TerraFusion"))
            .map(|line| line.trim().to_string())
            .collect();
        
        Ok(rules)
    } else {
        Ok(Vec::new())
    }
}

/// Firewall status information
#[derive(Debug)]
pub struct FirewallStatus {
    pub enabled: bool,
    pub rules_configured: bool,
    pub rule_count: usize,
    pub rules: Vec<String>,
}