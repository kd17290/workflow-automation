from abc import ABC
from abc import abstractmethod
from typing import Any

from app.connector.enum import ConnectorType


class BaseConnector(ABC):
    def __init__(self, type: ConnectorType):
        self.type: ConnectorType = type

    @abstractmethod
    async def execute(self, config: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the connector logic"""
        ...
