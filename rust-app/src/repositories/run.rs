use std::sync::Arc;

use crate::schemas::run::WorkflowRun;
use crate::storage::base::{Storage, StorageError};

/// Repository for managing WorkflowRun entities.
///
/// Mirrors Python's WorkflowRunRepository from app/repositories/run.py.
/// Follows Single Responsibility Principle — only orchestrates storage calls
/// for WorkflowRun.
pub struct WorkflowRunRepository {
    storage: Arc<dyn Storage<WorkflowRun>>,
}

impl WorkflowRunRepository {
    /// Initialize the repository with a storage backend.
    pub fn new(storage: Arc<dyn Storage<WorkflowRun>>) -> Self {
        Self { storage }
    }

    /// Retrieve a workflow run by its UUID.
    pub async fn get_workflow_run(&self, uuid: &str) -> Result<Option<WorkflowRun>, StorageError> {
        self.storage.get(uuid).await
    }

    /// Create a new workflow run.
    pub async fn create_workflow_run(&self, run: &mut WorkflowRun) -> Result<String, StorageError> {
        self.storage.create(run).await
    }

    /// Delete a workflow run by its UUID.
    pub async fn delete_workflow_run(&self, uuid: &str) -> Result<bool, StorageError> {
        self.storage.delete(uuid).await
    }

    /// Update an existing workflow run.
    pub async fn update_workflow_run(&self, run: &WorkflowRun) -> Result<bool, StorageError> {
        self.storage.update(run).await
    }

    /// List all workflow runs.
    pub async fn list_workflow_runs(&self) -> Result<Vec<WorkflowRun>, StorageError> {
        self.storage.list_all().await
    }

    /// List workflow runs with cursor-based pagination.
    pub async fn list_workflow_runs_paginated(
        &self,
        limit: i64,
        cursor: Option<&str>,
    ) -> Result<(Vec<WorkflowRun>, Option<String>), StorageError> {
        self.storage.list_paginated(limit, cursor).await
    }
}
