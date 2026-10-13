from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models.schedule import ScheduleTask, StudyPlan
from app.schemas.schedule import (
    ScheduleReplanRequest,
    ScheduleTaskStatus,
    StudyPlanCreate,
)


def _spread_dates(start_date: date, end_date: date, count: int) -> list[date]:
    if count == 1:
        return [start_date]

    span_days = (end_date - start_date).days
    return [
        start_date + timedelta(days=round(span_days * index / (count - 1)))
        for index in range(count)
    ]


def create_study_plan(db: Session, plan_data: StudyPlanCreate) -> StudyPlan:
    plan = StudyPlan(
        goal=plan_data.goal,
        start_date=plan_data.start_date,
        end_date=plan_data.end_date,
    )
    dates = _spread_dates(plan_data.start_date, plan_data.end_date, len(plan_data.tasks))
    plan.tasks = [
        ScheduleTask(
            title=task.title,
            description=task.description,
            scheduled_date=scheduled_date,
            status=ScheduleTaskStatus.PENDING.value,
        )
        for task, scheduled_date in zip(plan_data.tasks, dates, strict=True)
    ]

    try:
        db.add(plan)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_study_plan(db, plan.id)


def get_study_plan(db: Session, plan_id: int) -> StudyPlan | None:
    return (
        db.query(StudyPlan)
        .options(selectinload(StudyPlan.tasks))
        .filter(StudyPlan.id == plan_id)
        .one_or_none()
    )


def update_task_status(
    db: Session,
    plan_id: int,
    task_id: int,
    status: ScheduleTaskStatus,
) -> ScheduleTask | None:
    task = (
        db.query(ScheduleTask)
        .filter(
            ScheduleTask.id == task_id,
            ScheduleTask.plan_id == plan_id,
        )
        .one_or_none()
    )
    if task is None:
        return None

    task.status = status.value
    try:
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise
    return task


def replan_study_plan(
    db: Session,
    plan_id: int,
    replan_data: ScheduleReplanRequest,
) -> StudyPlan | None:
    plan = get_study_plan(db, plan_id)
    if plan is None:
        return None

    pending_tasks = sorted(
        (task for task in plan.tasks if task.status == ScheduleTaskStatus.PENDING.value),
        key=lambda task: (task.scheduled_date, task.id),
    )
    dates = _spread_dates(
        replan_data.start_date,
        replan_data.end_date,
        len(pending_tasks),
    )
    for task, scheduled_date in zip(pending_tasks, dates, strict=True):
        task.scheduled_date = scheduled_date

    plan.start_date = replan_data.start_date
    plan.end_date = replan_data.end_date
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_study_plan(db, plan_id)
