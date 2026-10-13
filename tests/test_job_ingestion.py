from app.schemas.job import JobCreate, JobResponse
from app.services.job_ingestion import normalize_job


def test_normalize_job_strips_company_and_title_and_preserves_other_values():
    raw = {
        "external_id": "job-123",
        "company": "  Example Corp  ",
        "title": "  Backend Engineer  ",
        "description": "Build APIs",
        "url": "https://example.com/jobs/123",
        "deadline": "2026-12-31T23:59:59",
        "skills": ["Python", "FastAPI"],
    }

    result = normalize_job(raw, "example")

    assert result == {
        "source": "example",
        "external_id": "job-123",
        "company": "Example Corp",
        "title": "Backend Engineer",
        "description": "Build APIs",
        "url": "https://example.com/jobs/123",
        "deadline": "2026-12-31T23:59:59",
        "skills": ["Python", "FastAPI"],
    }


def test_normalize_job_defaults_optional_fields():
    raw = {
        "company": "Example Corp",
        "title": "Backend Engineer",
        "url": "https://example.com/jobs/123",
    }

    result = normalize_job(raw, "example")

    assert result == {
        "source": "example",
        "external_id": None,
        "company": "Example Corp",
        "title": "Backend Engineer",
        "description": "",
        "url": "https://example.com/jobs/123",
        "deadline": None,
        "skills": [],
    }


def test_job_create_applies_defaults_and_validates_url():
    job = JobCreate(
        source="example",
        company="Example Corp",
        title="Backend Engineer",
        url="https://example.com/jobs/123",
    )

    assert job.external_id is None
    assert job.description == ""
    assert job.deadline is None
    assert job.skills == []
    assert str(job.url) == "https://example.com/jobs/123"


def test_job_response_includes_id():
    job = JobResponse(
        id=1,
        source="example",
        company="Example Corp",
        title="Backend Engineer",
        url="https://example.com/jobs/123",
    )

    assert job.id == 1
