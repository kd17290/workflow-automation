use actix_web::{web, App, HttpResponse, HttpServer};
use serde_json::json;
use sqlx::PgPool;
use std::sync::Arc;
use tracing::info;

use workflow_automation::api::deps::AppState;
use workflow_automation::api::v1::router;
use workflow_automation::core::config::Settings;
use workflow_automation::db::session::{create_pool, run_migrations};
use workflow_automation::repositories::health::save_health_status;

/// Root endpoint to verify API is running.
/// GET /
async fn root() -> HttpResponse {
    HttpResponse::Ok().json(json!({"message": "Hello World"}))
}

/// Health check endpoint.
/// GET /health
async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(json!({"status": "ok"}))
}

/// Background task to periodically save the health status to the database.
/// Runs every 10 seconds. Mirrors Python's health_status_task.
async fn health_status_task(pool: PgPool) {
    loop {
        info!("Health status task");
        if let Err(e) = save_health_status(&pool, "ok").await {
            tracing::error!("Failed to save health status: {}", e);
        }
        tokio::time::sleep(tokio::time::Duration::from_secs(10)).await;
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    // Load .env file if present
    let _ = dotenvy::dotenv();

    let settings = Settings::from_env();
    info!("Starting {} v{}", settings.project_name, settings.version);

    // Create database pool
    let pool = create_pool(&settings)
        .await
        .expect("Failed to create database pool");

    // Run migrations
    run_migrations(&pool)
        .await
        .expect("Failed to run database migrations");

    info!("Database migrations completed");

    // Start background health status task
    let health_pool = pool.clone();
    tokio::spawn(async move {
        health_status_task(health_pool).await;
    });

    // Create application state
    let app_state = web::Data::new(AppState::new(
        pool,
        &settings.kafka_bootstrap_servers,
        &settings.redis_url,
    ));

    info!("Starting HTTP server on 0.0.0.0:8002");

    HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .route("/", web::get().to(root))
            .route("/health", web::get().to(health_check))
            .service(
                web::scope("/api/v1").configure(router::configure),
            )
    })
    .bind("0.0.0.0:8002")?
    .run()
    .await
}
