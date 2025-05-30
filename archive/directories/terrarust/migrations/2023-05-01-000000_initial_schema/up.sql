-- Initial database schema for TerraFusion platform

-- Create sync pairs table
CREATE TABLE IF NOT EXISTS sync_pairs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_system VARCHAR(255) NOT NULL,
    source_config JSONB NOT NULL,
    target_system VARCHAR(255) NOT NULL,
    target_config JSONB NOT NULL,
    county_id VARCHAR(255) NOT NULL,
    sync_interval_minutes INTEGER,
    last_sync_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    sync_conflict_strategy VARCHAR(255),
    metadata JSONB
);

-- Create sync operations table
CREATE TABLE IF NOT EXISTS sync_operations (
    id UUID PRIMARY KEY,
    sync_pair_id UUID NOT NULL REFERENCES sync_pairs(id),
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_records INTEGER,
    records_processed INTEGER,
    records_succeeded INTEGER,
    records_failed INTEGER,
    error_message TEXT,
    initiated_by VARCHAR(255) NOT NULL,
    county_id VARCHAR(255) NOT NULL,
    execution_logs JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create sync diffs table
CREATE TABLE IF NOT EXISTS sync_diffs (
    id UUID PRIMARY KEY,
    sync_operation_id UUID NOT NULL REFERENCES sync_operations(id),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    source_data JSONB,
    target_data JSONB,
    diff_details JSONB,
    sync_status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create validation issues table
CREATE TABLE IF NOT EXISTS validation_issues (
    id UUID PRIMARY KEY,
    sync_operation_id UUID NOT NULL REFERENCES sync_operations(id),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    field_name VARCHAR(255),
    issue_type VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    source_value JSONB,
    target_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create sync stats table
CREATE TABLE IF NOT EXISTS sync_stats (
    sync_operation_id UUID PRIMARY KEY REFERENCES sync_operations(id),
    total_records INTEGER NOT NULL,
    added_count INTEGER NOT NULL,
    modified_count INTEGER NOT NULL,
    deleted_count INTEGER NOT NULL,
    unchanged_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    validation_issues_count INTEGER NOT NULL,
    duration_seconds FLOAT NOT NULL,
    avg_record_processing_ms FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255) NOT NULL,
    resource_id VARCHAR(255),
    description TEXT NOT NULL,
    user_id VARCHAR(255),
    username VARCHAR(255),
    county_id VARCHAR(255),
    ip_address VARCHAR(50),
    previous_state JSONB,
    new_state JSONB,
    operation_id UUID,
    correlation_id VARCHAR(255),
    severity VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    county_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create gis exports table
CREATE TABLE IF NOT EXISTS gis_exports (
    id UUID PRIMARY KEY,
    county_id VARCHAR(255) NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    area_of_interest JSONB,
    layers JSONB NOT NULL,
    parameters JSONB NOT NULL,
    result_url VARCHAR(1024),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by VARCHAR(255) NOT NULL
);

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY,
    service VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_labels JSONB,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sync_operations_sync_pair_id ON sync_operations(sync_pair_id);
CREATE INDEX IF NOT EXISTS idx_sync_operations_county_id ON sync_operations(county_id);
CREATE INDEX IF NOT EXISTS idx_sync_operations_status ON sync_operations(status);
CREATE INDEX IF NOT EXISTS idx_sync_diffs_sync_operation_id ON sync_diffs(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_validation_issues_sync_operation_id ON validation_issues(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_county_id ON audit_log(county_id);
CREATE INDEX IF NOT EXISTS idx_gis_exports_county_id ON gis_exports(county_id);
CREATE INDEX IF NOT EXISTS idx_gis_exports_status ON gis_exports(status);
CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service);
CREATE INDEX IF NOT EXISTS idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_collected_at ON metrics(collected_at);