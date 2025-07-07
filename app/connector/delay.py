# Delay Connector
import asyncio
import logging
from typing import Any
from typing import Dict

from app.connector.base import BaseConnector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DelayConnector(BaseConnector):
    def __init__(self):
        super().__init__("delay")

    async def execute(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wait for specified duration"""
        duration = config.get("duration", 1)  # Default 1 second

        logger.info(f"Delaying for {duration} seconds")
        await asyncio.sleep(duration)

        return {"duration": duration, "message": f"Delayed for {duration} seconds"}
