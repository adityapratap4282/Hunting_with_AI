from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Resume, ResumeVersion
from app.schemas import ResumeCreate, ResumeRead
from app.services.logging_service import log_event

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("", response_model=list[ResumeRead])
def list_resumes(db: Session = Depends(get_db)) -> list[Resume]:
    return db.query(Resume).options(selectinload(Resume.versions)).all()


@router.post("", response_model=ResumeRead, status_code=201)
def create_resume(payload: ResumeCreate, db: Session = Depends(get_db)) -> Resume:
    resume = Resume(name=payload.name, summary=payload.summary)
    db.add(resume)
    db.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_label=payload.initial_version.version_label,
        source_text=payload.initial_version.source_text,
    )
    db.add(version)
    db.commit()
    db.refresh(resume)
    log_event(db, event_type="resume.created", entity_type="resume", entity_id=str(resume.id), message=resume.name)
    return db.query(Resume).options(selectinload(Resume.versions)).get(resume.id)


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> Resume:
    resume = db.query(Resume).options(selectinload(Resume.versions)).get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
