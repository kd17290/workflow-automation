from typing import Any
from typing import Dict


class BaseConnector:
    def __init__(self, name: str):
        self.name = name

    async def execute(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the connector logic"""
        raise NotImplementedError
