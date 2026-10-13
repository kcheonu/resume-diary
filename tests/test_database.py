import pytest
from sqlalchemy import text

from app.database import get_db, get_database_url, get_engine


def test_get_database_url_requires_environment_variable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()


def test_get_engine_uses_postgresql_url_from_environment(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://localhost/resume_diary",
    )
    get_engine.cache_clear()
    engine = get_engine()

    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()
        get_engine.cache_clear()


def test_database_dependency_provides_a_working_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    get_engine.cache_clear()
    engine = get_engine()
    db_generator = get_db()

    try:
        session = next(db_generator)

        assert session.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        db_generator.close()
        engine.dispose()
        get_engine.cache_clear()
