from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.job import Job
from app.schemas.job import JobCreate
from app.services.job_repository import create_job


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def test_create_job_persists_and_returns_job(db_session):
    job_data = JobCreate(
        source="example",
        external_id="job-123",
        company="Example Corp",
        title="Backend Engineer",
        description="Build APIs",
        url="https://example.com/jobs/123",
        deadline=datetime(2026, 12, 31, 23, 59, 59),
        skills=["Python", "FastAPI"],
    )

    created_job = create_job(db_session, job_data)

    assert created_job.id is not None
    assert created_job.source == "example"
    assert created_job.external_id == "job-123"
    assert created_job.company == "Example Corp"
    assert created_job.title == "Backend Engineer"
    assert created_job.description == "Build APIs"
    assert created_job.url == "https://example.com/jobs/123"
    assert created_job.deadline == datetime(2026, 12, 31, 23, 59, 59)
    assert created_job.skills == ["Python", "FastAPI"]

    persisted_job = db_session.get(Job, created_job.id)
    assert persisted_job is not None
    assert persisted_job.url == "https://example.com/jobs/123"


def test_create_job_persists_schema_defaults(db_session):
    job_data = JobCreate(
        source="example",
        company="Example Corp",
        title="Backend Engineer",
        url="https://example.com/jobs/123",
    )

    created_job = create_job(db_session, job_data)

    assert created_job.external_id is None
    assert created_job.description == ""
    assert created_job.deadline is None
    assert created_job.skills == []
