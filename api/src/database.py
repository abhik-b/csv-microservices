from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
import os


# db_url = "postgresql://postgres:admin@localhost:5432/csv-processin"
# db_url = "postgresql://postgres:admin@host.docker.internal:5432/csv-processin"
# Get DATABASE_URL from environment, fallback to default
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
