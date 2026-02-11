use sqlx::FromRow;

/// Database model for WorkflowRun.
///
/// Mirrors Python's WorkflowRunModel from app/db/models/run.py.
#[derive(Debug, Clone, FromRow)]
pub struct WorkflowRunRow {
    pub uuid: String,
    pub id: Option<String>,
    pub workflow_id: String,
    pub status: String,
    pub payload: serde_json::Value,
    pub started_at: String,
    pub completed_at: Option<String>,
    pub error: Option<String>,
    pub step_results: serde_json::Value,
}
