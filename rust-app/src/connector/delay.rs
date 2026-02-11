use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::info;

use crate::connector::base::Connector;
use crate::schemas::workflow::{WorkflowStep, WorkflowStepResponse};

/// Configuration for the Delay connector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelayConfig {
    pub duration: u64,
}

/// Output model for the Delay connector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelayOutput {
    pub duration: u64,
    pub message: String,
}

/// Connector that waits for a specified duration.
pub struct DelayConnector;

impl DelayConnector {
    pub fn new() -> Self {
        Self
    }
}

impl Default for DelayConnector {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl Connector for DelayConnector {
    async fn execute(
        &self,
        step: &WorkflowStep,
        _context: &HashMap<String, serde_json::Value>,
    ) -> Result<WorkflowStepResponse, Box<dyn std::error::Error + Send + Sync>> {
        match step {
            WorkflowStep::Delay { config, .. } => {
                let duration = config.duration;
                info!("Delaying for {} seconds", duration);
                tokio::time::sleep(tokio::time::Duration::from_secs(duration)).await;

                Ok(WorkflowStepResponse::Delay(DelayOutput {
                    duration,
                    message: format!("Delayed for {} seconds", duration),
                }))
            }
            _ => Err("DelayConnector received non-delay step".into()),
        }
    }
}
