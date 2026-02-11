use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::connector::delay::{DelayConfig, DelayOutput};
use crate::connector::webhook::{WebhookConfig, WebhookResponse};
use crate::schemas::common::StepStatus;

/// Request model for triggering a workflow.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TriggerRequest {
    pub workflow_id: String,
    #[serde(default)]
    pub payload: HashMap<String, serde_json::Value>,
}

/// Enumeration of available connector types.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ConnectorType {
    Delay,
    Webhook,
}

impl std::fmt::Display for ConnectorType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Delay => write!(f, "delay"),
            Self::Webhook => write!(f, "webhook"),
        }
    }
}

/// A workflow step configuration — discriminated union by `type`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum WorkflowStep {
    Delay {
        name: String,
        config: DelayConfig,
    },
    Webhook {
        name: String,
        config: WebhookConfig,
    },
}

impl WorkflowStep {
    /// Get the name of this step.
    pub fn name(&self) -> &str {
        match self {
            Self::Delay { name, .. } => name,
            Self::Webhook { name, .. } => name,
        }
    }

    /// Get the connector type of this step.
    pub fn connector_type(&self) -> ConnectorType {
        match self {
            Self::Delay { .. } => ConnectorType::Delay,
            Self::Webhook { .. } => ConnectorType::Webhook,
        }
    }
}

/// Output from a workflow step — discriminated union by `type`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum WorkflowStepResponse {
    Delay(DelayOutput),
    Webhook(WebhookResponse),
}

/// Definition of a workflow.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowDefinition {
    #[serde(default)]
    pub uuid: Option<String>,
    #[serde(default)]
    pub id: Option<String>,
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    pub steps: Vec<WorkflowStep>,
}

/// Result of a single workflow step execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepResult {
    pub step_name: String,
    pub status: StepStatus,
    pub started_at: String,
    #[serde(default)]
    pub completed_at: Option<String>,
    #[serde(default)]
    pub output: Option<WorkflowStepResponse>,
    #[serde(default)]
    pub error: Option<String>,
}
