import uuid
from typing import Generic
from typing import TypeVar

from app.storage.base import BaseStorage

T = TypeVar("T")


class InMemoryStorage(BaseStorage[T]):
    def __init__(self, t_type: type[T]):
        """
        Initialize the in-memory storage.

        Args:
            t_type (type[T]): The type of the item to store.
        """
        super().__init__(t_type)
        self.storage: dict[str, T] = {}

    def get(self, uuid: str) -> T | None:
        """
        Retrieve an item by its UUID.

        Args:
            uuid (str): The UUID of the item.

        Returns:
            T | None: The item if found, else None.
        """
        item = self.storage.get(uuid)
        return item

    def create(self, item: T) -> str:
        """
        Create a new item and return its UUID.

        Args:
            item (T): The item to create.

        Returns:
            str: The UUID of the created item.
        """
        # create a uuid
        item.uuid = uuid.uuid4().hex
        self.storage[item.uuid] = item
        return item.uuid

    def delete(self, uuid: str) -> bool:
        """
        Delete an item by its UUID.

        Args:
            uuid (str): The UUID of the item to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        if uuid in self.storage:
            del self.storage[uuid]
            return True
        return False

    def update(self, item: T) -> bool:
        """
        Update an existing item.

        Args:
            item (T): The item to update.

        Returns:
            bool: True if updated, False if not found.
        """
        if item.uuid in self.storage:
            self.storage[item.uuid] = item
            return True
        return False

    def list_all(self) -> list[T]:
        """
        List all items in storage.

        Returns:
            list[T]: A list of all items.
        """
        return list(self.storage.values())
