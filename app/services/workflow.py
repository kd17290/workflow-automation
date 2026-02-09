import logging
from datetime import datetime
from typing import Any

from app.connector.factory import ConnectorFactory
from app.schemas.workflow import StepResult, WorkflowDefinition, WorkflowStep
from app.schemas.run import WorkflowRun
from app.schemas.common import StepStatus, WorkflowStatus
from app.repositories.workflow import WorkflowRepository
from app.repositories.run import WorkflowRunRepository
from app.storage.enum import StorageType
from app.storage.factory import StorageFactory


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, storage: StorageType):
        """
        Initialize the WorkflowService with a specific storage type.

        Args:
            storage (StorageType): The type of storage to use (e.g., StorageType.FILE_SYSTEM).

        Raises:
            ValueError: If the storage type is unknown.
        """
        storage_cls = StorageFactory.create_storage(storage)

        # Initialize storage and engine
        workflow_storage = storage_cls[WorkflowDefinition](t_type=WorkflowDefinition)
        workflow_run_storage = storage_cls[WorkflowRun](t_type=WorkflowRun)

        self.workflow_repository = WorkflowRepository(workflow_storage)
        self.workflow_run_repository = WorkflowRunRepository(workflow_run_storage)

    def create_workflow(self, workflow: WorkflowDefinition) -> str:
        """
        Create a new workflow definition.

        Args:
            workflow (WorkflowDefinition): The workflow definition to create.

        Returns:
            str: The UUID of the created workflow.
        """
        return self.workflow_repository.create_workflow(workflow)

    def load_workflow(self, uuid: str) -> WorkflowDefinition:
        """
        Load a workflow definition by its UUID.

        Args:
            uuid (str): The UUID of the workflow to load.

        Returns:
            WorkflowDefinition: The workflow definition, or None if not found.
        """
        return self.workflow_repository.get_workflow(uuid)

    def create_workflow_run(self, workflow_run: WorkflowRun) -> str:
        """
        Create a new workflow run.

        Args:
            workflow_run (WorkflowRun): The workflow run object to save.

        Returns:
            str: The UUID of the created workflow run.
        """
        return self.workflow_run_repository.create_workflow_run(workflow_run)

    def load_workflow_run(self, uuid: str) -> WorkflowRun:
        """
        Load a workflow run by its UUID.

        Args:
            uuid (str): The UUID of the workflow run to load.

        Returns:
            WorkflowRun: The workflow run object, or None if not found.
        """
        return self.workflow_run_repository.get_workflow_run(uuid)

    def list_runs(self) -> list[WorkflowRun]:
        """
        List all workflow runs.

        Returns:
            list[WorkflowRun]: A list of all workflow runs.
        """
        return self.workflow_run_repository.list_workflow_runs()

    async def execute_workflow(self, run_id: str):
        """
        Execute a workflow run.

        Args:
            run_id (str): The UUID of the workflow run to execute.

        This method:
            1. Loads the run and workflow definition.
            2. Updates status to RUNNING.
            3. Iterates through steps sequentially, passing context.
            4. Handling step retries (if implemented) or failure.
            5. Updates final status to SUCCESS or FAILED.
        """
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
        """
        Execute a single workflow step.

        Args:
            step (WorkflowStep): The step definition.
            context (dict[str, Any]): The execution context containing payload and previous step outputs.

        Returns:
            StepResult: The result of the step execution.
        """
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
