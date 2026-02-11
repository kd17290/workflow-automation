use async_trait::async_trait;
use std::collections::HashMap;

use crate::schemas::workflow::{WorkflowStep, WorkflowStepResponse};

/// Base trait for all workflow connectors (Interface Segregation & Dependency Inversion).
///
/// Each connector implements this trait to provide step execution logic.
/// Mirrors Python's BaseConnector ABC.
#[async_trait]
pub trait Connector: Send + Sync {
    /// Execute the connector logic for a given workflow step.
    ///
    /// # Arguments
    /// * `step` - The workflow step configuration.
    /// * `context` - The execution context containing payload and previous step outputs.
    ///
    /// # Returns
    /// The step output on success, or an error.
    async fn execute(
        &self,
        step: &WorkflowStep,
        context: &HashMap<String, serde_json::Value>,
    ) -> Result<WorkflowStepResponse, Box<dyn std::error::Error + Send + Sync>>;
}
