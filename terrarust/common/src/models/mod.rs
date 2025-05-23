pub mod sync;
pub mod geo;
pub mod audit;
pub mod user;

use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Base model with common fields
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BaseModel {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Pagination parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginationParams {
    pub page: Option<usize>,
    pub per_page: Option<usize>,
}

impl Default for PaginationParams {
    fn default() -> Self {
        Self {
            page: Some(1),
            per_page: Some(20),
        }
    }
}

impl PaginationParams {
    /// Calculate the offset based on page and per_page
    pub fn offset(&self) -> usize {
        let page = self.page.unwrap_or(1).max(1);
        let per_page = self.per_page.unwrap_or(20);
        (page - 1) * per_page
    }
    
    /// Get the limit (per_page)
    pub fn limit(&self) -> usize {
        self.per_page.unwrap_or(20)
    }
}

/// Paginated response wrapper
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginatedResponse<T> {
    pub items: Vec<T>,
    pub total: usize,
    pub page: usize,
    pub per_page: usize,
    pub total_pages: usize,
}

impl<T> PaginatedResponse<T> {
    /// Create a new paginated response
    pub fn new(items: Vec<T>, total: usize, params: &PaginationParams) -> Self {
        let page = params.page.unwrap_or(1).max(1);
        let per_page = params.per_page.unwrap_or(20);
        let total_pages = (total as f64 / per_page as f64).ceil() as usize;
        
        Self {
            items,
            total,
            page,
            per_page,
            total_pages,
        }
    }
    
    /// Check if there is a next page
    pub fn has_next_page(&self) -> bool {
        self.page < self.total_pages
    }
    
    /// Check if there is a previous page
    pub fn has_prev_page(&self) -> bool {
        self.page > 1
    }
    
    /// Get the next page number
    pub fn next_page(&self) -> Option<usize> {
        if self.has_next_page() {
            Some(self.page + 1)
        } else {
            None
        }
    }
    
    /// Get the previous page number
    pub fn prev_page(&self) -> Option<usize> {
        if self.has_prev_page() {
            Some(self.page - 1)
        } else {
            None
        }
    }
    
    /// Create an empty paginated response
    pub fn empty(params: &PaginationParams) -> Self {
        Self::new(Vec::new(), 0, params)
    }
}

/// Filter parameters for queries
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct FilterParams {
    pub from_date: Option<DateTime<Utc>>,
    pub to_date: Option<DateTime<Utc>>,
    pub status: Option<String>,
    pub search: Option<String>,
    pub county_id: Option<String>,
    pub user_id: Option<String>,
}

/// Sort direction
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum SortDirection {
    #[serde(rename = "asc")]
    Ascending,
    #[serde(rename = "desc")]
    Descending,
}

impl Default for SortDirection {
    fn default() -> Self {
        Self::Descending
    }
}

/// Sort parameters
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SortParams {
    pub field: Option<String>,
    pub direction: Option<SortDirection>,
}

/// Health status for services
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum HealthStatus {
    #[serde(rename = "up")]
    Up,
    #[serde(rename = "down")]
    Down,
    #[serde(rename = "degraded")]
    Degraded,
    #[serde(rename = "unknown")]
    Unknown,
}

impl Default for HealthStatus {
    fn default() -> Self {
        Self::Unknown
    }
}

/// Health check response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheck {
    pub status: HealthStatus,
    pub version: String,
    pub services: Vec<ServiceHealth>,
    pub timestamp: DateTime<Utc>,
}

/// Service health information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceHealth {
    pub name: String,
    pub status: HealthStatus,
    pub version: Option<String>,
    pub latency_ms: Option<u64>,
    pub message: Option<String>,
    pub last_check: DateTime<Utc>,
}

/// Generic API response wrapper
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
    pub timestamp: DateTime<Utc>,
}

impl<T> ApiResponse<T> {
    /// Create a successful response
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
            timestamp: Utc::now(),
        }
    }
    
    /// Create an error response
    pub fn error(error: impl ToString) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(error.to_string()),
            timestamp: Utc::now(),
        }
    }
}