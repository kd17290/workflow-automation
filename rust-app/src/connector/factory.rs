use crate::connector::base::Connector;
use crate::connector::delay::DelayConnector;
use crate::connector::webhook::WebhookConnector;
use crate::schemas::workflow::ConnectorType;

/// Factory for creating connector instances based on type (Factory Pattern).
///
/// Mirrors Python's ConnectorFactory. Uses Open/Closed principle —
/// new connector types can be added without modifying existing code.
pub struct ConnectorFactory;

impl ConnectorFactory {
    /// Get a connector instance for the given type.
    ///
    /// # Arguments
    /// * `connector_type` - The type of connector to create.
    ///
    /// # Returns
    /// A boxed trait object implementing Connector.
    ///
    /// # Errors
    /// Returns an error if the connector type is unknown.
    pub fn get_instance(
        connector_type: &ConnectorType,
    ) -> Result<Box<dyn Connector>, String> {
        match connector_type {
            ConnectorType::Delay => Ok(Box::new(DelayConnector::new())),
            ConnectorType::Webhook => Ok(Box::new(WebhookConnector::new())),
        }
    }
}
