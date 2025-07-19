import json
import logging
from pathlib import Path
from typing import List
from typing import Optional

from .models import WorkflowDefinition
from .models import WorkflowRun

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowStorage:
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.workflows_path = self.base_path / "workflows"
        self.runs_path = self.base_path / "runs"

        # Create directories if they don't exist
        self.workflows_path.mkdir(parents=True, exist_ok=True)
        self.runs_path.mkdir(parents=True, exist_ok=True)

    def save_workflow(self, workflow: WorkflowDefinition):
        """Save workflow definition to filesystem"""
        workflow_file = self.workflows_path / f"{workflow.id}.json"
        print(f"Saving workflow to {workflow_file=}")
        with open(workflow_file, "w") as f:
            json.dump(workflow.model_dump(), f, indent=2)

    def load_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Load workflow definition from filesystem"""
        workflow_file = self.workflows_path / f"{workflow_id}.json"
        if not workflow_file.exists():
            return None

        with open(workflow_file, "r") as f:
            data = json.load(f)
        return WorkflowDefinition(**data)

    def save_run(self, run: WorkflowRun):
        """Save workflow run to filesystem"""
        run_file = self.runs_path / f"{run.id}.json"
        # Convert datetime objects to ISO format for JSON serialization
        run_data = run.model_dump()

        with open(run_file, "w") as f:
            json.dump(run_data, f, indent=2)

    def load_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Load workflow run from filesystem"""
        run_file = self.runs_path / f"{run_id}.json"
        if not run_file.exists():
            return None

        with open(run_file, "r") as f:
            data = json.load(f)

        return WorkflowRun(**data)

    def list_runs(self) -> List[str]:
        """List all workflow run IDs"""
        return [f.stem for f in self.runs_path.glob("*.json")]
