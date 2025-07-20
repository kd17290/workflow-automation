# create API testcases
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import TriggerRequest
from app.models import WorkflowDefinition
from app.models import WorkflowStatus
from app.storage.enum import StorageType
from app.workflow_service import WorkflowService

# Initialize test client


@pytest.fixture
def client():
    """Fixture to provide a FastAPI test client."""
    yield TestClient(app)


@pytest.fixture
def file_system_workflow_service():
    """Fixture to provide a fresh WorkflowStorage instance for each test."""
    yield WorkflowService(StorageType.IN_MEMORY)


@pytest.fixture
def in_memory_workflow_service():
    """Fixture to provide a fresh WorkflowStorage instance for each test."""
    yield WorkflowService(StorageType.IN_MEMORY)


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


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_get_workflow(client, workflow_service_fixture, sample_workflow):
    """Test retrieving a workflow."""
    # First create the workflow
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200

    # Now retrieve it
    workflow_id = response.json()["workflow_id"]
    response = client.get(f"/api/v1/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["id"] == "test_workflow"
    assert response.json()["name"] == "Test Workflow"


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_trigger_workflow(
    client, workflow_service_fixture, sample_workflow, sample_trigger_request
):
    """Test triggering a workflow execution."""
    # First create the workflow
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200

    sample_trigger_request.workflow_id = response.json()["workflow_id"]
    # Now trigger it
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    assert "run_id" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "triggered"


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_get_run(
    client, workflow_service_fixture, sample_workflow, sample_trigger_request
):
    """Test retrieving a workflow run."""
    # First create the workflow
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200

    sample_trigger_request.workflow_id = response.json()["workflow_id"]
    # Now trigger it
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    # Now retrieve the run
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["workflow_id"] == sample_trigger_request.workflow_id
    assert response.json()["status"] in [
        WorkflowStatus.PENDING,
        WorkflowStatus.RUNNING,
        WorkflowStatus.SUCCESS,
    ]


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_list_runs(
    client, workflow_service_fixture, sample_workflow, sample_trigger_request
):
    """Test listing all workflow runs."""
    # First create the workflow
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200

    sample_trigger_request.workflow_id = response.json()["workflow_id"]
    # Now trigger it
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200

    # Now list all runs
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_create_workflow_invalid(client, workflow_service_fixture):
    """Test creating a workflow with invalid data."""
    response = client.post("/api/v1/workflows", json={"name": "Invalid Workflow"})
    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()
    assert "steps" in response.json()["detail"][0]["loc"]
    assert response.json()["detail"][0]["msg"] == "Field required"


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_trigger_workflow_invalid(client, workflow_service_fixture):
    """Test triggering a workflow with invalid data."""
    response = client.post("/api/v1/trigger", json={"workflow_id": "non_existent"})
    assert response.status_code == 404  # Not Found
    assert response.json()["detail"] == "Workflow non_existent not found"


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_get_run_not_found(client, workflow_service_fixture):
    """Test retrieving a non-existent workflow run."""
    response = client.get("/api/v1/runs/non_existent_run")
    assert response.status_code == 404  # Not Found
    assert response.json()["detail"] == "Workflow run not found"


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_list_runs_empty(client, workflow_service_fixture):
    """Test listing runs when no runs exist."""
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.parametrize(
    "workflow_service_fixture",
    ["file_system_workflow_service", "in_memory_workflow_service"],
)
def test_workflow_run_status(
    client, workflow_service_fixture, sample_workflow, sample_trigger_request
):
    """Test the status of a workflow run."""
    # First create the workflow
    response = client.post("/api/v1/workflows", json=sample_workflow.model_dump())
    assert response.status_code == 200

    sample_trigger_request.workflow_id = response.json()["workflow_id"]
    # Now trigger it
    response = client.post("/api/v1/trigger", json=sample_trigger_request.model_dump())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    # Now check the run status
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["status"] in [
        WorkflowStatus.PENDING,
        WorkflowStatus.RUNNING,
        WorkflowStatus.SUCCESS,
    ]
