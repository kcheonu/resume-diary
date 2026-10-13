from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.schedule import ScheduleTask, StudyPlan


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
def clear_plans(test_database):
    with Session(test_database) as session:
        session.query(ScheduleTask).delete()
        session.query(StudyPlan).delete()
        session.commit()


def create_plan(client):
    return client.post(
        "/schedules",
        json={
            "goal": "백엔드 취업 준비",
            "start_date": "2026-10-01",
            "end_date": "2026-10-11",
            "tasks": [
                {"title": "이력서 정리"},
                {"title": "프로젝트 보완"},
                {"title": "모의 면접"},
            ],
        },
    )


def test_create_schedule_spreads_tasks_across_date_range(client):
    response = create_plan(client)

    assert response.status_code == 201
    plan = response.json()
    assert plan["goal"] == "백엔드 취업 준비"
    assert [task["scheduled_date"] for task in plan["tasks"]] == [
        "2026-10-01",
        "2026-10-06",
        "2026-10-11",
    ]
    assert all(task["status"] == "pending" for task in plan["tasks"])

    detail_response = client.get(f"/schedules/{plan['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json() == plan


def test_replan_moves_only_pending_tasks(client):
    created = create_plan(client)
    plan = created.json()
    completed_task = plan["tasks"][1]

    update_response = client.patch(
        f"/schedules/{plan['id']}/tasks/{completed_task['id']}",
        json={"status": "completed"},
    )
    assert update_response.status_code == 200

    response = client.post(
        f"/schedules/{plan['id']}/replan",
        json={"start_date": "2026-10-20", "end_date": "2026-10-30"},
    )

    assert response.status_code == 200
    replanned = response.json()
    assert replanned["start_date"] == "2026-10-20"
    assert replanned["end_date"] == "2026-10-30"
    tasks_by_title = {task["title"]: task for task in replanned["tasks"]}
    assert tasks_by_title["이력서 정리"]["scheduled_date"] == "2026-10-20"
    assert tasks_by_title["프로젝트 보완"]["scheduled_date"] == "2026-10-06"
    assert tasks_by_title["프로젝트 보완"]["status"] == "completed"
    assert tasks_by_title["모의 면접"]["scheduled_date"] == "2026-10-30"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "goal": "목표",
            "start_date": "2026-10-12",
            "end_date": "2026-10-11",
            "tasks": [{"title": "준비"}],
        },
        {
            "goal": "목표",
            "start_date": "2026-10-01",
            "end_date": "2026-10-11",
            "tasks": [],
        },
    ],
)
def test_create_schedule_rejects_invalid_request(client, payload):
    response = client.post("/schedules", json=payload)

    assert response.status_code == 422


def test_replan_rejects_invalid_date_range(client):
    plan_id = create_plan(client).json()["id"]

    response = client.post(
        f"/schedules/{plan_id}/replan",
        json={"start_date": "2026-10-30", "end_date": "2026-10-20"},
    )

    assert response.status_code == 422


def test_schedule_endpoints_return_404_for_missing_records(client):
    assert client.get("/schedules/999").status_code == 404
    assert client.post(
        "/schedules/999/replan",
        json={"start_date": "2026-10-20", "end_date": "2026-10-30"},
    ).status_code == 404
    assert client.patch(
        "/schedules/999/tasks/999",
        json={"status": "completed"},
    ).status_code == 404


def test_task_status_rejects_unknown_value(client):
    plan_id = create_plan(client).json()["id"]

    response = client.patch(
        f"/schedules/{plan_id}/tasks/1",
        json={"status": "skipped"},
    )

    assert response.status_code == 422


def test_schedule_response_dates_are_valid_dates(client):
    response = create_plan(client)
    assert date.fromisoformat(response.json()["start_date"]) == date(2026, 10, 1)
