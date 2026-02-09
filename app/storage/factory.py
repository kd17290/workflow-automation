from app.storage.db_storage import DBStorage
from app.storage.enum import StorageType
from app.storage.file_storage import FileStorage
from app.storage.in_memory import InMemoryStorage


class StorageFactory:
    """
    Factory class for creating storage instances.
    """

    @staticmethod
    def create_storage(storage_type: StorageType):
        if storage_type == StorageType.FILE_SYSTEM:
            return FileStorage
        elif storage_type == StorageType.IN_MEMORY:
            return InMemoryStorage
        elif storage_type == StorageType.POSTGRES:
            return DBStorage
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
