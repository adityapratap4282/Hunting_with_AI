from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import JobPost, JobScore, ResumeVersion
from app.schemas import RankingRequest, RankingResult
from app.services.logging_service import log_event
from app.services.ranking_service import compute_score

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.post("/score", response_model=list[RankingResult])
def score_jobs(payload: RankingRequest, db: Session = Depends(get_db)) -> list[RankingResult]:
    resume_version = db.query(ResumeVersion).get(payload.resume_version_id)
    if not resume_version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    jobs_query = db.query(JobPost)
    if payload.job_post_ids:
        jobs_query = jobs_query.filter(JobPost.id.in_(payload.job_post_ids))
    jobs = jobs_query.all()

    results: list[RankingResult] = []
    for job in jobs:
        existing = (
            db.query(JobScore)
            .filter(JobScore.job_post_id == job.id, JobScore.resume_version_id == resume_version.id)
            .one_or_none()
        )
        if existing:
            score = existing
        else:
            score = compute_score(db, resume_version, job)
            db.add(score)
            db.commit()
            db.refresh(score)
        results.append(
            RankingResult(
                job_post_id=job.id,
                score=score.score,
                title_score=score.title_score,
                skill_score=score.skill_score,
                freshness_score=score.freshness_score,
                llm_score=score.llm_score,
                explanation=score.explanation,
                gap_summary=score.gap_summary or "",
            )
        )
    log_event(
        db,
        event_type="ranking.completed",
        entity_type="resume_version",
        entity_id=str(resume_version.id),
        message=f"Scored {len(results)} job(s)",
    )
    return sorted(results, key=lambda item: item.score, reverse=True)
