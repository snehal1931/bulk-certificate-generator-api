"""Pytest configuration and shared fixtures."""

import os
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set env vars before importing application modules
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_certificate_generator.db"
os.environ["STORAGE_DIR"] = "storage/test_certificates"

from app.main import app
from app.core.database import Base, get_db, engine as app_engine
from app.core.config import settings

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure clean test storage directory exists and cleanup after."""
    # Ensure DB file is removed before starting session
    if os.path.exists("./test_certificate_generator.db"):
        os.remove("./test_certificate_generator.db")
        
    storage_dir = settings.get_absolute_storage_dir()
    Base.metadata.create_all(bind=app_engine)
    yield
    # Cleanup storage after all tests
    if storage_dir.exists() and "test_certificates" in str(storage_dir):
        shutil.rmtree(storage_dir, ignore_errors=True)
    
    # Drop tables and remove DB file
    Base.metadata.drop_all(bind=app_engine)
    if os.path.exists("./test_certificate_generator.db"):
        try:
            os.remove("./test_certificate_generator.db")
        except PermissionError:
            pass


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean data from tables without dropping them
        from app.models.certificate import Certificate
        from app.models.job import Job
        clean_session = TestingSessionLocal()
        clean_session.query(Certificate).delete()
        clean_session.query(Job).delete()
        clean_session.commit()
        clean_session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI test client with the db dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
