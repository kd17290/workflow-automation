use async_trait::async_trait;
use sqlx::PgPool;
use std::collections::HashMap;

use crate::db::models::run::WorkflowRunRow;
use crate::db::models::workflow::WorkflowDefinitionRow;
use crate::schemas::run::WorkflowRun;
use crate::schemas::workflow::WorkflowDefinition;
use crate::storage::base::{Storage, StorageError};

/// PostgreSQL-backed storage for WorkflowDefinition.
///
/// Mirrors Python's DBStorage from app/storage/db_storage.py.
/// Single Responsibility: only handles DB persistence for WorkflowDefinition.
pub struct WorkflowDefinitionStorage {
    pool: PgPool,
}

impl WorkflowDefinitionStorage {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl Storage<WorkflowDefinition> for WorkflowDefinitionStorage {
    async fn get(&self, uuid: &str) -> Result<Option<WorkflowDefinition>, StorageError> {
        let row = sqlx::query_as::<_, WorkflowDefinitionRow>(
            "SELECT uuid, id, name, description, steps FROM workflow_definitions WHERE uuid = $1",
        )
        .bind(uuid)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some(r) => {
                let steps = serde_json::from_value(r.steps)?;
                Ok(Some(WorkflowDefinition {
                    uuid: Some(r.uuid),
                    id: r.id,
                    name: r.name,
                    description: r.description,
                    steps,
                }))
            }
            None => Ok(None),
        }
    }

    async fn create(&self, item: &mut WorkflowDefinition) -> Result<String, StorageError> {
        let uuid = uuid::Uuid::new_v4().simple().to_string();
        item.uuid = Some(uuid.clone());

        let steps_json = serde_json::to_value(&item.steps)?;

        sqlx::query(
            "INSERT INTO workflow_definitions (uuid, id, name, description, steps) VALUES ($1, $2, $3, $4, $5)",
        )
        .bind(&uuid)
        .bind(&item.id)
        .bind(&item.name)
        .bind(&item.description)
        .bind(&steps_json)
        .execute(&self.pool)
        .await?;

        Ok(uuid)
    }

    async fn delete(&self, uuid: &str) -> Result<bool, StorageError> {
        let result = sqlx::query("DELETE FROM workflow_definitions WHERE uuid = $1")
            .bind(uuid)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }

    async fn update(&self, item: &WorkflowDefinition) -> Result<bool, StorageError> {
        let uuid = item.uuid.as_deref().ok_or_else(|| {
            StorageError::Database("Cannot update item without uuid".to_string())
        })?;

        let steps_json = serde_json::to_value(&item.steps)?;

        let result = sqlx::query(
            "UPDATE workflow_definitions SET id = $1, name = $2, description = $3, steps = $4 WHERE uuid = $5",
        )
        .bind(&item.id)
        .bind(&item.name)
        .bind(&item.description)
        .bind(&steps_json)
        .bind(uuid)
        .execute(&self.pool)
        .await?;

        Ok(result.rows_affected() > 0)
    }

    async fn list_all(&self) -> Result<Vec<WorkflowDefinition>, StorageError> {
        let rows = sqlx::query_as::<_, WorkflowDefinitionRow>(
            "SELECT uuid, id, name, description, steps FROM workflow_definitions",
        )
        .fetch_all(&self.pool)
        .await?;

        let mut results = Vec::with_capacity(rows.len());
        for r in rows {
            let steps = serde_json::from_value(r.steps)?;
            results.push(WorkflowDefinition {
                uuid: Some(r.uuid),
                id: r.id,
                name: r.name,
                description: r.description,
                steps,
            });
        }
        Ok(results)
    }

    async fn list_paginated(
        &self,
        limit: i64,
        cursor: Option<&str>,
    ) -> Result<(Vec<WorkflowDefinition>, Option<String>), StorageError> {
        let rows = match cursor {
            Some(c) => {
                sqlx::query_as::<_, WorkflowDefinitionRow>(
                    "SELECT uuid, id, name, description, steps FROM workflow_definitions WHERE uuid > $1 ORDER BY uuid LIMIT $2",
                )
                .bind(c)
                .bind(limit + 1)
                .fetch_all(&self.pool)
                .await?
            }
            None => {
                sqlx::query_as::<_, WorkflowDefinitionRow>(
                    "SELECT uuid, id, name, description, steps FROM workflow_definitions ORDER BY uuid LIMIT $1",
                )
                .bind(limit + 1)
                .fetch_all(&self.pool)
                .await?
            }
        };

        let has_more = rows.len() as i64 > limit;
        let rows: Vec<_> = rows.into_iter().take(limit as usize).collect();
        let next_cursor = if has_more {
            rows.last().map(|r| r.uuid.clone())
        } else {
            None
        };

        let mut results = Vec::with_capacity(rows.len());
        for r in rows {
            let steps = serde_json::from_value(r.steps)?;
            results.push(WorkflowDefinition {
                uuid: Some(r.uuid),
                id: r.id,
                name: r.name,
                description: r.description,
                steps,
            });
        }
        Ok((results, next_cursor))
    }
}

/// PostgreSQL-backed storage for WorkflowRun.
///
/// Single Responsibility: only handles DB persistence for WorkflowRun.
pub struct WorkflowRunStorage {
    pool: PgPool,
}

