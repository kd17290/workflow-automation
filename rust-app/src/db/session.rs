use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;

use crate::core::config::Settings;

/// Create a PostgreSQL connection pool from settings.
///
/// Mirrors Python's SessionLocal / engine setup from app/db/session.py.
pub async fn create_pool(settings: &Settings) -> Result<PgPool, sqlx::Error> {
    let pool = PgPoolOptions::new()
        .max_connections(100)
        .acquire_timeout(std::time::Duration::from_secs(30))
        .idle_timeout(std::time::Duration::from_secs(3600))
        .connect(&settings.database_url())
        .await?;

    Ok(pool)
}

/// Run database migrations — create tables if they don't exist.
///
/// Mirrors Python's `Base.metadata.create_all(bind=engine)`.
pub async fn run_migrations(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS health_status (
            id SERIAL PRIMARY KEY,
            status VARCHAR NOT NULL DEFAULT 'ok',
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS workflow_definitions (
            uuid VARCHAR PRIMARY KEY,
            id VARCHAR,
            name VARCHAR NOT NULL,
            description VARCHAR,
            steps JSONB NOT NULL
        )
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS workflow_runs (
            uuid VARCHAR PRIMARY KEY,
            id VARCHAR,
            workflow_id VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            payload JSONB NOT NULL,
            started_at VARCHAR NOT NULL,
            completed_at VARCHAR,
            error VARCHAR,
            step_results JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Create indexes matching the Python models (wrapped to handle pre-existing indexes)
    sqlx::query(
        r#"
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workflow_runs_workflow_id'
            ) THEN
                CREATE INDEX idx_workflow_runs_workflow_id ON workflow_runs (workflow_id);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workflow_runs_status'
            ) THEN
                CREATE INDEX idx_workflow_runs_status ON workflow_runs (status);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workflow_runs_started_at'
            ) THEN
                CREATE INDEX idx_workflow_runs_started_at ON workflow_runs (started_at);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workflow_runs_uuid_cursor'
            ) THEN
                CREATE INDEX idx_workflow_runs_uuid_cursor ON workflow_runs (uuid);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workflow_definitions_name'
            ) THEN
                CREATE INDEX idx_workflow_definitions_name ON workflow_definitions (name);
            END IF;
        END
        $$;
        "#,
    )
    .execute(pool)
    .await?;

    Ok(())
}
