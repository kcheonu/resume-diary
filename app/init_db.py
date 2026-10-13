import app.models.job  # noqa: F401
import app.models.schedule  # noqa: F401
from app.database import Base, get_engine


def initialize_database() -> None:
    Base.metadata.create_all(bind=get_engine())


if __name__ == "__main__":
    initialize_database()
    get_engine().dispose()
    print("데이터베이스 테이블 초기화를 완료했습니다.")
