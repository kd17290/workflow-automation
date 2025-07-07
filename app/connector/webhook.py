import logging
from typing import Any
from typing import Dict

import httpx

from app.connector.base import BaseConnector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookConnector(BaseConnector):
    def __init__(self):
        super().__init__("webhook")

    async def execute(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP request to webhook URL"""
        url = config.get("url")
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        body = config.get("body", {})

        if not url:
            raise ValueError("Webhook URL is required")

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

        return {
            "status_code": response.status_code,
            "response_data": response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else response.text,
            "url": url,
            "method": method,
        }

    def _replace_placeholders(self, data: Any, context: Dict[str, Any]) -> Any:
        """Replace placeholders in data with context values"""
        if isinstance(data, dict):
            return {k: self._replace_placeholders(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_placeholders(item, context) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            # Simple placeholder replacement: ${key} -> context[key]
            key = data[2:-1]
            return context.get(key, data)
        return data
