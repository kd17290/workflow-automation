use rdkafka::config::ClientConfig;
use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::message::OwnedHeaders;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::Message;
use std::collections::HashMap;
use std::time::Duration;
use tokio_stream::StreamExt;
use tracing::{error, info};

/// Async Kafka producer for publishing events.
///
/// Mirrors Python's KafkaProducer from app/messaging/kafka.py.
pub struct KafkaProducer {
    producer: FutureProducer,
}

impl KafkaProducer {
    /// Create a new Kafka producer.
    ///
    /// # Arguments
    /// * `bootstrap_servers` - Kafka broker addresses.
    pub fn new(bootstrap_servers: &str) -> Result<Self, rdkafka::error::KafkaError> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", bootstrap_servers)
            .set("message.timeout.ms", "5000")
            .create()?;

        info!("Kafka producer created: {}", bootstrap_servers);
        Ok(Self { producer })
    }

    /// Send a message to a Kafka topic.
    ///
    /// # Arguments
    /// * `topic` - The Kafka topic name.
    /// * `value` - The message payload (will be JSON serialized).
    /// * `key` - Optional message key for partitioning.
    pub async fn send(
        &self,
        topic: &str,
        value: &HashMap<String, serde_json::Value>,
        key: Option<&str>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let payload = serde_json::to_string(value)?;

        let mut record = FutureRecord::to(topic)
            .payload(&payload)
            .headers(OwnedHeaders::new());

        if let Some(k) = key {
            record = record.key(k);
        }

        self.producer
            .send(record, Duration::from_secs(5))
            .await
            .map_err(|(err, _)| {
                error!("Failed to send message to {}: {}", topic, err);
                Box::new(err) as Box<dyn std::error::Error + Send + Sync>
            })?;

        info!("Message sent to {}", topic);
        Ok(())
    }
}

/// Async Kafka consumer for processing events.
///
/// Mirrors Python's KafkaConsumer from app/messaging/kafka.py.
pub struct KafkaConsumer {
    consumer: StreamConsumer,
    topic: String,
}

impl KafkaConsumer {
    /// Create a new Kafka consumer.
    ///
    /// # Arguments
    /// * `topic` - The Kafka topic to subscribe to.
    /// * `group_id` - Consumer group ID.
    /// * `bootstrap_servers` - Kafka broker addresses.
    pub fn new(
        topic: &str,
        group_id: &str,
        bootstrap_servers: &str,
    ) -> Result<Self, rdkafka::error::KafkaError> {
        let consumer: StreamConsumer = ClientConfig::new()
            .set("bootstrap.servers", bootstrap_servers)
            .set("group.id", group_id)
            .set("auto.offset.reset", "earliest")
            .set("enable.auto.commit", "true")
            .create()?;

        consumer.subscribe(&[topic])?;

        info!(
            "Kafka consumer created: topic={}, group={}",
            topic, group_id
        );

        Ok(Self {
            consumer,
            topic: topic.to_string(),
        })
    }

    /// Start consuming messages and pass them to the handler.
    ///
    /// # Arguments
    /// * `handler` - Async function to process each message.
    pub async fn consume<F, Fut>(&self, handler: F) -> Result<(), Box<dyn std::error::Error>>
    where
        F: Fn(HashMap<String, serde_json::Value>) -> Fut,
        Fut: std::future::Future<Output = Result<(), Box<dyn std::error::Error + Send + Sync>>>,
    {
        info!("Starting to consume from {}...", self.topic);

        let mut stream = self.consumer.stream();
        while let Some(result) = stream.next().await {
            match result {
                Ok(message) => {
                    if let Some(payload) = message.payload() {
                        match serde_json::from_slice::<HashMap<String, serde_json::Value>>(payload)
                        {
                            Ok(value) => {
                                info!("Received message from {}: {:?}", self.topic, value);
                                if let Err(e) = handler(value).await {
                                    error!("Error processing message: {}", e);
                                }
                            }
                            Err(e) => {
                                error!("Failed to deserialize message: {}", e);
                            }
                        }
                    }
                }
                Err(e) => {
                    error!("Consumer error: {}", e);
                }
            }
        }

        Ok(())
    }
}
