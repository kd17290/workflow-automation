import uuid
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TypeVar

T = TypeVar("T")


from typing import Generic


class BaseStorage(ABC, Generic[T]):
    def __init__(self, t_type: type[T]):
        """
        Initialize the storage.

        Args:
            t_type (type[T]): The type of the item to store.
        """
        self.t_type = t_type

    @abstractmethod
    def get(self, uuid: str) -> T | None:
        """
        Retrieve an item by its UUID.

        Args:
            uuid (str): The UUID of the item.

        Returns:
            T | None: The item if found, else None.
        """
        ...

    @abstractmethod
    def create(self, item: T) -> str:
        """
        Create a new item and return its UUID.

        Args:
            item (T): The item to create.

        Returns:
            str: The UUID of the created item.
        """
        ...

    @abstractmethod
    def delete(self, uuid: str) -> bool:
        """
        Delete an item by its UUID.

        Args:
            uuid (str): The UUID of the item to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        ...

    @abstractmethod
    def update(self, item: T) -> bool:
        """
        Update an existing item.

        Args:
            item (T): The item to update.

        Returns:
            bool: True if updated, False if not found.
        """
        ...

    @abstractmethod
    def list_all(self) -> list[T]:
        """
        List all items in storage.

        Returns:
            list[T]: A list of all items.
        """
        ...

    def list_paginated(self, limit: int = 50, cursor: str | None = None) -> tuple[list[T], str | None]:
        """
        List items with cursor-based pagination.

        Args:
            limit: Maximum number of items to return.
            cursor: UUID cursor for pagination.

        Returns:
            tuple: (list of items, next_cursor or None).
        """
        # Default implementation falls back to list_all (for non-DB backends)
        items = self.list_all()
        return items[:limit], None

    def generate_uuid(self) -> str:
        """Generate a new UUID."""
        return uuid.uuid4().hex
