from enum import StrEnum


class ConnectorType(StrEnum):
    """Enumeration of available connector types."""

    DELAY = "delay"
    WEBHOOK = "webhook"