impl WorkflowRunStorage {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl Storage<WorkflowRun> for WorkflowRunStorage {
    async fn get(&self, uuid: &str) -> Result<Option<WorkflowRun>, StorageError> {
        let row = sqlx::query_as::<_, WorkflowRunRow>(
            "SELECT uuid, id, workflow_id, status, payload, started_at, completed_at, error, step_results FROM workflow_runs WHERE uuid = $1",
        )
        .bind(uuid)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some(r) => Ok(Some(row_to_workflow_run(r)?)),
            None => Ok(None),
        }
    }

    async fn create(&self, item: &mut WorkflowRun) -> Result<String, StorageError> {
        let uuid = uuid::Uuid::new_v4().simple().to_string();
        item.uuid = Some(uuid.clone());

        let payload_json = serde_json::to_value(&item.payload)?;
        let step_results_json = serde_json::to_value(&item.step_results)?;

        sqlx::query(
            "INSERT INTO workflow_runs (uuid, id, workflow_id, status, payload, started_at, completed_at, error, step_results) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
        )
        .bind(&uuid)
        .bind(&item.id)
        .bind(&item.workflow_id)
        .bind(item.status.to_string())
        .bind(&payload_json)
        .bind(&item.started_at)
        .bind(&item.completed_at)
        .bind(&item.error)
        .bind(&step_results_json)
        .execute(&self.pool)
        .await?;

        Ok(uuid)
    }

    async fn delete(&self, uuid: &str) -> Result<bool, StorageError> {
        let result = sqlx::query("DELETE FROM workflow_runs WHERE uuid = $1")
            .bind(uuid)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }

    async fn update(&self, item: &WorkflowRun) -> Result<bool, StorageError> {
        let uuid = item.uuid.as_deref().ok_or_else(|| {
            StorageError::Database("Cannot update item without uuid".to_string())
        })?;

        let payload_json = serde_json::to_value(&item.payload)?;
        let step_results_json = serde_json::to_value(&item.step_results)?;

        let result = sqlx::query(
            "UPDATE workflow_runs SET id = $1, workflow_id = $2, status = $3, payload = $4, started_at = $5, completed_at = $6, error = $7, step_results = $8 WHERE uuid = $9",
        )
        .bind(&item.id)
        .bind(&item.workflow_id)
        .bind(item.status.to_string())
        .bind(&payload_json)
        .bind(&item.started_at)
        .bind(&item.completed_at)
        .bind(&item.error)
        .bind(&step_results_json)
        .bind(uuid)
        .execute(&self.pool)
        .await?;

        Ok(result.rows_affected() > 0)
    }

    async fn list_all(&self) -> Result<Vec<WorkflowRun>, StorageError> {
        let rows = sqlx::query_as::<_, WorkflowRunRow>(
            "SELECT uuid, id, workflow_id, status, payload, started_at, completed_at, error, step_results FROM workflow_runs",
        )
        .fetch_all(&self.pool)
        .await?;

        let mut results = Vec::with_capacity(rows.len());
        for r in rows {
            results.push(row_to_workflow_run(r)?);
        }
        Ok(results)
    }

    async fn list_paginated(
        &self,
        limit: i64,
        cursor: Option<&str>,
    ) -> Result<(Vec<WorkflowRun>, Option<String>), StorageError> {
        let rows = match cursor {
            Some(c) => {
                sqlx::query_as::<_, WorkflowRunRow>(
                    "SELECT uuid, id, workflow_id, status, payload, started_at, completed_at, error, step_results FROM workflow_runs WHERE uuid > $1 ORDER BY uuid LIMIT $2",
                )
                .bind(c)
                .bind(limit + 1)
                .fetch_all(&self.pool)
                .await?
            }
            None => {
                sqlx::query_as::<_, WorkflowRunRow>(
                    "SELECT uuid, id, workflow_id, status, payload, started_at, completed_at, error, step_results FROM workflow_runs ORDER BY uuid LIMIT $1",
                )
                .bind(limit + 1)
                .fetch_all(&self.pool)
                .await?
            }
        };

        let has_more = rows.len() as i64 > limit;
        let rows: Vec<_> = rows.into_iter().take(limit as usize).collect();
        let next_cursor = if has_more {
            rows.last().map(|r| r.uuid.clone())
        } else {
            None
        };

        let mut results = Vec::with_capacity(rows.len());
        for r in rows {
            results.push(row_to_workflow_run(r)?);
        }
        Ok((results, next_cursor))
    }
}

/// Convert a database row to a WorkflowRun domain object.
fn row_to_workflow_run(r: WorkflowRunRow) -> Result<WorkflowRun, StorageError> {
    let payload: HashMap<String, serde_json::Value> = serde_json::from_value(r.payload)?;
    let step_results = serde_json::from_value(r.step_results)?;
    let status = serde_json::from_value(serde_json::Value::String(r.status))?;

    Ok(WorkflowRun {
        uuid: Some(r.uuid),
        id: r.id,
        workflow_id: r.workflow_id,
        status,
        payload,
        started_at: r.started_at,
        completed_at: r.completed_at,
        error: r.error,
        step_results,
    })
}
