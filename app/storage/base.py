import uuid
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TypeVar

T = TypeVar("T")


class BaseStorage(ABC):
    def __init__(self, t_type: type[T]):
        self.t_type = t_type

    @abstractmethod
    def get(self, uuid: str) -> T | None:
        """Retrieve an item by its UUID."""
        ...

    @abstractmethod
    def create(self, item) -> str:
        """Create a new item and return its UUID."""
        ...

    @abstractmethod
    def delete(self, uuid: str) -> bool:
        """Delete an item by its UUID."""
        ...

    @abstractmethod
    def update(self, item: T) -> bool:
        """Update an item by its UUID."""
        ...

    @abstractmethod
    def list_all(self) -> list[Any]:
        """List all items."""
        ...

    def generate_uuid(self) -> str:
        """Generate a new UUID."""
        return uuid.uuid4().hex
