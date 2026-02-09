import logging
from typing import Any
from typing import Literal

import httpx
from pydantic import BaseModel

from .enum import ConnectorType
from app.connector.base import BaseConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookConfig(BaseModel):
    """Configuration for Webhook connector."""

    url: str
    method: str
    headers: dict[str, str] = {}
    body: dict[str, Any] = {}


class WebhookWorkflowStep(BaseModel):
    """Definition of a Webhook step in a workflow."""

    type: Literal[ConnectorType.WEBHOOK] = ConnectorType.WEBHOOK
    name: str
    config: WebhookConfig


class WebhookResponse(BaseModel):
    """Output model for Webhook connector."""

    type: Literal[ConnectorType.WEBHOOK] = ConnectorType.WEBHOOK
    status_code: int
    response_data: Any
    url: str
    method: str


class WebhookConnector(BaseConnector):
    """Connector that makes HTTP requests."""

    def __init__(self):
        super().__init__(ConnectorType.WEBHOOK)

    async def execute(
        self, step: WebhookWorkflowStep, context: dict[str, Any]
    ) -> WebhookResponse:
        """
        Make HTTP request to webhook URL.

        Args:
            step (WebhookWorkflowStep): The step configuration.
            context (dict[str, Any]): The execution context.

        Returns:
            WebhookResponse: The response from the webhook.

        Raises:
            ValueError: If an unsupported HTTP method is used.
        """
        url = step.config.url
        method = step.config.method.upper()
        headers = step.config.headers
        body = step.config.body

        # Replace placeholders in body with context data
        if isinstance(body, dict):
            body = self._replace_placeholders(body, context)

        logger.info(f"Making {method} request to {url}")

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=body, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=body, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        response_data = (
            response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else response.text
        )
        return WebhookResponse(
            status_code=response.status_code,
            response_data=response_data,
            url=url,
            method=method,
        )

    def _replace_placeholders(self, data: Any, context: dict[str, Any]) -> Any:
        """
        Replace placeholders in data with context values.
        Supports dictionary, list, and string replacement (e.g., "${key}").

        Args:
            data (Any): The data containing placeholders.
            context (dict[str, Any]): The context values.

        Returns:
            Any: The data with placeholders replaced.
        """
        if isinstance(data, dict):
            return {k: self._replace_placeholders(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_placeholders(item, context) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            # Simple placeholder replacement: ${key} -> context[key]
            key = data[2:-1]
            return context.get(key, data)
        return data
