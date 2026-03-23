from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Company, JobPost
from app.schemas import JobPostCreate, JobPostRead
from app.services.logging_service import log_event

router = APIRouter(prefix="/jobs", tags=["jobs"])


def build_dedupe_key(title: str, company_name: str | None, source_url: str | None) -> str:
    raw = f"{title.lower()}::{(company_name or '').lower()}::{source_url or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


@router.get("", response_model=list[JobPostRead])
def list_jobs(db: Session = Depends(get_db)) -> list[JobPost]:
    return db.query(JobPost).options(selectinload(JobPost.company)).all()


@router.post("", response_model=JobPostRead, status_code=201)
def create_job(payload: JobPostCreate, db: Session = Depends(get_db)) -> JobPost:
    company = None
    if payload.company_name:
        company = db.query(Company).filter(Company.name == payload.company_name).one_or_none()
        if not company:
            company = Company(name=payload.company_name)
            db.add(company)
            db.flush()

    dedupe_key = build_dedupe_key(payload.title, payload.company_name, payload.source_url)
    job = db.query(JobPost).filter(JobPost.dedupe_key == dedupe_key).one_or_none()
    if job:
        return job

    job = JobPost(
        company_id=company.id if company else None,
        title=payload.title,
        source=payload.source,
        source_url=payload.source_url,
        location=payload.location,
        employment_type=payload.employment_type,
        jd_text=payload.jd_text,
        source_posted_at_raw=payload.source_posted_at_raw,
        freshness_bucket=payload.freshness_bucket,
        dedupe_key=dedupe_key,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    log_event(db, event_type="job.ingested", entity_type="job_post", entity_id=str(job.id), message=job.title)
    return db.query(JobPost).options(selectinload(JobPost.company)).get(job.id)
