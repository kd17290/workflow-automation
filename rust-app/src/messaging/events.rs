use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Event published when a workflow is triggered.
/// Consumed by workers to execute the workflow.
///
/// Mirrors Python's WorkflowTriggerEvent from app/messaging/events.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowTriggerEvent {
    pub run_id: String,
    pub workflow_id: String,
    pub payload: HashMap<String, serde_json::Value>,
}

/// Event published when a workflow execution completes.
/// Can be used for notifications, callbacks, or chaining.
///
/// Mirrors Python's WorkflowCompletedEvent from app/messaging/events.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowCompletedEvent {
    pub run_id: String,
    pub workflow_id: String,
    pub status: String,
    #[serde(default)]
    pub error: Option<String>,
}
