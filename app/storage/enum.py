from enum import Enum


class StorageType(str, Enum):
    """
    Enum for different storage types.
    """

    FILE_SYSTEM = "file_system"
    IN_MEMORY = "in_memory"
    # Add more storage types as needed
