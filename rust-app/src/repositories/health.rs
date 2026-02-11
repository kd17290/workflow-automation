use sqlx::PgPool;
use tracing::info;

/// Save the health status to the database.
///
/// Mirrors Python's save_health_status from app/repositories/health.py.
///
/// # Arguments
/// * `pool` - The database connection pool.
/// * `status` - The status string to save (e.g., "ok").
pub async fn save_health_status(pool: &PgPool, status: &str) -> Result<(), sqlx::Error> {
    info!("Saving health status: {}", status);
    sqlx::query("INSERT INTO health_status (status, timestamp) VALUES ($1, NOW())")
        .bind(status)
        .execute(pool)
        .await?;
    Ok(())
}
