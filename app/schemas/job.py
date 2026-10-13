from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


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


class JobRecommendationRequest(BaseModel):
    skills: list[str] = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class JobRecommendationResponse(BaseModel):
    job: JobResponse
    matched_skills: list[str]
    match_score: int = Field(ge=1, le=100)