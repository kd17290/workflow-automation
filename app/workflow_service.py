import logging
from datetime import datetime
from typing import Any

from app.connector.factory import ConnectorFactory
from app.models import StepResult
from app.models import StepStatus
from app.models import WorkflowDefinition
from app.models import WorkflowRun
from app.models import WorkflowStatus
from app.models import WorkflowStep
from app.repository.workflow_repository import WorkflowRepository
from app.repository.workflow_run_repository import WorkflowRunRepository
from app.storage.enum import StorageType
from app.storage.factory import StorageFactory


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, storage: StorageType):
        """
        Initialize the WorkflowService with a specific storage type.
        :param storage: The type of storage to use (e.g., "file_system", "in_memory").
        :type storage: StorageType
        :raises ValueError: If the storage type is unknown.
        """
        storage_cls = StorageFactory.create_storage(storage)

        # Initialize storage and engine
        workflow_storage = storage_cls[WorkflowDefinition](t_type=WorkflowDefinition)
        workflow_run_storage = storage_cls[WorkflowRun](t_type=WorkflowRun)

        self.workflow_repository = WorkflowRepository(workflow_storage)
        self.workflow_run_repository = WorkflowRunRepository(workflow_run_storage)

    def create_workflow(self, workflow: WorkflowDefinition):
        """Create a new workflow."""
        return self.workflow_repository.create_workflow(workflow)

    def load_workflow(self, uuid: str) -> WorkflowDefinition:
        """Load a workflow by its UUID."""
        return self.workflow_repository.get_workflow(uuid)

    def create_workflow_run(self, workflow_run):
        """Create a new workflow run."""
        return self.workflow_run_repository.create_workflow_run(workflow_run)

    def load_workflow_run(self, uuid: str):
        """Load a workflow run by its UUID."""
        return self.workflow_run_repository.get_workflow_run(uuid)

    def list_runs(self):
        """List all workflow runs."""
        return self.workflow_run_repository.list_workflow_runs()

    async def execute_workflow(self, run_id: str):
        """Execute a workflow run by its ID."""
        # This method would contain the logic to execute the workflow.
        # For now, we will just return a placeholder message.
        run = self.load_workflow_run(run_id)
        if not run:
            logger.error(f"Workflow run {run_id} not found")
            return

        workflow = self.load_workflow(run.workflow_id)
        if not workflow:
            logger.error(f"Workflow {run.workflow_id} not found")
            run.status = WorkflowStatus.FAILED
            run.error = f"Workflow {run.workflow_id} not found"
            self.workflow_run_repository.update_workflow_run(run)
            return

        logger.info(f"Executing workflow run {run_id}")
        run.status = WorkflowStatus.RUNNING
        self.workflow_run_repository.update_workflow_run(run)

        context = {"payload": run.payload}
        try:
            for step in workflow.steps:
                step_result = await self._execute_step(step, context)
                run.step_results[step.name] = step_result

                if step_result.status == StepStatus.FAILED:
                    run.status = WorkflowStatus.FAILED
                    run.error = step_result.error
                    run.completed_at = datetime.now().isoformat()
                    self.workflow_run_repository.update_workflow_run(run)
                    return

                # Add step output to context for next steps
                if step_result.output:
                    context[step.name] = step_result.output

            # All steps completed successfully
            run.status = WorkflowStatus.SUCCESS
            run.completed_at = datetime.now().isoformat()
            self.workflow_run_repository.update_workflow_run(run)
            logger.info(f"Workflow run {run_id} completed successfully")

        except Exception as e:
            logger.error(f"Workflow run {run_id} failed: {str(e)}")
            run.status = WorkflowStatus.FAILED
            run.error = str(e)
            run.completed_at = datetime.now().isoformat()
            self.workflow_run_repository.update_workflow_run(run)

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]):
        """Execute a single workflow step."""
        """This method would contain the logic to execute a single step."""
        result = StepResult(
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        try:
            # Simulate step execution
            connector = ConnectorFactory.get_instance(step.type)
            logger.info(f"Executing step: {step.name} ({step.type})")
            result.output = await connector.execute(step, context)
            result.status = StepStatus.SUCCESS
            result.completed_at = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Step {step.name} failed: {str(e)}")
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now().isoformat()
        return result
