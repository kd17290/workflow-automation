# Unit tests for FileSystem storage backend
import pytest

from app.schemas.workflow import WorkflowDefinition
from app.schemas.run import WorkflowRun
from app.schemas.common import WorkflowStatus
from app.storage.file_storage import FileStorage


@pytest.fixture
def sample_workflow_definition():
    """Sample workflow definition for testing."""
    return WorkflowDefinition(
        id="test_workflow",
        name="Test Workflow",
        description="A workflow for testing storage",
        steps=[
            {"name": "step1", "type": "delay", "config": {"duration": 1}},
        ],
    )


@pytest.fixture
def sample_workflow_run():
    """Sample workflow run for testing."""
    return WorkflowRun(
        workflow_id="test_workflow_uuid",
        status=WorkflowStatus.PENDING,
        payload={"key": "value"},
        started_at="2024-01-01T10:00:00Z",
    )


class TestFileSystemStorage:
    """Test suite for FileStorage."""

    def test_create_workflow(self, sample_workflow_definition):
        """Test creating a workflow in FileSystem storage."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        assert uuid is not None
        assert sample_workflow_definition.uuid == uuid

    def test_get_workflow(self, sample_workflow_definition):
        """Test retrieving a workflow from FileSystem storage."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        retrieved = storage.get(uuid)
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"

    def test_get_nonexistent_workflow(self):
        """Test retrieving a non-existent workflow."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)

        result = storage.get("nonexistent_uuid")
        assert result is None

    def test_update_workflow(self, sample_workflow_definition):
        """Test updating a workflow in FileSystem storage."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        sample_workflow_definition.name = "Updated Workflow"
        result = storage.update(sample_workflow_definition)

        assert result is True
        retrieved = storage.get(uuid)
        assert retrieved.name == "Updated Workflow"

    def test_delete_workflow(self, sample_workflow_definition):
        """Test deleting a workflow from FileSystem storage."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        result = storage.delete(uuid)
        assert result is True

        retrieved = storage.get(uuid)
        assert retrieved is None

    def test_list_all_workflows(self, sample_workflow_definition):
        """Test listing all workflows from FileSystem storage."""
        storage = FileStorage[WorkflowDefinition](t_type=WorkflowDefinition)
        storage.create(sample_workflow_definition)

        workflows = storage.list_all()
        assert len(workflows) >= 1

    def test_create_run(self, sample_workflow_run):
        """Test creating a run in FileSystem storage."""
        storage = FileStorage[WorkflowRun](t_type=WorkflowRun)
        uuid = storage.create(sample_workflow_run)

        assert uuid is not None
        assert sample_workflow_run.uuid == uuid
