from app.connector.delay import DelayConnector
from app.connector.enum import ConnectorType
from app.connector.webhook import WebhookConnector

CONNECTORS = [DelayConnector(), WebhookConnector()]


class ConnectorFactory:
    """
    Factory class to create instances of different connectors based on the type.
    """

    @staticmethod
    def get_instance(connector_type: ConnectorType):
        """
        Create an instance of the specified connector type.
        :param connector_type: The type of connector to create.
        :return: An instance of the specified connector.
        """
        for connector in CONNECTORS:
            if connector.type == connector_type:
                return connector
        raise ValueError(f"Unknown connector type: {connector_type}")
