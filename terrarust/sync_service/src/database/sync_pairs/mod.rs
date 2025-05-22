use common::error::{Error, Result};
use common::models::sync_pair::{SyncPair, NewSyncPair, SyncPairUpdate};
use common::database::Database;
use common::schema::sync_pairs;
use diesel::prelude::*;
use diesel::pg::PgConnection;
use uuid::Uuid;
use chrono::Utc;

/// Get all sync pairs with optional filtering
pub async fn get_sync_pairs_with_filters(
    database: &Database,
    page: i64,
    per_page: i64,
    source_system: Option<&str>,
    target_system: Option<&str>,
    is_active: Option<bool>,
    county_id: Option<&str>,
) -> Result<(Vec<SyncPair>, i64)> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Calculate offset
    let offset = (page - 1) * per_page;
    
    // Build query
    let mut query = sync_pairs::table.into_boxed();
    
    // Apply filters
    if let Some(ss) = source_system {
        query = query.filter(source_system.eq(ss));
    }
    
    if let Some(ts) = target_system {
        query = query.filter(target_system.eq(ts));
    }
    
    if let Some(ia) = is_active {
        query = query.filter(is_active.eq(ia));
    }
    
    if let Some(cid) = county_id {
        query = query.filter(county_id.eq(cid));
    }
    
    // Execute count query
    let total_count: i64 = query.count().get_result(&conn)?;
    
    // Execute main query with pagination
    let sync_pairs: Vec<SyncPair> = query
        .order(created_at.desc())
        .limit(per_page)
        .offset(offset)
        .load(&conn)?;
    
    Ok((sync_pairs, total_count))
}

/// Get a specific sync pair by ID
pub async fn get_sync_pair_by_id(database: &Database, pair_id: Uuid) -> Result<SyncPair> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    let sync_pair = sync_pairs
        .filter(id.eq(pair_id))
        .first(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync pair not found: {}", pair_id)))?;
    
    Ok(sync_pair)
}

/// Create a new sync pair
pub async fn create_sync_pair(database: &Database, new_pair: NewSyncPair) -> Result<SyncPair> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    let now = Utc::now();
    
    let sync_pair = diesel::insert_into(sync_pairs)
        .values((
            id.eq(Uuid::new_v4()),
            name.eq(&new_pair.name),
            description.eq(&new_pair.description),
            source_system.eq(&new_pair.source_system),
            target_system.eq(&new_pair.target_system),
            source_config.eq(&new_pair.source_config),
            target_config.eq(&new_pair.target_config),
            field_mappings.eq(&new_pair.field_mappings),
            transformations.eq(&new_pair.transformations),
            filters.eq(&new_pair.filters),
            schedule.eq(&new_pair.schedule),
            is_active.eq(&new_pair.is_active),
            created_at.eq(now),
            updated_at.eq(now),
            created_by.eq(&new_pair.created_by),
            county_id.eq(&new_pair.county_id),
        ))
        .get_result(&conn)?;
    
    Ok(sync_pair)
}

/// Update an existing sync pair
pub async fn update_sync_pair_by_id(
    database: &Database,
    pair_id: Uuid,
    update: SyncPairUpdate,
) -> Result<SyncPair> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Check if sync pair exists
    let existing_pair = sync_pairs
        .filter(id.eq(pair_id))
        .first::<SyncPair>(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync pair not found: {}", pair_id)))?;
    
    // Build update query
    let mut update_query = diesel::update(sync_pairs.filter(id.eq(pair_id)));
    
    // Add fields to update
    let now = Utc::now();
    let mut updates = vec![(updated_at.eq(now))];
    
    if let Some(n) = update.name {
        updates.push(name.eq(n));
    }
    
    if let Some(d) = update.description {
        updates.push(description.eq(d));
    }
    
    if let Some(sc) = update.source_config {
        updates.push(source_config.eq(sc));
    }
    
    if let Some(tc) = update.target_config {
        updates.push(target_config.eq(tc));
    }
    
    if let Some(fm) = update.field_mappings {
        updates.push(field_mappings.eq(fm));
    }
    
    if let Some(t) = update.transformations {
        updates.push(transformations.eq(t));
    }
    
    if let Some(f) = update.filters {
        updates.push(filters.eq(f));
    }
    
    if let Some(s) = update.schedule {
        updates.push(schedule.eq(s));
    }
    
    if let Some(ia) = update.is_active {
        updates.push(is_active.eq(ia));
    }
    
    // Execute update
    let updated_pair = update_query
        .set(updates)
        .get_result(&conn)?;
    
    Ok(updated_pair)
}

/// Delete a sync pair
pub async fn delete_sync_pair_by_id(database: &Database, pair_id: Uuid) -> Result<()> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Check if sync pair exists
    let existing_pair = sync_pairs
        .filter(id.eq(pair_id))
        .first::<SyncPair>(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync pair not found: {}", pair_id)))?;
    
    // Delete the sync pair
    diesel::delete(sync_pairs.filter(id.eq(pair_id)))
        .execute(&conn)?;
    
    Ok(())
}

/// Toggle the active status of a sync pair
pub async fn toggle_sync_pair_status(database: &Database, pair_id: Uuid) -> Result<SyncPair> {
    use common::schema::sync_pairs::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Get current status
    let current_pair = sync_pairs
        .filter(id.eq(pair_id))
        .first::<SyncPair>(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync pair not found: {}", pair_id)))?;
    
    // Toggle status
    let new_status = !current_pair.is_active;
    
    // Update the status
    let now = Utc::now();
    let updated_pair = diesel::update(sync_pairs.filter(id.eq(pair_id)))
        .set((
            is_active.eq(new_status),
            updated_at.eq(now),
        ))
        .get_result(&conn)?;
    
    Ok(updated_pair)
}