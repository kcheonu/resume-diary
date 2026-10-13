from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ScheduleTaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class ScheduleTaskInput(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""


class StudyPlanCreate(BaseModel):
    goal: str = Field(min_length=1)
    start_date: date
    end_date: date
    tasks: list[ScheduleTaskInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
        return self


class ScheduleTaskResponse(BaseModel):
    id: int
    title: str
    description: str
    scheduled_date: date
    status: ScheduleTaskStatus

    model_config = {"from_attributes": True}


class StudyPlanResponse(BaseModel):
    id: int
    goal: str
    start_date: date
    end_date: date
    tasks: list[ScheduleTaskResponse]

    model_config = {"from_attributes": True}


class ScheduleTaskUpdate(BaseModel):
    status: ScheduleTaskStatus


class ScheduleReplanRequest(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
        return self
