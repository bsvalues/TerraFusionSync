"""
Seed script to populate the database with initial test data.

This script creates sample data for the TerraFusion SyncService application
to allow for testing and demonstration.
"""

import os
import random
from datetime import datetime, timedelta

from flask import Flask
from models import db, SyncPair, SyncOperation, SystemMetrics, AuditEntry

# Database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create a Flask app for the database context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)


def seed_sync_pairs():
    """Create sample synchronization pairs."""
    pairs = [
        {
            "name": "PACS to CAMA - Parcel Data",
            "description": "Synchronize property parcel data from the PACS system to CAMA",
            "source_system": "PACS",
            "target_system": "CAMA",
            "config": {
                "fields": ["parcel_id", "owner", "address", "value", "tax_status"],
                "schedule": "daily",
                "time": "01:00",
                "filter": "last_modified > '2023-01-01'"
            },
            "active": True
        },
        {
            "name": "CAMA to GIS - Property Boundaries",
            "description": "Synchronize property boundary data from CAMA to GIS",
            "source_system": "CAMA",
            "target_system": "GIS",
            "config": {
                "fields": ["parcel_id", "geometry", "zoning", "land_use"],
                "schedule": "weekly",
                "time": "02:00",
                "filter": "status = 'approved'"
            },
            "active": True
        },
        {
            "name": "ERP to CRM - Customer Data",
            "description": "Synchronize customer data from ERP to CRM",
            "source_system": "ERP",
            "target_system": "CRM",
            "config": {
                "fields": ["customer_id", "name", "contact_info", "account_status"],
                "schedule": "hourly",
                "time": "XX:15",
                "filter": "last_update > NOW() - INTERVAL '1 hour'"
            },
            "active": True
        },
        {
            "name": "PACS to ERP - Financial Data",
            "description": "Synchronize financial transactions from PACS to ERP",
            "source_system": "PACS",
            "target_system": "ERP",
            "config": {
                "fields": ["transaction_id", "amount", "date", "type", "account"],
                "schedule": "daily",
                "time": "23:00",
                "filter": "date = CURRENT_DATE"
            },
            "active": False
        }
    ]
    
    # Add sync pairs to database
    for pair_data in pairs:
        existing = SyncPair.query.filter_by(name=pair_data["name"]).first()
        if not existing:
            pair = SyncPair(
                name=pair_data["name"],
                description=pair_data["description"],
                source_system=pair_data["source_system"],
                target_system=pair_data["target_system"],
                config=pair_data["config"],
                active=pair_data["active"]
            )
            db.session.add(pair)
    
    db.session.commit()
    return SyncPair.query.all()


def seed_sync_operations(pairs):
    """Create sample sync operations for the given pairs."""
    operations = []
    now = datetime.utcnow()
    
    # Create operations over the past 7 days
    for i in range(50):
        # Select a random pair
        pair = random.choice(pairs)
        
        # Determine operation parameters
        op_type = random.choice(["full", "incremental"])
        started_at = now - timedelta(days=random.randint(0, 7),
                               hours=random.randint(0, 23),
                               minutes=random.randint(0, 59))
        completed_at = started_at + timedelta(minutes=random.randint(5, 60))
        
        status = random.choices(
            ["completed", "failed", "pending", "running"],
            weights=[0.7, 0.15, 0.1, 0.05],
            k=1
        )[0]
        
        # For pending/running, remove completion time
        if status in ["pending", "running"]:
            completed_at = None
        
        # Generate random metrics
        total_records = random.randint(100, 10000)
        processed_records = total_records if status == "completed" else random.randint(0, total_records)
        successful_records = processed_records
        failed_records = 0
        error_message = None
        
        # For failed operations, add error data
        if status == "failed":
            failed_records = random.randint(1, processed_records)
            successful_records = processed_records - failed_records
            error_messages = [
                "Connection timeout",
                "Authentication failure",
                "Schema validation error",
                "Data integrity constraint violation",
                "Remote API unavailable"
            ]
            error_message = random.choice(error_messages)
        
        # Create operation object
        operation = SyncOperation(
            sync_pair_id=pair.id,
            operation_type=op_type,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            total_records=total_records,
            processed_records=processed_records,
            successful_records=successful_records,
            failed_records=failed_records,
            error_message=error_message,
            metrics={
                "avg_record_processing_time": round(random.uniform(0.01, 2.0), 4),
                "network_latency": round(random.uniform(5, 200), 2),
                "memory_usage": round(random.uniform(20, 80), 2)
            }
        )
        
        operations.append(operation)
        db.session.add(operation)
    
    db.session.commit()
    return operations


