from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


def get_job(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)


def list_jobs(db: Session, *, offset: int = 0, limit: int = 20) -> list[Job]:
    return (
        db.query(Job)
        .order_by(Job.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_all_jobs(db: Session) -> list[Job]:
    return db.query(Job).order_by(Job.id).all()


def create_job(db: Session, job_data: JobCreate) -> Job:
    values = job_data.model_dump()
    values["url"] = str(job_data.url)
    job = Job(**values)

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return job
