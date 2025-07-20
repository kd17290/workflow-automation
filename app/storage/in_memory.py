import uuid
from typing import Generic
from typing import TypeVar

from app.storage.base import BaseStorage

T = TypeVar("T")


class InMemoryStorage(Generic[T], BaseStorage):
    def __init__(self, t_type: type[T]):
        super().__init__(t_type)
        self.storage: dict[str, T] = {}

    def get(self, uuid: str) -> T | None:
        """Retrieve an item by its UUID."""
        item = self.storage.get(uuid)
        return item

    def create(self, item: T) -> str:
        """Create a new item and return its UUID."""
        # create a uuid
        item.uuid = uuid.uuid4().hex
        self.storage[item.uuid] = item
        return item.uuid

    def delete(self, uuid: str) -> bool:
        """Delete an item by its UUID."""
        if uuid in self.storage:
            del self.storage[uuid]
            return True
        return False

    def update(self, item: T) -> bool:
        """Update an item by its UUID."""
        if item.uuid in self.storage:
            self.storage[item.uuid] = item
            return True
        return False

    def list_all(self) -> list[T]:
        """List all items."""
        return list(self.storage.values())
