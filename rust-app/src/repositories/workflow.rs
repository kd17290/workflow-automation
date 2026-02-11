use std::sync::Arc;

use crate::schemas::workflow::WorkflowDefinition;
use crate::storage::base::{Storage, StorageError};

/// Repository for managing WorkflowDefinition entities.
///
/// Mirrors Python's WorkflowRepository from app/repositories/workflow.py.
/// Follows Single Responsibility Principle — only orchestrates storage calls
/// for WorkflowDefinition.
pub struct WorkflowRepository {
    storage: Arc<dyn Storage<WorkflowDefinition>>,
}

impl WorkflowRepository {
    /// Initialize the repository with a storage backend.
    pub fn new(storage: Arc<dyn Storage<WorkflowDefinition>>) -> Self {
        Self { storage }
    }

    /// Retrieve a workflow definition by its UUID.
    pub async fn get_workflow(&self, uuid: &str) -> Result<Option<WorkflowDefinition>, StorageError> {
        self.storage.get(uuid).await
    }

    /// Create a new workflow definition.
    pub async fn create_workflow(&self, workflow: &mut WorkflowDefinition) -> Result<String, StorageError> {
        self.storage.create(workflow).await
    }

    /// Delete a workflow definition by its UUID.
    pub async fn delete_workflow(&self, uuid: &str) -> Result<bool, StorageError> {
        self.storage.delete(uuid).await
    }

    /// Update an existing workflow definition.
    pub async fn update_workflow(&self, workflow: &WorkflowDefinition) -> Result<bool, StorageError> {
        self.storage.update(workflow).await
    }

    /// List all workflow definitions.
    pub async fn list_workflows(&self) -> Result<Vec<WorkflowDefinition>, StorageError> {
        self.storage.list_all().await
    }
}
