-- Seed initial data for the TerraFusion platform

-- Insert admin user (password is 'password', hashed with bcrypt)
INSERT INTO users (
    id, username, email, password_hash, role, county_id,
    is_active, created_at, updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000001', -- UUID
    'admin',
    'admin@terrafusion.example',
    '$2a$12$lGqfioV7GMijdJZNZ3XB7eSMLEtPBcbpZBiS9in.3N9HrJgBrbjv2', -- hashed 'password'
    'admin',
    'TEST_COUNTY',
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Insert test user
INSERT INTO users (
    id, username, email, password_hash, role, county_id,
    is_active, created_at, updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000002', -- UUID
    'user',
    'user@terrafusion.example',
    '$2a$12$lGqfioV7GMijdJZNZ3XB7eSMLEtPBcbpZBiS9in.3N9HrJgBrbjv2', -- hashed 'password'
    'user',
    'TEST_COUNTY',
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Insert sample sync pair
INSERT INTO sync_pairs (
    id, name, description, source_system, source_config,
    target_system, target_config, county_id, sync_interval_minutes,
    is_active, created_at, updated_at, created_by, sync_conflict_strategy
) VALUES (
    '00000000-0000-0000-0000-000000000001', -- UUID
    'County Parcels Sync',
    'Synchronizes parcel data between Legacy GIS and Modern GIS',
    'Legacy GIS',
    '{"connection_string": "example_source_connection", "schema": "public", "table": "parcels"}',
    'Modern GIS',
    '{"connection_string": "example_target_connection", "schema": "public", "table": "parcels"}',
    'TEST_COUNTY',
    60, -- sync every hour
    TRUE,
    NOW(),
    NOW(),
    'admin',
    'TARGET_WINS'
) ON CONFLICT (id) DO NOTHING;

-- Insert another sample sync pair
INSERT INTO sync_pairs (
    id, name, description, source_system, source_config,
    target_system, target_config, county_id, sync_interval_minutes,
    is_active, created_at, updated_at, created_by, sync_conflict_strategy
) VALUES (
    '00000000-0000-0000-0000-000000000002', -- UUID
    'Tax Assessment Sync',
    'Synchronizes tax assessment data between Tax System and County Database',
    'Tax System',
    '{"connection_string": "example_tax_connection", "schema": "public", "table": "assessments"}',
    'County Database',
    '{"connection_string": "example_county_connection", "schema": "public", "table": "tax_assessments"}',
    'TEST_COUNTY',
    1440, -- sync once per day
    TRUE,
    NOW(),
    NOW(),
    'admin',
    'SOURCE_WINS'
) ON CONFLICT (id) DO NOTHING;