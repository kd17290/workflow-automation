from app.schemas.run import WorkflowRun
from app.storage.base import BaseStorage


class WorkflowRunRepository:
    """
    Repository for managing WorkflowRun entities.
    """

    def __init__(self, storage: BaseStorage[WorkflowRun]):
        """
        Initialize the repository.

        Args:
            storage (BaseStorage[WorkflowRun]): The storage backend.
        """
        self.storage = storage

    def get_workflow_run(self, uuid: str) -> WorkflowRun:
        """
        Retrieve a workflow run by its UUID.

        Args:
            uuid (str): The UUID of the workflow run.

        Returns:
            WorkflowRun: The workflow run object, or None if not found.
        """
        data = self.storage.get(uuid)
        return data

    def create_workflow_run(self, workflow_run: WorkflowRun) -> str:
        """
        Create a new workflow run.

        Args:
            workflow_run (WorkflowRun): The workflow run to create.

        Returns:
            str: The UUID of the created workflow run.
        """
        return self.storage.create(workflow_run)

    def delete_workflow_run(self, uuid: str) -> bool:
        """
        Delete a workflow run by its UUID.

        Args:
            uuid (str): The UUID of the workflow run to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        return self.storage.delete(uuid)

    def update_workflow_run(self, workflow_run: WorkflowRun) -> bool:
        """
        Update an existing workflow run.

        Args:
            workflow_run (WorkflowRun): The updated workflow run.

        Returns:
            bool: True if updated, False if not found.
        """
        return self.storage.update(workflow_run)

    def list_workflow_runs(self) -> list[WorkflowRun]:
        """
        List all workflow runs.

        Returns:
            list[WorkflowRun]: A list of all workflow runs.
        """
        # Assuming the storage has a method to list all items
        return self.storage.list_all()
