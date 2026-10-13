from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class JobCreate(BaseModel):
    source: str
    external_id: str | None = None

    company: str
    title: str
    description: str = ""

    url: HttpUrl
    deadline: datetime | None = None

    skills: list[str] = Field(default_factory=list)


class JobResponse(JobCreate):
    id: int

    class Config:
        from_attributes = True