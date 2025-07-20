from app.models import WorkflowRun
from app.storage.base import BaseStorage


class WorkflowRunRepository:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def get_workflow_run(self, uuid: str) -> WorkflowRun:
        """Retrieve a workflow by its UUID."""
        data = self.storage.get(uuid)
        return data

    def create_workflow_run(self, workflow_run: WorkflowRun) -> str:
        """Create a new workflow and return its UUID."""
        return self.storage.create(workflow_run)

    def delete_workflow_run(self, uuid: str) -> bool:
        """Delete a workflow by its UUID."""
        return self.storage.delete(uuid)

    def update_workflow_run(self, workflow_run: WorkflowRun) -> bool:
        """Update a workflow runs by its UUID."""
        return self.storage.update(workflow_run)

    def list_workflow_runs(self) -> list[WorkflowRun]:
        """List all workflow runs."""
        # Assuming the storage has a method to list all items
        return self.storage.list_all()
