use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::info;

use crate::connector::base::Connector;
use crate::schemas::workflow::{WorkflowStep, WorkflowStepResponse};

/// Configuration for the Webhook connector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebhookConfig {
    pub url: String,
    pub method: String,
    #[serde(default)]
    pub headers: HashMap<String, String>,
    #[serde(default)]
    pub body: serde_json::Value,
}

/// Output model for the Webhook connector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebhookResponse {
    pub status_code: u16,
    pub response_data: serde_json::Value,
    pub url: String,
    pub method: String,
}

/// Connector that makes HTTP requests.
pub struct WebhookConnector;

impl WebhookConnector {
    pub fn new() -> Self {
        Self
    }
}

impl Default for WebhookConnector {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl Connector for WebhookConnector {
    async fn execute(
        &self,
        step: &WorkflowStep,
        context: &HashMap<String, serde_json::Value>,
    ) -> Result<WorkflowStepResponse, Box<dyn std::error::Error + Send + Sync>> {
        match step {
            WorkflowStep::Webhook { config, .. } => {
                let url = &config.url;
                let method = config.method.to_uppercase();
                let headers = &config.headers;
                let body = Self::replace_placeholders(&config.body, context);

                info!("Making {} request to {}", method, url);

                let client = reqwest::Client::new();
                let mut request_builder = match method.as_str() {
                    "GET" => client.get(url),
                    "POST" => client.post(url).json(&body),
                    "PUT" => client.put(url).json(&body),
                    "DELETE" => client.delete(url),
                    _ => return Err(format!("Unsupported HTTP method: {}", method).into()),
                };

                for (key, value) in headers {
                    request_builder = request_builder.header(key.as_str(), value.as_str());
                }

                let response = request_builder.send().await?;
                let status_code = response.status().as_u16();
                let content_type = response
                    .headers()
                    .get("content-type")
                    .and_then(|v| v.to_str().ok())
                    .unwrap_or("")
                    .to_string();

                let response_data = if content_type.starts_with("application/json") {
                    response.json::<serde_json::Value>().await?
                } else {
                    serde_json::Value::String(response.text().await?)
                };

                Ok(WorkflowStepResponse::Webhook(WebhookResponse {
                    status_code,
                    response_data,
                    url: url.clone(),
                    method,
                }))
            }
            _ => Err("WebhookConnector received non-webhook step".into()),
        }
    }
}

impl WebhookConnector {
    /// Replace placeholders in data with context values.
    /// Supports ${key} syntax for simple string replacement.
    fn replace_placeholders(
        data: &serde_json::Value,
        context: &HashMap<String, serde_json::Value>,
    ) -> serde_json::Value {
        match data {
            serde_json::Value::Object(map) => {
                let mut new_map = serde_json::Map::new();
                for (k, v) in map {
                    new_map.insert(k.clone(), Self::replace_placeholders(v, context));
                }
                serde_json::Value::Object(new_map)
            }
            serde_json::Value::Array(arr) => {
                serde_json::Value::Array(
                    arr.iter()
                        .map(|item| Self::replace_placeholders(item, context))
                        .collect(),
                )
            }
            serde_json::Value::String(s) if s.starts_with("${") && s.ends_with('}') => {
                let key = &s[2..s.len() - 1];
                // Look up in context by key
                if let Some(val) = context.get(key) {
                    val.clone()
                } else {
                    data.clone()
                }
            }
            _ => data.clone(),
        }
    }
}
