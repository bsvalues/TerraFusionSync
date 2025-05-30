use anyhow::{Result, Context};
use std::path::PathBuf;
use std::process::Command;
use tokio::fs;
use log::{info, warn};
use uuid::Uuid;

/// Create and initialize the PostgreSQL database for TerraFusion
pub async fn create_database(
    install_dir: &PathBuf,
    county_id: &str,
    password: Option<&str>,
) -> Result<()> {
    let db_dir = install_dir.join("database");
    let data_dir = db_dir.join("data");
    
    // Generate database password if not provided
    let db_password = password.unwrap_or_else(|| {
        // Generate secure random password
        &Uuid::new_v4().to_string().replace("-", "")[..16]
    });
    
    info!("Setting up PostgreSQL database...");
    
    // Ensure database directory exists
    fs::create_dir_all(&data_dir).await
        .context("Failed to create database directory")?;
    
    // Initialize PostgreSQL data directory if it doesn't exist
    if !data_dir.join("postgresql.conf").exists() {
        info!("Initializing PostgreSQL data directory...");
        let initdb_result = Command::new(db_dir.join("bin").join("initdb.exe"))
            .args(&[
                "-D", &data_dir.to_string_lossy(),
                "-U", "postgres",
                "--pwfile", "-",
                "--encoding=UTF8",
                "--locale=C",
                "--auth-local=trust",
                "--auth-host=md5"
            ])
            .arg(format!("--pwfile={}", create_password_file(&db_dir, db_password).await?))
            .output()
            .context("Failed to run initdb")?;
        
        if !initdb_result.status.success() {
            anyhow::bail!(
                "Database initialization failed: {}",
                String::from_utf8_lossy(&initdb_result.stderr)
            );
        }
        
        info!("PostgreSQL data directory initialized");
    }
    
    // Configure PostgreSQL
    configure_postgresql(&data_dir).await?;
    
    // Start PostgreSQL temporarily for setup
    let postgres_handle = start_postgres_temporarily(&db_dir, &data_dir).await?;
    
    // Wait a moment for PostgreSQL to start
    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
    
    // Create TerraFusion database and user
    create_terrafusion_database(&db_dir, county_id, db_password).await?;
    
    // Run database migrations
    run_database_migrations(&db_dir, county_id).await?;
    
    // Stop temporary PostgreSQL instance
    stop_postgres_process(postgres_handle).await?;
    
    // Save database configuration
    save_database_config(install_dir, county_id, db_password).await?;
    
    info!("Database setup completed successfully");
    Ok(())
}

/// Create password file for initdb
async fn create_password_file(db_dir: &PathBuf, password: &str) -> Result<String> {
    let password_file = db_dir.join("temp_password.txt");
    fs::write(&password_file, password).await
        .context("Failed to create password file")?;
    Ok(password_file.to_string_lossy().to_string())
}

/// Configure PostgreSQL settings
async fn configure_postgresql(data_dir: &PathBuf) -> Result<()> {
    let config_file = data_dir.join("postgresql.conf");
    
    // Read existing configuration
    let mut config = if config_file.exists() {
        fs::read_to_string(&config_file).await
            .context("Failed to read PostgreSQL configuration")?
    } else {
        String::new()
    };
    
    // Append TerraFusion-specific settings
    config.push_str(&format!(
        "\n# TerraFusion Platform Configuration\n\
        port = 5433\n\
        listen_addresses = 'localhost'\n\
        max_connections = 100\n\
        shared_buffers = 128MB\n\
        effective_cache_size = 512MB\n\
        maintenance_work_mem = 64MB\n\
        checkpoint_completion_target = 0.9\n\
        wal_buffers = 16MB\n\
        default_statistics_target = 100\n\
        random_page_cost = 1.1\n\
        effective_io_concurrency = 200\n\
        work_mem = 4MB\n\
        min_wal_size = 1GB\n\
        max_wal_size = 4GB\n\
        log_destination = 'stderr'\n\
        logging_collector = on\n\
        log_directory = 'log'\n\
        log_filename = 'postgresql-%%Y-%%m-%%d_%%H%%M%%S.log'\n\
        log_rotation_age = 1d\n\
        log_rotation_size = 10MB\n\
        log_min_messages = warning\n\
        log_line_prefix = '%%t [%%p]: [%%l-1] user=%%u,db=%%d,app=%%a,client=%%h '\n"
    ));
    
    fs::write(&config_file, config).await
        .context("Failed to write PostgreSQL configuration")?;
    
    info!("PostgreSQL configuration updated");
    Ok(())
}

