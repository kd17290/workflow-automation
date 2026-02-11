use sqlx::FromRow;

/// Database model for WorkflowDefinition.
///
/// Mirrors Python's WorkflowDefinitionModel from app/db/models/workflow.py.
#[derive(Debug, Clone, FromRow)]
pub struct WorkflowDefinitionRow {
    pub uuid: String,
    pub id: Option<String>,
    pub name: String,
    pub description: Option<String>,
    pub steps: serde_json::Value,
}
