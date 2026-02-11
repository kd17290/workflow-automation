use actix_web::{web, HttpResponse};
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::api::deps::AppState;

/// Query parameters for paginated list endpoints.
#[derive(Debug, Deserialize)]
pub struct PaginationParams {
    pub limit: Option<i64>,
    pub cursor: Option<String>,
}

/// Paginated response wrapper.
#[derive(Debug, Serialize)]
pub struct PaginatedResponse<T: Serialize> {
    pub items: Vec<T>,
    pub next_cursor: Option<String>,
    pub limit: i64,
}

/// Get workflow run details by run_id.
///
/// GET /api/v1/runs/{run_id}
/// Mirrors Python's get_run from app/api/v1/endpoints/runs.py.
pub async fn get_run(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let run_id = path.into_inner();

    // Check cache first
    let cache_key = format!("run:{}", run_id);
    if let Some(cached) = state.cache.get(&cache_key).await {
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&cached) {
            return HttpResponse::Ok().json(val);
        }
    }

    match state.workflow_service.load_workflow_run(&run_id).await {
        Ok(Some(run)) => {
            // Cache for 10s (runs change status so short TTL)
            if let Ok(serialized) = serde_json::to_string(&run) {
                state.cache.set(&cache_key, &serialized, 10).await;
            }
            HttpResponse::Ok().json(run)
        }
        Ok(None) => HttpResponse::NotFound().json(json!({
            "detail": "Workflow run not found",
        })),
        Err(e) => HttpResponse::InternalServerError().json(json!({
            "detail": format!("Error loading run: {}", e),
        })),
    }
}

/// List workflow runs with cursor-based pagination.
///
/// GET /api/v1/runs?limit=50&cursor=<uuid>
/// Mirrors Python's list_runs from app/api/v1/endpoints/runs.py.
pub async fn list_runs(
    state: web::Data<AppState>,
    query: web::Query<PaginationParams>,
) -> HttpResponse {
    let limit = query.limit.unwrap_or(50).min(200).max(1);
    let cursor = query.cursor.as_deref();

    match state.workflow_service.list_runs_paginated(limit, cursor).await {
        Ok((runs, next_cursor)) => {
            HttpResponse::Ok().json(PaginatedResponse {
                items: runs,
                next_cursor,
                limit,
            })
        }
        Err(e) => HttpResponse::InternalServerError().json(json!({
            "detail": format!("Error listing runs: {}", e),
        })),
    }
}
