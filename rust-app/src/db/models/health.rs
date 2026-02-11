use chrono::{DateTime, Utc};
use sqlx::FromRow;

/// Database model for system health checks.
///
/// Mirrors Python's HealthStatus model from app/db/models/health.py.
#[derive(Debug, Clone, FromRow)]
pub struct HealthStatusRow {
    pub id: i32,
    pub status: String,
    pub timestamp: DateTime<Utc>,
}
