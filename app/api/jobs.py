from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import (
    JobCreate,
    JobRecommendationRequest,
    JobRecommendationResponse,
    JobResponse,
)
from app.services.job_recommendation import recommend_jobs
from app.services.job_repository import create_job, get_job, list_jobs


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/recommendations", response_model=list[JobRecommendationResponse])
def recommend_jobs_endpoint(
    request: JobRecommendationRequest,
    db: Session = Depends(get_db),
) -> list[JobRecommendationResponse]:
    return recommend_jobs(db, request.skills, limit=request.limit)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job_endpoint(
    job_data: JobCreate,
    db: Session = Depends(get_db),
) -> JobResponse:
    return create_job(db, job_data)


@router.get("", response_model=list[JobResponse])
def list_jobs_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    return list_jobs(db, offset=offset, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
def get_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobResponse:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채용공고를 찾을 수 없습니다.",
        )
    return job
