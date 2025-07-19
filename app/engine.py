import logging
from datetime import datetime
from typing import Any

from app.connector.factory import ConnectorFactory
from app.models import StepResult
from app.models import StepStatus
from app.models import WorkflowStatus
from app.models import WorkflowStep
from app.storage import WorkflowStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self, storage: WorkflowStorage):
        self.storage = storage

    async def execute_workflow(self, run_id: str):
        """Execute a workflow run"""
        run = self.storage.load_run(run_id)
        if not run:
            logger.error(f"Workflow run {run_id} not found")
            return

        workflow = self.storage.load_workflow(run.workflow_id)
        if not workflow:
            logger.error(f"Workflow {run.workflow_id} not found")
            run.status = WorkflowStatus.FAILED
            run.error = f"Workflow {run.workflow_id} not found"
            run.completed_at = datetime.now().isoformat()
            self.storage.save_run(run)
            return

        logger.info(f"Starting workflow run {run_id}")
        run.status = WorkflowStatus.RUNNING
        self.storage.save_run(run)

        context = {"payload": run.payload}

        try:
            for step in workflow.steps:
                step_result = await self._execute_step(step, context)
                run.step_results[step.name] = step_result

                if step_result.status == StepStatus.FAILED:
                    run.status = WorkflowStatus.FAILED
                    run.error = step_result.error
                    run.completed_at = datetime.now().isoformat()
                    self.storage.save_run(run)
                    return

                # Add step output to context for next steps
                if step_result.output:
                    context[step.name] = step_result.output

            # All steps completed successfully
            run.status = WorkflowStatus.SUCCESS
            run.completed_at = datetime.now().isoformat()
            self.storage.save_run(run)
            logger.info(f"Workflow run {run_id} completed successfully")

        except Exception as e:
            logger.error(f"Workflow run {run_id} failed: {str(e)}")
            run.status = WorkflowStatus.FAILED
            run.error = str(e)
            run.completed_at = datetime.now().isoformat()
            self.storage.save_run(run)

    async def _execute_step(
        self, step: WorkflowStep, context: dict[str, Any]
    ) -> StepResult:
        """Execute a single workflow step"""
        step_result = StepResult(
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )

        try:
            connector = ConnectorFactory.get_instance(step.type)
            logger.info(f"Executing step: {step.name} ({step.type})")
            output = await connector.execute(step, context)
            step_result.status = StepStatus.SUCCESS
            step_result.output = output
            step_result.completed_at = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Step {step.name} failed: {str(e)}")
            step_result.status = StepStatus.FAILED
            step_result.error = str(e)
            step_result.completed_at = datetime.now().isoformat()

        return step_result
