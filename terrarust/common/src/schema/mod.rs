// @generated automatically by Diesel CLI.

diesel::table! {
    audit_entries (id) {
        id -> Uuid,
        event_type -> Text,
        resource_type -> Text,
        description -> Text,
        resource_id -> Nullable<Text>,
        operation_id -> Nullable<Int4>,
        previous_state -> Nullable<Jsonb>,
        new_state -> Nullable<Jsonb>,
        severity -> Text,
        user_id -> Nullable<Text>,
        username -> Nullable<Text>,
        ip_address -> Nullable<Text>,
        correlation_id -> Nullable<Text>,
        created_at -> Timestamptz,
    }
}

diesel::table! {
    sync_pairs (id) {
        id -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        source_system -> Text,
        target_system -> Text,
        source_config -> Jsonb,
        target_config -> Jsonb,
        field_mappings -> Jsonb,
        transformations -> Nullable<Jsonb>,
        filters -> Nullable<Jsonb>,
        schedule -> Nullable<Jsonb>,
        is_active -> Bool,
        created_at -> Timestamptz,
        updated_at -> Timestamptz,
        created_by -> Nullable<Text>,
        county_id -> Nullable<Text>,
    }
}

diesel::table! {
    sync_operations (id) {
        id -> Int4,
        sync_pair_id -> Uuid,
        status -> Text,
        started_at -> Nullable<Timestamptz>,
        completed_at -> Nullable<Timestamptz>,
        error_message -> Nullable<Text>,
        records_processed -> Nullable<Int4>,
        records_succeeded -> Nullable<Int4>,
        records_failed -> Nullable<Int4>,
        execution_details -> Nullable<Jsonb>,
        created_at -> Timestamptz,
        updated_at -> Timestamptz,
        created_by -> Nullable<Text>,
        correlation_id -> Nullable<Text>,
    }
}

diesel::table! {
    gis_exports (id) {
        id -> Uuid,
        county_id -> Text,
        export_format -> Text,
        status -> Text,
        area_of_interest -> Nullable<Jsonb>,
        layers -> Jsonb,
        parameters -> Jsonb,
        result_url -> Nullable<Text>,
        started_at -> Nullable<Timestamptz>,
        completed_at -> Nullable<Timestamptz>,
        error_message -> Nullable<Text>,
        created_at -> Timestamptz,
        updated_at -> Timestamptz,
        created_by -> Text,
    }
}

diesel::table! {
    system_metrics (id) {
        id -> Int4,
        metric_name -> Text,
        metric_value -> Float8,
        labels -> Jsonb,
        timestamp -> Timestamptz,
    }
}

diesel::table! {
    users (id) {
        id -> Uuid,
        username -> Text,
        email -> Text,
        password_hash -> Text,
        first_name -> Nullable<Text>,
        last_name -> Nullable<Text>,
        roles -> Array<Text>,
        counties -> Array<Text>,
        is_active -> Bool,
        created_at -> Timestamptz,
        updated_at -> Timestamptz,
        last_login -> Nullable<Timestamptz>,
    }
}

diesel::joinable!(sync_operations -> sync_pairs (sync_pair_id));

diesel::allow_tables_to_appear_in_same_query!(
    audit_entries,
    sync_pairs,
    sync_operations,
    gis_exports,
    system_metrics,
    users,
);