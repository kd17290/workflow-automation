use actix_web::{web, HttpResponse};
use serde_json::json;

use crate::api::deps::AppState;
use crate::schemas::workflow::WorkflowDefinition;

/// Create a new workflow definition.
///
/// POST /api/v1/workflows
/// Mirrors Python's create_workflow from app/api/v1/endpoints/workflows.py.
pub async fn create_workflow(
    state: web::Data<AppState>,
    body: web::Json<WorkflowDefinition>,
) -> HttpResponse {
    let mut workflow = body.into_inner();

    match state.workflow_service.create_workflow(&mut workflow).await {
        Ok(uuid) => {
            // Cache the newly created workflow (60s TTL)
            if let Ok(serialized) = serde_json::to_string(&workflow) {
                state.cache.set(&format!("workflow:{}", uuid), &serialized, 60).await;
            }
            HttpResponse::Ok().json(json!({
                "message": "Workflow created successfully",
                "workflow_id": uuid,
            }))
        }
        Err(e) => HttpResponse::InternalServerError().json(json!({
            "detail": format!("Failed to create workflow: {}", e),
        })),
    }
}

/// Get workflow definition by UUID.
///
/// GET /api/v1/workflows/{workflow_uuid}
/// Mirrors Python's get_workflow from app/api/v1/endpoints/workflows.py.
pub async fn get_workflow(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let workflow_uuid = path.into_inner();

    // Check cache first
    let cache_key = format!("workflow:{}", workflow_uuid);
    if let Some(cached) = state.cache.get(&cache_key).await {
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&cached) {
            return HttpResponse::Ok().json(val);
        }
    }

    match state.workflow_service.load_workflow(&workflow_uuid).await {
        Ok(Some(workflow)) => {
            // Cache for 60s (workflow definitions are mostly static)
            if let Ok(serialized) = serde_json::to_string(&workflow) {
                state.cache.set(&cache_key, &serialized, 60).await;
            }
            HttpResponse::Ok().json(workflow)
        }
        Ok(None) => HttpResponse::NotFound().json(json!({
            "detail": format!("Workflow {} not found", workflow_uuid),
        })),
        Err(e) => HttpResponse::InternalServerError().json(json!({
            "detail": format!("Error loading workflow: {}", e),
        })),
    }
}
