# create API testcases
import pytest
from fastapi.testclient import TestClient

from app.legacy_storage import WorkflowStorage
from app.main import app
from app.models import TriggerRequest
from app.models import WorkflowDefinition
from app.models import WorkflowStatus

# Initialize test client
client = TestClient(app)


@pytest.fixture
def workflow_storage():
    """Fixture to provide a fresh WorkflowStorage instance for each test."""
    storage = WorkflowStorage()
    yield storage


@pytest.fixture
def sample_workflow():
    """Fixture to provide a sample workflow definition."""
    return WorkflowDefinition(
        id="test_workflow",
        name="Test Workflow",
        description="A workflow for testing purposes",
        steps=[
            {"name": "initial_delay", "type": "delay", "config": {"duration": 3}},
            {
                "name": "send_notification",
                "type": "webhook",
                "config": {
                    "url": "https://httpbin.org/post",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "message": "Test notification from workflow",
                        "user_id": "${payload.user_id}",
                        "processed_at": "${payload.timestamp}",
                    },
                },
            },
        ],
    )


@pytest.fixture
def sample_trigger_request():
    """Fixture to provide a sample trigger request."""
    return TriggerRequest(
        workflow_id="test_workflow",
        payload={
            "user_id": "user123",
            "timestamp": "2024-01-01T10:00:00Z",
            "event": "user_signup",
        },
    )


def test_create_workflow(workflow_storage, sample_workflow):
    """Test creating a workflow."""
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200
    assert response.json() == {
        "message": "Workflow created successfully",
        "workflow_id": sample_workflow.id,
    }

    # Verify the workflow is saved in storage
    stored_workflow = workflow_storage.load_workflow(sample_workflow.id)
    assert stored_workflow == sample_workflow


def test_trigger_workflow(workflow_storage, sample_workflow, sample_trigger_request):
    """Test triggering a workflow execution."""
    # First, save the workflow
    workflow_storage.save_workflow(sample_workflow)

    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "status" in data
    assert data["status"] == "triggered"

    # Verify the run is created in storage
    run_id = data["run_id"]
    run = workflow_storage.load_run(run_id)
    assert run is not None
    assert run.workflow_id == sample_trigger_request.workflow_id


def test_get_workflow(workflow_storage, sample_workflow):
    """Test retrieving a workflow definition."""
    # First, save the workflow
    workflow_storage.save_workflow(sample_workflow)

    response = client.get(f"/api/v1/workflows/{sample_workflow.id}")
    assert response.status_code == 200
    assert response.json() == sample_workflow.model_dump()


def test_get_nonexistent_workflow():
    """Test retrieving a non-existent workflow."""
    response = client.get("/api/v1/workflows/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Workflow not found"}


def test_get_run(workflow_storage, sample_workflow, sample_trigger_request):
    """Test retrieving a workflow run."""
    # First, save the workflow and trigger it
    workflow_storage.save_workflow(sample_workflow)
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    run = response.json()
    assert run["id"] == run_id
    assert run["workflow_id"] == sample_workflow.id


def test_get_nonexistent_run(workflow_storage):
    """Test retrieving a non-existent workflow run."""
    response = client.get("/api/v1/runs/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Workflow run not found"}


def test_list_runs(workflow_storage, sample_workflow, sample_trigger_request):
    """Test listing all workflow runs."""
    # First, save the workflow and trigger it
    workflow_storage.save_workflow(sample_workflow)
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200

    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    run_ids = response.json()
    assert isinstance(run_ids, list)
    assert len(run_ids) > 0


def test_workflow_run_status(workflow_storage, sample_workflow, sample_trigger_request):
    """Test the status of a workflow run."""
    # First, save the workflow and trigger it
    workflow_storage.save_workflow(sample_workflow)
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    # Check the run status
    run = workflow_storage.load_run(run_id)
    assert run is not None
    assert run.status == WorkflowStatus.SUCCESS or run.status == WorkflowStatus.RUNNING
