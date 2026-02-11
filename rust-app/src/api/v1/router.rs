use actix_web::web;

use crate::api::v1::endpoints::{runs, trigger, workflows};

/// Configure the v1 API routes.
///
/// Mirrors Python's api_router from app/api/v1/router.py.
/// All routes are prefixed with /api/v1 by the caller.
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/workflows")
            .route("", web::post().to(workflows::create_workflow))
            .route("/{workflow_uuid}", web::get().to(workflows::get_workflow)),
    )
    .service(
        web::scope("/runs")
            .route("", web::get().to(runs::list_runs))
            .route("/{run_id}", web::get().to(runs::get_run)),
    )
    .service(
        web::scope("/trigger")
            .route("", web::post().to(trigger::trigger_workflow)),
    );
}