def seed_system_metrics():
    """Create sample system metrics data points."""
    metrics = []
    now = datetime.utcnow()
    
    # Create metrics for the past 24 hours
    for i in range(100):
        timestamp = now - timedelta(hours=random.randint(0, 24),
                              minutes=random.randint(0, 59))
        
        # Generate random but somewhat realistic metrics
        cpu_base = 30  # Base CPU usage
        memory_base = 40  # Base memory usage
        disk_base = 65  # Base disk usage
        
        # Add some variance
        cpu_variance = random.uniform(-20, 40)
        memory_variance = random.uniform(-10, 25)
        disk_variance = random.uniform(-5, 15)
        
        # Ensure metrics stay within realistic bounds
        cpu_usage = max(5, min(95, cpu_base + cpu_variance))
        memory_usage = max(10, min(95, memory_base + memory_variance))
        disk_usage = max(40, min(90, disk_base + disk_variance))
        
        # Other metrics
        active_connections = random.randint(2, 50)
        response_time = random.uniform(0.05, 2.0)
        error_count = random.choices([0, random.randint(1, 10)], weights=[0.85, 0.15], k=1)[0]
        sync_operations_count = random.randint(0, 10)
        
        metric = SystemMetrics(
            timestamp=timestamp,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_connections=active_connections,
            response_time=response_time,
            error_count=error_count,
            sync_operations_count=sync_operations_count
        )
        
        metrics.append(metric)
        db.session.add(metric)
    
    db.session.commit()
    return metrics


def seed_audit_entries(operations):
    """Create sample audit entries based on operations."""
    entries = []
    
    # Create system startup entry
    startup_entry = AuditEntry(
        timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
        event_type="system_startup",
        resource_type="system",
        description="System initialized and services started",
        severity="info"
    )
    db.session.add(startup_entry)
    entries.append(startup_entry)
    
    # Create entries for operations
    for operation in operations:
        # Start entry
        start_entry = AuditEntry(
            timestamp=operation.started_at,
            event_type="sync_started",
            resource_type="sync_operation",
            resource_id=str(operation.id),
            operation_id=operation.id,
            description=f"{operation.operation_type.capitalize()} sync started for pair ID {operation.sync_pair_id}",
            severity="info",
            correlation_id=f"sync-{operation.id}"
        )
        db.session.add(start_entry)
        entries.append(start_entry)
        
        # Only add completion entry if operation is completed or failed
        if operation.status in ["completed", "failed"]:
            event_type = "sync_completed" if operation.status == "completed" else "sync_failed"
            severity = "info" if operation.status == "completed" else "error"
            
            description = (
                f"{operation.operation_type.capitalize()} sync {operation.status} "
                f"for pair ID {operation.sync_pair_id}"
            )
            
            if operation.error_message:
                description += f": {operation.error_message}"
            
            complete_entry = AuditEntry(
                timestamp=operation.completed_at or datetime.utcnow(),
                event_type=event_type,
                resource_type="sync_operation",
                resource_id=str(operation.id),
                operation_id=operation.id,
                description=description,
                severity=severity,
                correlation_id=f"sync-{operation.id}"
            )
            db.session.add(complete_entry)
            entries.append(complete_entry)
    
    # Add some config change events
    for i in range(10):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        pair_id = random.randint(1, 4)
        
        config_entry = AuditEntry(
            timestamp=timestamp,
            event_type="config_changed",
            resource_type="sync_pair",
            resource_id=str(pair_id),
            description=f"Configuration updated for sync pair ID {pair_id}",
            severity="info"
        )
        db.session.add(config_entry)
        entries.append(config_entry)
    
    # Add some security audit events
    security_events = [
        "user_login_success",
        "user_login_failed",
        "permission_changed",
        "user_logout"
    ]
    
    for i in range(20):
        timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
        event_type = random.choice(security_events)
        
        security_entry = AuditEntry(
            timestamp=timestamp,
            event_type=event_type,
            resource_type="user",
            resource_id=str(random.randint(1, 5)),
            description=f"Security event: {event_type}",
            severity="warning" if event_type == "user_login_failed" else "info",
            ip_address=f"192.168.1.{random.randint(2, 254)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        db.session.add(security_entry)
        entries.append(security_entry)
    
    db.session.commit()
    return entries


def main():
    """Main function to seed the database with sample data."""
    with app.app_context():
        # First check if we already have data
        existing_pairs = SyncPair.query.count()
        existing_operations = SyncOperation.query.count()
        existing_metrics = SystemMetrics.query.count()
        existing_audit = AuditEntry.query.count()
        
        if existing_pairs > 0 and existing_operations > 0 and existing_metrics > 0 and existing_audit > 0:
            print("Database already has data. Skipping seeding.")
            return
        
        # Create tables if they don't exist
        db.create_all()
        
        # Seed data
        print("Seeding sync pairs...")
        pairs = seed_sync_pairs()
        
        print("Seeding sync operations...")
        operations = seed_sync_operations(pairs)
        
        print("Seeding system metrics...")
        metrics = seed_system_metrics()
        
        print("Seeding audit entries...")
        entries = seed_audit_entries(operations)
        
        print(f"Database seeded with:")
        print(f"- {len(pairs)} sync pairs")
        print(f"- {len(operations)} sync operations")
        print(f"- {len(metrics)} system metrics")
        print(f"- {len(entries)} audit entries")


if __name__ == "__main__":
    main()