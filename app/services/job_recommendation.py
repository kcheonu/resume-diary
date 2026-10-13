from sqlalchemy.orm import Session

from app.schemas.job import JobRecommendationResponse, JobResponse
from app.services.job_repository import list_all_jobs


def recommend_jobs(
    db: Session,
    candidate_skills: list[str],
    *,
    limit: int = 20,
) -> list[JobRecommendationResponse]:
    normalized_candidate_skills = {
        skill.strip().casefold()
        for skill in candidate_skills
        if skill.strip()
    }
    recommendations: list[tuple[int, int, JobRecommendationResponse]] = []

    for job in list_all_jobs(db):
        unique_job_skills: dict[str, str] = {}
        for skill in job.skills:
            normalized_skill = skill.strip().casefold()
            if normalized_skill:
                unique_job_skills.setdefault(normalized_skill, skill.strip())

        if not unique_job_skills:
            continue

        matched_skills = [
            skill
            for normalized_skill, skill in unique_job_skills.items()
            if normalized_skill in normalized_candidate_skills
        ]
        if not matched_skills:
            continue

        match_score = round(100 * len(matched_skills) / len(unique_job_skills))
        recommendation = JobRecommendationResponse(
            job=JobResponse.model_validate(job),
            matched_skills=matched_skills,
            match_score=match_score,
        )
        recommendations.append((match_score, job.id, recommendation))

    recommendations.sort(key=lambda item: (-item[0], item[1]))
    return [recommendation for _, _, recommendation in recommendations[:limit]]
