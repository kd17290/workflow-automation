from app.models import WorkflowDefinition
from app.storage.base import BaseStorage


class WorkflowRepository:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def get_workflow(self, uuid: str) -> WorkflowDefinition:
        """Retrieve a workflow by its UUID."""
        data = self.storage.get(uuid)
        return data

    def create_workflow(self, workflow: WorkflowDefinition) -> str:
        """Create a new workflow and return its UUID."""
        return self.storage.create(workflow)

    def delete_workflow(self, uuid: str) -> bool:
        """Delete a workflow by its UUID."""
        return self.storage.delete(uuid)

    def update_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Update a workflow by its UUID."""
        return self.storage.update(workflow)

    def list_workflows(self) -> list[WorkflowDefinition]:
        """List all workflows."""
        # Assuming the storage has a method to list all items
        return [
            self.storage.get(uuid)
            for uuid in self.storage.list_all()
            if self.storage.get(uuid)
        ]
