from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_serves_career_diary():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "취업 준비 다이어리" in response.text
    assert "/static/app.css" in response.text


def test_frontend_assets_are_served():
    client = TestClient(app)

    css_response = client.get("/static/app.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert ".app-shell" in css_response.text
    assert js_response.status_code == 200
    assert '"/jobs/recommendations"' in js_response.text