/// Start PostgreSQL temporarily for initial setup
async fn start_postgres_temporarily(
    db_dir: &PathBuf,
    data_dir: &PathBuf,
) -> Result<tokio::process::Child> {
    info!("Starting PostgreSQL for initial setup...");
    
    let postgres_exe = db_dir.join("bin").join("postgres.exe");
    let child = tokio::process::Command::new(postgres_exe)
        .args(&[
            "-D", &data_dir.to_string_lossy(),
            "-k", &db_dir.to_string_lossy(),
        ])
        .spawn()
        .context("Failed to start PostgreSQL")?;
    
    Ok(child)
}

/// Create TerraFusion database and user
async fn create_terrafusion_database(
    db_dir: &PathBuf,
    county_id: &str,
    password: &str,
) -> Result<()> {
    info!("Creating TerraFusion database and user...");
    
    let psql_exe = db_dir.join("bin").join("psql.exe");
    
    // Create database
    let create_db_sql = format!(
        "CREATE DATABASE terrafusion_{};\n\
         CREATE USER terrafusion WITH PASSWORD '{}';\n\
         GRANT ALL PRIVILEGES ON DATABASE terrafusion_{} TO terrafusion;\n\
         \\q",
        county_id.replace("-", "_"),
        password,
        county_id.replace("-", "_")
    );
    
    let result = Command::new(psql_exe)
        .args(&[
            "-h", "localhost",
            "-p", "5433",
            "-U", "postgres",
            "-d", "postgres",
            "-c", &create_db_sql
        ])
        .env("PGPASSWORD", "postgres")
        .output()
        .context("Failed to create database")?;
    
    if !result.status.success() {
        warn!("Database creation warning: {}", String::from_utf8_lossy(&result.stderr));
        // Continue as database might already exist
    }
    
    info!("Database and user created successfully");
    Ok(())
}

/// Run database migrations
async fn run_database_migrations(db_dir: &PathBuf, county_id: &str) -> Result<()> {
    info!("Running database migrations...");
    
    let psql_exe = db_dir.join("bin").join("psql.exe");
    let schema_file = db_dir.join("schema.sql");
    
    // Check if schema file exists
    if !schema_file.exists() {
        warn!("Schema file not found, skipping migrations");
        return Ok(());
    }
    
    let result = Command::new(psql_exe)
        .args(&[
            "-h", "localhost",
            "-p", "5433",
            "-U", "terrafusion",
            "-d", &format!("terrafusion_{}", county_id.replace("-", "_")),
            "-f", &schema_file.to_string_lossy()
        ])
        .env("PGPASSWORD", "terrafusion")
        .output()
        .context("Failed to run migrations")?;
    
    if !result.status.success() {
        anyhow::bail!(
            "Database migration failed: {}",
            String::from_utf8_lossy(&result.stderr)
        );
    }
    
    info!("Database migrations completed successfully");
    Ok(())
}

/// Stop PostgreSQL process
async fn stop_postgres_process(mut process: tokio::process::Child) -> Result<()> {
    info!("Stopping temporary PostgreSQL instance...");
    
    process.kill().await
        .context("Failed to stop PostgreSQL process")?;
    
    // Wait for process to exit
    let _ = process.wait().await;
    
    Ok(())
}

/// Save database configuration to file
async fn save_database_config(
    install_dir: &PathBuf,
    county_id: &str,
    password: &str,
) -> Result<()> {
    let config_dir = install_dir.join("config");
    fs::create_dir_all(&config_dir).await
        .context("Failed to create config directory")?;
    
    let db_config = format!(
        "# TerraFusion Database Configuration\n\
        DATABASE_URL=postgresql://terrafusion:{}@localhost:5433/terrafusion_{}\n\
        DATABASE_HOST=localhost\n\
        DATABASE_PORT=5433\n\
        DATABASE_NAME=terrafusion_{}\n\
        DATABASE_USER=terrafusion\n\
        DATABASE_PASSWORD={}\n\
        DATABASE_MAX_CONNECTIONS=20\n",
        password,
        county_id.replace("-", "_"),
        county_id.replace("-", "_"),
        password
    );
    
    let config_file = config_dir.join("database.env");
    fs::write(&config_file, db_config).await
        .context("Failed to save database configuration")?;
    
    info!("Database configuration saved to {}", config_file.display());
    Ok(())
}