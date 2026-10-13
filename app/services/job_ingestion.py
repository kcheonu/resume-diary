def normalize_job(raw: dict, source: str) -> dict:
    """외부 공고 데이터를 내부 공통 형식으로 변환한다."""

    return {
        "source": source,
        "external_id": raw.get("external_id"),
        "company": raw["company"].strip(),
        "title": raw["title"].strip(),
        "description": raw.get("description", ""),
        "url": raw["url"],
        "deadline": raw.get("deadline"),
        "skills": raw.get("skills", []),
    }