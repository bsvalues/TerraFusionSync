pub mod sync;
pub mod gis;
pub mod audit;

use crate::config::ServiceConfig;
use common::database::Database;

#[derive(Clone)]
pub struct Services {
    pub sync: sync::SyncServiceClient,
    pub gis: gis::GisExportClient,
    pub audit: audit::AuditClient,
}

impl Services {
    pub fn new(config: &ServiceConfig, database: Database) -> Self {
        Self {
            sync: sync::SyncServiceClient::new(config.sync_service_url.clone()),
            gis: gis::GisExportClient::new(config.gis_service_url.clone()),
            audit: audit::AuditClient::new(database),
        }
    }
}