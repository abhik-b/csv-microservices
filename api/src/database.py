from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:admin@localhost:5432/csv-processin"
)
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_task_service():
    return 1
