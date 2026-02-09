from app.schemas.workflow import WorkflowDefinition
from app.storage.base import BaseStorage


class WorkflowRepository:
    """
    Repository for managing WorkflowDefinition entities.
    """

    def __init__(self, storage: BaseStorage[WorkflowDefinition]):
        """
        Initialize the repository.

        Args:
            storage (BaseStorage[WorkflowDefinition]): The storage backend.
        """
        self.storage = storage

    def get_workflow(self, uuid: str) -> WorkflowDefinition:
        """
        Retrieve a workflow definition by its UUID.

        Args:
            uuid (str): The UUID of the workflow.

        Returns:
            WorkflowDefinition: The workflow definition, or None if not found.
        """
        data = self.storage.get(uuid)
        return data

    def create_workflow(self, workflow: WorkflowDefinition) -> str:
        """
        Create a new workflow definition.

        Args:
            workflow (WorkflowDefinition): The workflow definition to create.

        Returns:
            str: The UUID of the created workflow.
        """
        return self.storage.create(workflow)

    def delete_workflow(self, uuid: str) -> bool:
        """
        Delete a workflow definition by its UUID.

        Args:
            uuid (str): The UUID of the workflow to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        return self.storage.delete(uuid)

    def update_workflow(self, workflow: WorkflowDefinition) -> bool:
        """
        Update an existing workflow definition.

        Args:
            workflow (WorkflowDefinition): The updated workflow definition.

        Returns:
            bool: True if updated, False if not found.
        """
        return self.storage.update(workflow)

    def list_workflows(self) -> list[WorkflowDefinition]:
        """
        List all workflow definitions.

        Returns:
            list[WorkflowDefinition]: A list of all workflow definitions.
        """
        return self.storage.list_all()
