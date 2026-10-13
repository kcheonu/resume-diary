from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schedule import (
    ScheduleReplanRequest,
    ScheduleTaskResponse,
    ScheduleTaskUpdate,
    StudyPlanCreate,
    StudyPlanResponse,
)
from app.services.schedule_planner import (
    create_study_plan,
    get_study_plan,
    replan_study_plan,
    update_task_status,
)


router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED)
def create_study_plan_endpoint(
    plan_data: StudyPlanCreate,
    db: Session = Depends(get_db),
) -> StudyPlanResponse:
    return create_study_plan(db, plan_data)


@router.get("/{plan_id}", response_model=StudyPlanResponse)
def get_study_plan_endpoint(
    plan_id: int,
    db: Session = Depends(get_db),
) -> StudyPlanResponse:
    plan = get_study_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="준비 일정을 찾을 수 없습니다.",
        )
    return plan


@router.patch(
    "/{plan_id}/tasks/{task_id}",
    response_model=ScheduleTaskResponse,
)
def update_schedule_task_endpoint(
    plan_id: int,
    task_id: int,
    task_update: ScheduleTaskUpdate,
    db: Session = Depends(get_db),
) -> ScheduleTaskResponse:
    task = update_task_status(db, plan_id, task_id, task_update.status)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정 항목을 찾을 수 없습니다.",
        )
    return task


@router.post("/{plan_id}/replan", response_model=StudyPlanResponse)
def replan_study_plan_endpoint(
    plan_id: int,
    replan_data: ScheduleReplanRequest,
    db: Session = Depends(get_db),
) -> StudyPlanResponse:
    plan = replan_study_plan(db, plan_id, replan_data)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="준비 일정을 찾을 수 없습니다.",
        )
    return plan
