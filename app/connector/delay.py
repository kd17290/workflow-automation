# Delay Connector
import asyncio
import logging
from typing import Any
from typing import Literal

from pydantic import BaseModel

from .enum import ConnectorType
from app.connector.base import BaseConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DelayConfig(BaseModel):
    duration: int


class DelayWorkflowStep(BaseModel):
    type: Literal[ConnectorType.DELAY] = ConnectorType.DELAY
    name: str
    config: DelayConfig


class DelayOutput(BaseModel):
    type: Literal[ConnectorType.DELAY] = ConnectorType.DELAY
    duration: int
    message: str


class DelayConnector(BaseConnector):
    def __init__(self):
        super().__init__(ConnectorType.DELAY)

    async def execute(
        self, step: DelayWorkflowStep, context: dict[str, Any]
    ) -> DelayOutput:
        """Wait for specified duration"""
        assert step.type == ConnectorType.DELAY
        duration = step.config.duration  # Default 1 second

        logger.info(f"Delaying for {duration} seconds")
        await asyncio.sleep(duration)

        return DelayOutput(duration=duration, message=f"Delayed for {duration} seconds")
