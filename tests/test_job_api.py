import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.job import Job  # noqa: F401


@pytest.fixture(scope="module")
def test_database():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield engine
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


@pytest.fixture(scope="module")
def client(test_database):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_jobs(test_database):
    with Session(test_database) as session:
        session.query(Job).delete()
        session.commit()


def test_create_and_get_job(client):
    response = client.post(
        "/jobs",
        json={
            "source": "example",
            "external_id": "job-123",
            "company": "Example Corp",
            "title": "Backend Engineer",
            "url": "https://example.com/jobs/123",
            "skills": ["Python"],
        },
    )

    assert response.status_code == 201
    created_job = response.json()
    assert created_job["id"] == 1
    assert created_job["company"] == "Example Corp"
    assert created_job["skills"] == ["Python"]
    assert created_job["url"] == "https://example.com/jobs/123"

    get_response = client.get(f"/jobs/{created_job['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created_job


def test_list_jobs_supports_pagination(client):
    for index in range(3):
        response = client.post(
            "/jobs",
            json={
                "source": "example",
                "company": "Example Corp",
                "title": f"Engineer {index}",
                "url": f"https://example.com/jobs/{index}",
            },
        )
        assert response.status_code == 201

    response = client.get("/jobs", params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Engineer 1"


def test_get_job_returns_404_when_missing(client):
    response = client.get("/jobs/999")

    assert response.status_code == 404


def test_create_job_rejects_invalid_url(client):
    response = client.post(
        "/jobs",
        json={
            "source": "example",
            "company": "Example Corp",
            "title": "Backend Engineer",
            "url": "not-a-url",
        },
    )

    assert response.status_code == 422


def test_recommend_jobs_ranks_by_required_skill_overlap(client):
    jobs = [
        {
            "source": "example",
            "company": "Example Corp",
            "title": "Python Developer",
            "url": "https://example.com/jobs/1",
            "skills": ["Python", " FastAPI ", "python"],
        },
        {
            "source": "example",
            "company": "Example Corp",
            "title": "Python and SQL Developer",
            "url": "https://example.com/jobs/2",
            "skills": ["python", "SQL"],
        },
        {
            "source": "example",
            "company": "Example Corp",
            "title": "Frontend Developer",
            "url": "https://example.com/jobs/3",
            "skills": ["TypeScript"],
        },
    ]
    for job in jobs:
        assert client.post("/jobs", json=job).status_code == 201

    response = client.post(
        "/jobs/recommendations",
        json={"skills": ["  PYTHON ", "FastAPI"], "limit": 10},
    )

    assert response.status_code == 200
    recommendations = response.json()
    assert [item["job"]["title"] for item in recommendations] == [
        "Python Developer",
        "Python and SQL Developer",
    ]
    assert recommendations[0]["matched_skills"] == ["Python", "FastAPI"]
    assert recommendations[0]["match_score"] == 100
    assert recommendations[1]["matched_skills"] == ["python"]
    assert recommendations[1]["match_score"] == 50


@pytest.mark.parametrize(
    "payload",
    [
        {"skills": []},
        {"skills": ["Python"], "limit": 0},
        {"skills": ["Python"], "limit": 101},
    ],
)
def test_recommend_jobs_rejects_invalid_request(client, payload):
    response = client.post("/jobs/recommendations", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("params", "status_code"),
    [
        ({"offset": -1}, 422),
        ({"limit": 0}, 422),
        ({"limit": 101}, 422),
    ],
)
def test_list_jobs_rejects_invalid_pagination(client, params, status_code):
    response = client.get("/jobs", params=params)

    assert response.status_code == status_code
