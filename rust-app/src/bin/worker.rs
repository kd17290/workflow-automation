/// Kafka worker service for async workflow execution.
///
/// This binary runs as a standalone service that:
/// 1. Consumes workflow trigger events from Kafka
/// 2. Executes workflows asynchronously
/// 3. Publishes completion events back to Kafka
///
/// Mirrors Python's worker from app/worker/main.py.
use std::collections::HashMap;
use std::sync::Arc;
use tracing::{error, info};

use workflow_automation::core::config::Settings;
use workflow_automation::db::session::{create_pool, run_migrations};
use workflow_automation::messaging::events::{WorkflowCompletedEvent, WorkflowTriggerEvent};
use workflow_automation::messaging::kafka::{KafkaConsumer, KafkaProducer};
use workflow_automation::schemas::common::WorkflowStatus;
use workflow_automation::services::workflow::WorkflowService;
use workflow_automation::storage::db_storage::{WorkflowDefinitionStorage, WorkflowRunStorage};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
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
    info!("Starting workflow worker (Rust)...");

    // Create database pool
    let pool = create_pool(&settings)
        .await
        .expect("Failed to create database pool");

    // Run migrations
    run_migrations(&pool)
        .await
        .expect("Failed to run database migrations");

    // Create workflow service
    let workflow_storage = Arc::new(WorkflowDefinitionStorage::new(pool.clone()));
    let run_storage = Arc::new(WorkflowRunStorage::new(pool));
    let workflow_service = Arc::new(WorkflowService::new(workflow_storage, run_storage));

    // Create Kafka producer for completion events
    let producer = Arc::new(KafkaProducer::new(&settings.kafka_bootstrap_servers)?);

    // Create Kafka consumer
    let consumer = KafkaConsumer::new(
        &settings.kafka_topic_workflow_trigger,
        &settings.kafka_consumer_group,
        &settings.kafka_bootstrap_servers,
    )?;

    info!("Workflow worker started. Waiting for messages...");

    let topic_completed = settings.kafka_topic_workflow_completed.clone();

    // Start consuming messages
    consumer
        .consume(|message: HashMap<String, serde_json::Value>| {
            let service = workflow_service.clone();
            let producer = producer.clone();
            let topic = topic_completed.clone();

            async move {
                // Parse the trigger event
                let event: WorkflowTriggerEvent = serde_json::from_value(
                    serde_json::to_value(&message)?,
                )?;

                info!("Processing workflow trigger: run_id={}", event.run_id);

                // Execute the workflow
                service.execute_workflow(&event.run_id).await;

                // Get the final status
                let (status, error) = match service.load_workflow_run(&event.run_id).await {
                    Ok(Some(run)) => {
                        let status = run.status.to_string();
                        let error = if run.status == WorkflowStatus::Failed {
                            run.error
                        } else {
                            None
                        };
                        (status, error)
                    }
                    _ => ("failed".to_string(), Some("Run not found".to_string())),
                };

                // Publish completion event
                let completed_event = WorkflowCompletedEvent {
                    run_id: event.run_id.clone(),
                    workflow_id: event.workflow_id,
                    status: status.clone(),
                    error,
                };

                let mut event_map: HashMap<String, serde_json::Value> = HashMap::new();
                event_map.insert(
                    "run_id".to_string(),
                    serde_json::Value::String(completed_event.run_id.clone()),
                );
                event_map.insert(
                    "workflow_id".to_string(),
                    serde_json::Value::String(completed_event.workflow_id),
                );
                event_map.insert(
                    "status".to_string(),
                    serde_json::Value::String(completed_event.status),
                );
                if let Some(ref err) = completed_event.error {
                    event_map.insert(
                        "error".to_string(),
                        serde_json::Value::String(err.clone()),
                    );
                }

                producer
                    .send(&topic, &event_map, Some(&event.run_id))
                    .await?;

                info!(
                    "Workflow completed: run_id={}, status={}",
                    event.run_id, status
                );

                Ok(())
            }
        })
        .await?;

    Ok(())
}
