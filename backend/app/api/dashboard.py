from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import JobPost, ReferralTarget, Resume
from app.schemas import DashboardRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardRead:
    resumes = (
        db.query(Resume)
        .options(selectinload(Resume.versions))
        .order_by(desc(Resume.updated_at))
        .limit(5)
        .all()
    )
    jobs = (
        db.query(JobPost)
        .options(selectinload(JobPost.company))
        .order_by(desc(JobPost.updated_at))
        .limit(8)
        .all()
    )
    referrals = (
        db.query(ReferralTarget)
        .options(selectinload(ReferralTarget.company), selectinload(ReferralTarget.messages))
        .order_by(desc(ReferralTarget.updated_at))
        .limit(5)
        .all()
    )
    metrics = {
        "resume_count": db.query(Resume).count(),
        "job_count": db.query(JobPost).count(),
        "referral_count": db.query(ReferralTarget).count(),
    }
    return DashboardRead(metrics=metrics, latest_resumes=resumes, latest_jobs=jobs, referral_queue=referrals)
