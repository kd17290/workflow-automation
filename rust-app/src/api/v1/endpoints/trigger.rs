use actix_web::{web, HttpResponse};
use serde_json::json;
use std::collections::HashMap;
use tracing::error;

use crate::api::deps::AppState;
use crate::core::config::Settings;
use crate::schemas::common::WorkflowStatus;
use crate::schemas::run::WorkflowRun;
use crate::schemas::workflow::TriggerRequest;

/// Trigger a workflow execution asynchronously via Kafka.
///
/// POST /api/v1/trigger
/// Mirrors Python's trigger_workflow from app/api/v1/endpoints/trigger.py.
///
/// This endpoint:
/// 1. Validates the workflow exists
/// 2. Creates a workflow run with PENDING status
/// 3. Publishes a trigger event to Kafka
/// 4. Returns immediately with the run ID
///
/// The actual execution happens in the worker service.
pub async fn trigger_workflow(
    state: web::Data<AppState>,
    body: web::Json<TriggerRequest>,
) -> HttpResponse {
    let request = body.into_inner();

    // Check if workflow exists
    let workflow = match state
        .workflow_service
        .load_workflow(&request.workflow_id)
        .await
    {
        Ok(Some(w)) => w,
        Ok(None) => {
            return HttpResponse::NotFound().json(json!({
                "detail": format!("Workflow {} not found", request.workflow_id),
            }));
        }
        Err(e) => {
            return HttpResponse::InternalServerError().json(json!({
                "detail": format!("Error loading workflow: {}", e),
            }));
        }
    };

    // Create workflow run with PENDING status
    let mut run = WorkflowRun {
        uuid: None,
        id: None,
        workflow_id: request.workflow_id.clone(),
        status: WorkflowStatus::Pending,
        payload: request.payload.clone(),
        started_at: chrono::Utc::now().to_rfc3339(),
        completed_at: None,
        error: None,
        step_results: HashMap::new(),
    };

    // Save run to database
    let run_uuid = match state.workflow_service.create_workflow_run(&mut run).await {
        Ok(uuid) => uuid,
        Err(e) => {
            return HttpResponse::InternalServerError().json(json!({
                "detail": format!("Failed to create workflow run: {}", e),
            }));
        }
    };

    // Publish trigger event to Kafka
    let settings = Settings::from_env();
    let mut event: HashMap<String, serde_json::Value> = HashMap::new();
    event.insert("run_id".to_string(), json!(run_uuid));
    event.insert("workflow_id".to_string(), json!(request.workflow_id));
    event.insert(
        "payload".to_string(),
        serde_json::to_value(&request.payload).unwrap_or_default(),
    );

    if let Err(e) = state
        .kafka_producer
        .send(
            &settings.kafka_topic_workflow_trigger,
            &event,
            Some(&run_uuid),
        )
        .await
    {
        error!("Failed to queue workflow: {}", e);
        // Update run status to FAILED
        let mut failed_run = run;
        failed_run.uuid = Some(run_uuid.clone());
        failed_run.status = WorkflowStatus::Failed;
        failed_run.error = Some(format!("Failed to queue workflow: {}", e));
        let _ = state.workflow_service.update_workflow_run(&failed_run).await;

        return HttpResponse::InternalServerError().json(json!({
            "detail": format!("Failed to queue workflow: {}", e),
        }));
    }

    HttpResponse::Ok().json(json!({
        "run_id": run_uuid,
        "status": "triggered",
    }))
}
