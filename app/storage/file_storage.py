import json
import os
import uuid
from pathlib import Path
from typing import Generic
from typing import TypeVar

from app.storage.base import BaseStorage

T = TypeVar("T")


class FileStorage(Generic[T], BaseStorage):
    def __init__(self, t_type: type[T]):
        super().__init__(t_type)
        base_path = "data"
        self.base_path = Path(base_path) / f"{t_type.__name__.lower()}s"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get(self, uuid: str) -> T | None:
        """Retrieve an item by its UUID."""
        try:
            file_path = self.base_path / f"{uuid}.json"
            if not file_path.exists():
                return None
            with open(file_path, "r") as file:
                data = json.load(file)
            return self.t_type(**data)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error retrieving item {uuid}: {e}")
            return None

    def create(self, item: T) -> str:
        """Create a new item and return its UUID."""
        item.uuid = uuid.uuid4().hex
        try:
            file_path = self.base_path / f"{item.uuid}.json"
            print(f"Saving workflow to {file_path=}")
            with open(file_path, "w") as file:
                json.dump(item.model_dump(), file, indent=2)
            return item.uuid
        except Exception as e:
            print(f"Error creating item: {e}")
            return ""

    def delete(self, uuid: str) -> bool:
        """Delete an item by its UUID."""
        try:
            file_path = self.base_path / f"{uuid}.json"
            if not self.get(uuid):
                return False
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting item {uuid}: {e}")
            return False

    def update(self, item: T) -> bool:
        """Update an item by its UUID."""
        try:
            if not self.get(item.uuid):
                return False
            file_path = self.base_path / f"{item.uuid}.json"
            with open(file_path, "w") as file:
                json.dump(item.model_dump(), file)
            return True
        except Exception as e:
            print(f"Error updating item {item.uuid}: {e}")
            return False

    def list_all(self) -> list[T]:
        """List all items."""
        try:
            # Read all JSON files in the directory
            return [
                self.get(file.stem)
                for file in self.base_path.glob("*.json")
                if file.is_file()
            ]

        except Exception as e:
            print(f"Error listing items: {e}")
            return []
