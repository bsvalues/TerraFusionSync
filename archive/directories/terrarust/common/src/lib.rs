/// TerraFusion Platform Common Library
/// 
/// This library provides common functionality shared across all TerraFusion
/// microservices, including error handling, database connections, models,
/// telemetry, and utilities.

pub mod errors;
pub mod database;
pub mod models;
pub mod telemetry;
pub mod config;
pub mod utils;
pub mod geo;

// Re-export common types for convenience
pub use errors::{Error, Result};
pub use database::DbPool;

/// Version information for the TerraFusion Platform
pub struct Version {
    pub version: &'static str,
    pub git_hash: &'static str,
    pub build_date: &'static str,
}

/// Get the current version of the TerraFusion Platform
pub fn version() -> Version {
    Version {
        version: env!("CARGO_PKG_VERSION"),
        git_hash: option_env!("GIT_HASH").unwrap_or("unknown"),
        build_date: option_env!("BUILD_DATE").unwrap_or("unknown"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        let v = version();
        assert!(!v.version.is_empty());
    }
}