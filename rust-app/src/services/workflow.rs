use std::collections::HashMap;
use std::sync::Arc;
use tracing::{error, info};

use crate::connector::factory::ConnectorFactory;
use crate::repositories::run::WorkflowRunRepository;
use crate::repositories::workflow::WorkflowRepository;
use crate::schemas::common::{StepStatus, WorkflowStatus};
use crate::schemas::run::WorkflowRun;
use crate::schemas::workflow::{StepResult, WorkflowDefinition};
use crate::storage::base::Storage;

/// Service layer for workflow operations.
///
/// Mirrors Python's WorkflowService from app/services/workflow.py.
/// Follows Single Responsibility: orchestrates workflow CRUD and execution
/// by delegating to repositories and connectors.
/// Follows Dependency Inversion: depends on Storage trait abstractions, not concrete types.
pub struct WorkflowService {
    workflow_repository: WorkflowRepository,
    workflow_run_repository: WorkflowRunRepository,
}

impl WorkflowService {
    /// Initialize the WorkflowService with storage backends.
    ///
    /// # Arguments
    /// * `workflow_storage` - Storage backend for workflow definitions.
    /// * `run_storage` - Storage backend for workflow runs.
    pub fn new(
        workflow_storage: Arc<dyn Storage<WorkflowDefinition>>,
        run_storage: Arc<dyn Storage<WorkflowRun>>,
    ) -> Self {
        Self {
            workflow_repository: WorkflowRepository::new(workflow_storage),
            workflow_run_repository: WorkflowRunRepository::new(run_storage),
        }
    }

    /// Create a new workflow definition.
    pub async fn create_workflow(
        &self,
        workflow: &mut WorkflowDefinition,
    ) -> Result<String, crate::storage::base::StorageError> {
        self.workflow_repository.create_workflow(workflow).await
    }

    /// Load a workflow definition by its UUID.
    pub async fn load_workflow(
        &self,
        uuid: &str,
    ) -> Result<Option<WorkflowDefinition>, crate::storage::base::StorageError> {
        self.workflow_repository.get_workflow(uuid).await
    }

    /// Create a new workflow run.
    pub async fn create_workflow_run(
        &self,
        run: &mut WorkflowRun,
    ) -> Result<String, crate::storage::base::StorageError> {
        self.workflow_run_repository.create_workflow_run(run).await
    }

    /// Load a workflow run by its UUID.
    pub async fn load_workflow_run(
        &self,
        uuid: &str,
    ) -> Result<Option<WorkflowRun>, crate::storage::base::StorageError> {
        self.workflow_run_repository.get_workflow_run(uuid).await
    }

    /// List all workflow runs.
    pub async fn list_runs(
        &self,
    ) -> Result<Vec<WorkflowRun>, crate::storage::base::StorageError> {
        self.workflow_run_repository.list_workflow_runs().await
    }

    /// List workflow runs with cursor-based pagination.
    pub async fn list_runs_paginated(
        &self,
        limit: i64,
        cursor: Option<&str>,
    ) -> Result<(Vec<WorkflowRun>, Option<String>), crate::storage::base::StorageError> {
        self.workflow_run_repository
            .list_workflow_runs_paginated(limit, cursor)
            .await
    }

    /// Update a workflow run.
    pub async fn update_workflow_run(
        &self,
        run: &WorkflowRun,
    ) -> Result<bool, crate::storage::base::StorageError> {
        self.workflow_run_repository.update_workflow_run(run).await
    }

    /// Execute a workflow run.
    ///
    /// This method:
    /// 1. Loads the run and workflow definition.
    /// 2. Updates status to RUNNING.
    /// 3. Iterates through steps sequentially, passing context.
    /// 4. Updates final status to SUCCESS or FAILED.
    pub async fn execute_workflow(&self, run_id: &str) {
        let run = match self.load_workflow_run(run_id).await {
            Ok(Some(r)) => r,
            Ok(None) => {
                error!("Workflow run {} not found", run_id);
                return;
            }
            Err(e) => {
                error!("Error loading workflow run {}: {}", run_id, e);
                return;
            }
        };

        let workflow = match self.load_workflow(&run.workflow_id).await {
            Ok(Some(w)) => w,
            Ok(None) => {
                error!("Workflow {} not found", run.workflow_id);
                let mut failed_run = run;
                failed_run.status = WorkflowStatus::Failed;
                failed_run.error = Some(format!("Workflow {} not found", failed_run.workflow_id));
                let _ = self.update_workflow_run(&failed_run).await;
                return;
            }
            Err(e) => {
                error!("Error loading workflow {}: {}", run.workflow_id, e);
                return;
            }
        };

        info!("Executing workflow run {}", run_id);
        let mut run = run;
        run.status = WorkflowStatus::Running;
        let _ = self.update_workflow_run(&run).await;

        let mut context: HashMap<String, serde_json::Value> = HashMap::new();
        context.insert(
            "payload".to_string(),
            serde_json::to_value(&run.payload).unwrap_or_default(),
        );

        for step in &workflow.steps {
            let step_result = self.execute_step(step, &context).await;

            if step_result.status == StepStatus::Failed {
                run.status = WorkflowStatus::Failed;
                run.error = step_result.error.clone();
                run.completed_at = Some(chrono::Utc::now().to_rfc3339());
                run.step_results
                    .insert(step.name().to_string(), step_result);
                let _ = self.update_workflow_run(&run).await;
                return;
            }

            // Add step output to context for next steps
            if let Some(ref output) = step_result.output {
                if let Ok(val) = serde_json::to_value(output) {
                    context.insert(step.name().to_string(), val);
                }
            }

            run.step_results
                .insert(step.name().to_string(), step_result);
        }

        // All steps completed successfully
        run.status = WorkflowStatus::Success;
        run.completed_at = Some(chrono::Utc::now().to_rfc3339());
        let _ = self.update_workflow_run(&run).await;
        info!("Workflow run {} completed successfully", run_id);
    }

    /// Execute a single workflow step.
    async fn execute_step(
        &self,
        step: &crate::schemas::workflow::WorkflowStep,
        context: &HashMap<String, serde_json::Value>,
    ) -> StepResult {
        let mut result = StepResult {
            step_name: step.name().to_string(),
            status: StepStatus::Running,
            started_at: chrono::Utc::now().to_rfc3339(),
            completed_at: None,
            output: None,
            error: None,
        };

        let connector_type = step.connector_type();
        match ConnectorFactory::get_instance(&connector_type) {
            Ok(connector) => {
                info!("Executing step: {} ({:?})", step.name(), connector_type);
                match connector.execute(step, context).await {
                    Ok(output) => {
                        result.output = Some(output);
                        result.status = StepStatus::Success;
                        result.completed_at = Some(chrono::Utc::now().to_rfc3339());
                    }
                    Err(e) => {
                        error!("Step {} failed: {}", step.name(), e);
                        result.status = StepStatus::Failed;
                        result.error = Some(e.to_string());
                        result.completed_at = Some(chrono::Utc::now().to_rfc3339());
                    }
                }
            }
            Err(e) => {
                error!("Failed to get connector for step {}: {}", step.name(), e);
                result.status = StepStatus::Failed;
                result.error = Some(e);
                result.completed_at = Some(chrono::Utc::now().to_rfc3339());
            }
        }

        result
    }
}
