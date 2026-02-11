use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::schemas::common::WorkflowStatus;
use crate::schemas::workflow::StepResult;

/// State of a workflow execution run.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowRun {
    #[serde(default)]
    pub uuid: Option<String>,
    #[serde(default)]
    pub id: Option<String>,
    pub workflow_id: String,
    pub status: WorkflowStatus,
    pub payload: HashMap<String, serde_json::Value>,
    pub started_at: String,
    #[serde(default)]
    pub completed_at: Option<String>,
    #[serde(default)]
    pub error: Option<String>,
    #[serde(default)]
    pub step_results: HashMap<String, StepResult>,
}
