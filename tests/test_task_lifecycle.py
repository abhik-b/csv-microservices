import pytest
from datetime import datetime
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


from sqlalchemy import Column, Text, String, DateTime, JSON
import uuid
from datetime import datetime

TestBaseModel = declarative_base()


class TestTaskModel(TestBaseModel):
    __tablename__ = "tasks"
    __test__ = False

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    original_filename = Column(String)
    file_path = Column(String)

    config = Column(JSON, nullable=True)
    status = Column(String)  # pending, processing, completed, failed
    progress = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    result_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)


# Test database (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    TestBaseModel.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    TestBaseModel.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_task_data():
    """Sample data for creating tasks"""
    return {
        "filename": "test.csv",
        "original_filename": "original_test.csv",
        "file_path": "/uploads/test.csv",
        "status": "pending",
        "config": {"operations": []}
    }


def test_task_creation(db_session, sample_task_data):
    """Test creating a new Task record"""
    task = TestTaskModel(**sample_task_data)

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Assertions
    assert task.id is not None
    assert isinstance(task.id, str)
    assert task.status == "pending"
    assert task.created_at is not None
    assert isinstance(task.created_at, datetime)
    assert task.config == {"operations": []}


def test_task_processing(db_session, sample_task_data):

    task = TestTaskModel(**sample_task_data)
    db_session.add(task)
    db_session.commit()

    assert task.started_at is None, "No started_at after creation"
    task.status = "processing"
    task.started_at = datetime.now()
    db_session.commit()
    assert task.started_at is not None, "started_at gets updated as processing begins"


def test_task_config(db_session, sample_task_data):
    task = TestTaskModel(**sample_task_data)
    db_session.add(task)
    db_session.commit()

    config = {
        "operations": [
            {"op": "remove_duplicates", "params": {"subset": ["col1"]}},
            {"op": "drop_columns", "params": {"columns": ["col2"]}}
        ]
    }

    task.config = config
    db_session.commit()
    db_session.refresh(task)
    assert len(task.config["operations"]) == 2
