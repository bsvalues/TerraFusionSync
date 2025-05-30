#!/bin/bash
# TerraFusion Platform - Rust Migration Deployment Script
# This script handles the deployment of Rust-based services and database migrations

set -e

# Configuration
CONFIG_FILE="${1:-config/deployment.conf}"
RUST_DIR="./terrarust"
SERVICES=("api_gateway" "sync_service" "gis_export")
OUTPUT_DIR="./target/release"
LOG_DIR="./logs"

# Create necessary directories
mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    echo "Loaded configuration from $CONFIG_FILE"
else
    echo "Configuration file not found, using defaults"
fi

# Deploy function for a single service
deploy_service() {
    local service="$1"
    echo "Deploying $service..."
    
    # Compile the service
    echo "  Compiling $service..."
    cd "$RUST_DIR"
    cargo build --release --package "$service"
    cd -
    
    # Create service directory
    mkdir -p "$OUTPUT_DIR/$service"
    
    # Copy the binary
    cp "$RUST_DIR/target/release/$service" "$OUTPUT_DIR/$service/"
    
    # Copy configuration
    cp -r "$RUST_DIR/config" "$OUTPUT_DIR/$service/"
    
    echo "  $service deployed to $OUTPUT_DIR/$service/"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    
    cd "$RUST_DIR"
    cargo run --release --bin migration_runner -- up
    cd -
    
    echo "Migrations completed"
}

# Deploy everything
deploy_all() {
    echo "Starting full deployment of TerraFusion Platform (Rust)"
    
    # Build common library first
    echo "Building common library..."
    cd "$RUST_DIR"
    cargo build --release --package common
    cd -
    
    # Deploy each service
    for service in "${SERVICES[@]}"; do
        deploy_service "$service"
    done
    
    # Run migrations
    run_migrations
    
    echo "Deployment completed successfully"
}

# Parse command line arguments
case "$2" in
    service)
        if [ -z "$3" ]; then
            echo "Error: Service name required"
            echo "Usage: $0 [$CONFIG_FILE] service <service_name>"
            exit 1
        fi
        
        if [[ ! " ${SERVICES[@]} " =~ " $3 " ]]; then
            echo "Error: Unknown service '$3'"
            echo "Available services: ${SERVICES[@]}"
            exit 1
        fi
        
        deploy_service "$3"
        ;;
    migrations)
        run_migrations
        ;;
    *)
        deploy_all
        ;;
esac

echo "Done"