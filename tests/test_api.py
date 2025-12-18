# import pytest
# import tempfile
# import os
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from unittest.mock import Mock, patch
# from sqlalchemy import Column, Text, String, DateTime, JSON
# import uuid
# from datetime import datetime
# # Import your app and models
# from src.main import app
# # from src.db_models import Base, Task
# from src.database import get_db

# # ====================
# # TEST DATABASE SETUP
# # ====================

# TestBaseModel = declarative_base()


# class TestTaskModel(TestBaseModel):
#     __tablename__ = "tasks"
#     __test__ = False

#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     filename = Column(String)
#     original_filename = Column(String)
#     file_path = Column(String)

#     config = Column(JSON, nullable=True)
#     status = Column(String)  # pending, processing, completed, failed
#     progress = Column(String, nullable=True)

#     created_at = Column(DateTime, default=datetime.now())
#     started_at = Column(DateTime, nullable=True)
#     completed_at = Column(DateTime, nullable=True)

#     result_path = Column(String, nullable=True)
#     error_message = Column(Text, nullable=True)


# # Use SQLite in-memory for testing
# TEST_DATABASE_URL = "sqlite:///:memory:"
# test_engine = create_engine(TEST_DATABASE_URL)
# TestingSessionLocal = sessionmaker(
#     autocommit=False, autoflush=False, bind=test_engine)

# # Override the get_db dependency


# def override_get_db():
#     """Override the database dependency for testing"""
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# app.dependency_overrides[get_db] = override_get_db

# # Create test client
# client = TestClient(app)


# @pytest.fixture(scope="function", autouse=True)
# def setup_database():
#     """Setup and teardown test database for each test"""
#     TestBaseModel.metadata.create_all(bind=test_engine)
#     yield
#     TestBaseModel.metadata.drop_all(bind=test_engine)

# # ====================
# # TEST 1: FILE UPLOAD
# # ====================


# def test_upload_valid_csv_returns_task_id():
#     """Test that uploading a valid CSV returns a task_id"""

#     # Create a temporary CSV file
#     csv_content = "name,age,city\nJohn,30,NYC\nJane,25,LA\n"

#     # Use TestClient's multipart upload
#     files = {
#         'csv_file': ('test.csv', csv_content, 'text/csv')
#     }

#     response = client.post("/upload", files=files)

#     # Assertions
#     assert response.status_code == 200
#     response_data = response.json()

#     # Should return task_id
#     assert "taskID" in response_data
#     assert isinstance(response_data["taskID"], str)
#     assert len(response_data["taskID"]) == 36  # UUID length

#     # Should have success message
#     assert "message" in response_data
#     assert "uploaded" in response_data["message"].lower()

#     # Verify task was created in database
#     with TestingSessionLocal() as db:
#         task = db.query(TestTaskModel).filter(
#             TestTaskModel.id == response_data["taskID"]).first()
#         assert task is not None
#         assert task.filename.endswith('.csv')
#         assert task.original_filename == 'test.csv'
#         assert task.status == 'pending'
#         assert os.path.exists(task.file_path)  # File should be saved
