# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Text, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    original_filename = Column(String)
    file_path = Column(String)

    config = Column(JSONB, nullable=True)
    status = Column(String)  # pending, processing, completed, failed
    progress = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    result_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, filename={self.filename}, status={self.status})"
