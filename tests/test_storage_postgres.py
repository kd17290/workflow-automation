# Unit tests for PostgreSQL storage backend
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.schemas.workflow import WorkflowDefinition
from app.schemas.run import WorkflowRun
from app.schemas.common import WorkflowStatus
from app.storage.db_storage import DBStorage
from app.db.session import Base


# Test database configuration - uses test_ prefix for isolation
TEST_POSTGRES_HOST = os.getenv("POSTGRES_HOST", "workflow_db")
TEST_POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
TEST_POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
TEST_POSTGRES_DB = f"test_{os.getenv('POSTGRES_DB', 'workflow_db')}"

TEST_DB_URL = f"postgresql://{TEST_POSTGRES_USER}:{TEST_POSTGRES_PASSWORD}@{TEST_POSTGRES_HOST}/{TEST_POSTGRES_DB}"


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine."""
    # Connect to default database to create test database
    admin_url = f"postgresql://{TEST_POSTGRES_USER}:{TEST_POSTGRES_PASSWORD}@{TEST_POSTGRES_HOST}/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        # Drop test database if exists and recreate
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_POSTGRES_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_POSTGRES_DB}"))

    admin_engine.dispose()

    # Create engine for test database
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup - drop test database
    engine.dispose()
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_POSTGRES_DB}"))
    admin_engine.dispose()


@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    """Create a session factory for the test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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


class TestPostgresStorage:
    """Test suite for DBStorage (PostgreSQL) with isolated test database."""

    @pytest.fixture(autouse=True)
    def setup_db(self, test_engine, test_session_factory):
        """Setup and teardown database tables for each test."""
        # Store session factory for use in storage
        self._session_factory = test_session_factory

        # Clear tables before each test
        with test_session_factory() as db:
            db.execute(text("TRUNCATE TABLE workflow_definitions, workflow_runs CASCADE"))
            db.commit()

        yield

        # Cleanup after test
        with test_session_factory() as db:
            db.execute(text("TRUNCATE TABLE workflow_definitions, workflow_runs CASCADE"))
            db.commit()

    def _get_storage(self, t_type):
        """Get a storage instance with test session factory."""
        storage = DBStorage[t_type](t_type=t_type)
        # Override the session factory to use test database
        storage._session_factory = self._session_factory
        return storage

    def test_create_workflow(self, sample_workflow_definition):
        """Test creating a workflow in PostgreSQL storage."""
        storage = self._get_storage(WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        assert uuid is not None
        assert sample_workflow_definition.uuid == uuid

    def test_get_workflow(self, sample_workflow_definition):
        """Test retrieving a workflow from PostgreSQL storage."""
        storage = self._get_storage(WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        retrieved = storage.get(uuid)
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"

    def test_get_nonexistent_workflow(self):
        """Test retrieving a non-existent workflow."""
        storage = self._get_storage(WorkflowDefinition)

        result = storage.get("nonexistent_uuid")
        assert result is None

    def test_update_workflow(self, sample_workflow_definition):
        """Test updating a workflow in PostgreSQL storage."""
        storage = self._get_storage(WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        sample_workflow_definition.name = "Updated Workflow"
        result = storage.update(sample_workflow_definition)

        assert result is True
        retrieved = storage.get(uuid)
        assert retrieved.name == "Updated Workflow"

    def test_delete_workflow(self, sample_workflow_definition):
        """Test deleting a workflow from PostgreSQL storage."""
        storage = self._get_storage(WorkflowDefinition)
        uuid = storage.create(sample_workflow_definition)

        result = storage.delete(uuid)
        assert result is True

        retrieved = storage.get(uuid)
        assert retrieved is None

    def test_list_all_workflows(self, sample_workflow_definition):
        """Test listing all workflows from PostgreSQL storage."""
        storage = self._get_storage(WorkflowDefinition)
        storage.create(sample_workflow_definition)

        workflows = storage.list_all()
        assert len(workflows) >= 1

    def test_create_run(self, sample_workflow_run):
        """Test creating a run in PostgreSQL storage."""
        storage = self._get_storage(WorkflowRun)
        uuid = storage.create(sample_workflow_run)

        assert uuid is not None
        assert sample_workflow_run.uuid == uuid

    def test_get_run(self, sample_workflow_run):
        """Test retrieving a run from PostgreSQL storage."""
        storage = self._get_storage(WorkflowRun)
        uuid = storage.create(sample_workflow_run)

        retrieved = storage.get(uuid)
        assert retrieved is not None
        assert retrieved.workflow_id == "test_workflow_uuid"
        assert retrieved.status == WorkflowStatus.PENDING

    def test_update_run_status(self, sample_workflow_run):
        """Test updating run status in PostgreSQL storage."""
        storage = self._get_storage(WorkflowRun)
        uuid = storage.create(sample_workflow_run)

        sample_workflow_run.status = WorkflowStatus.RUNNING
        result = storage.update(sample_workflow_run)

        assert result is True
        retrieved = storage.get(uuid)
        assert retrieved.status == WorkflowStatus.RUNNING

    def test_list_all_runs(self, sample_workflow_run):
        """Test listing all runs from PostgreSQL storage."""
        storage = self._get_storage(WorkflowRun)
        storage.create(sample_workflow_run)

        runs = storage.list_all()
        assert len(runs) >= 1
