from typing import Generic
from typing import TypeVar

from app.db.models.run import WorkflowRunModel
from app.db.models.workflow import WorkflowDefinitionModel
from app.db.session import SessionLocal
from app.schemas.run import WorkflowRun
from app.schemas.workflow import WorkflowDefinition
from app.storage.base import BaseStorage

T = TypeVar("T")

class DBStorage(BaseStorage[T]):
    def __init__(self, t_type: type[T]):
        """
        Initialize the DB storage.

        Args:
            t_type (type[T]): The type of the item to store.
        """
        super().__init__(t_type)
        if t_type == WorkflowDefinition:
            self.model = WorkflowDefinitionModel
        elif t_type == WorkflowRun:
            self.model = WorkflowRunModel
        else:
            raise ValueError(f"Unknown type: {t_type}")

    def get(self, uuid: str) -> T | None:
        """
        Retrieve an item by its UUID.

        Args:
            uuid (str): The UUID of the item.

        Returns:
            T | None: The item if found, else None.
        """
        try:
            db = SessionLocal()
            item = db.query(self.model).filter(self.model.uuid == uuid).first()
            if not item:
                return None
            return self.t_type.model_validate(item, from_attributes=True)
        finally:
            db.close()

    def create(self, item: T) -> str:
        """
        Create a new item and return its UUID.

        Args:
            item (T): The item to create.

        Returns:
            str: The UUID of the created item.
        """
        item.uuid = self.generate_uuid()
        try:
            db = SessionLocal()
            db_item = self.model(**item.model_dump())
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            return item.uuid
        except Exception as e:
            print(f"Error creating item: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

    def delete(self, uuid: str) -> bool:
        """
        Delete an item by its UUID.

        Args:
            uuid (str): The UUID of the item to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        try:
            db = SessionLocal()
            item = db.query(self.model).filter(self.model.uuid == uuid).first()
            if not item:
                return False
            db.delete(item)
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting item {uuid}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def update(self, item: T) -> bool:
        """
        Update an existing item.

        Args:
            item (T): The item to update.

        Returns:
            bool: True if updated, False if not found.
        """
        try:
            db = SessionLocal()
            db_item = db.query(self.model).filter(self.model.uuid == item.uuid).first()
            if not db_item:
                return False
            for key, value in item.model_dump().items():
                setattr(db_item, key, value)
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating item {item.uuid}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def list_all(self) -> list[T]:
        """
        List all items in storage.

        Returns:
            list[T]: A list of all items.
        """
        try:
            db = SessionLocal()
            items = db.query(self.model).all()
            return [self.t_type.model_validate(item, from_attributes=True) for item in items]
        finally:
            db.close()

    def list_paginated(self, limit: int = 50, cursor: str | None = None) -> tuple[list[T], str | None]:
        """
        List items with cursor-based pagination, ordered by uuid.

        Args:
            limit: Maximum number of items to return.
            cursor: UUID cursor — return items with uuid > cursor.

        Returns:
            tuple: (list of items, next_cursor or None if no more items).
        """
        try:
            db = SessionLocal()
            query = db.query(self.model).order_by(self.model.uuid)
            if cursor:
                query = query.filter(self.model.uuid > cursor)
            items = query.limit(limit + 1).all()

            has_more = len(items) > limit
            items = items[:limit]
            next_cursor = items[-1].uuid if has_more and items else None

            return (
                [self.t_type.model_validate(item, from_attributes=True) for item in items],
                next_cursor,
            )
        finally:
            db.close()
