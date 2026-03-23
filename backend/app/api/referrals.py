from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Company, OutreachMessage, ReferralTarget
from app.schemas import ReferralTargetCreate, ReferralTargetRead
from app.services.logging_service import log_event

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("", response_model=list[ReferralTargetRead])
def list_targets(db: Session = Depends(get_db)) -> list[ReferralTarget]:
    return db.query(ReferralTarget).options(selectinload(ReferralTarget.company), selectinload(ReferralTarget.messages)).all()


@router.post("", response_model=ReferralTargetRead, status_code=201)
def create_target(payload: ReferralTargetCreate, db: Session = Depends(get_db)) -> ReferralTarget:
    company = db.query(Company).filter(Company.name == payload.company_name).one_or_none()
    if not company:
        company = Company(name=payload.company_name)
        db.add(company)
        db.flush()

    target = ReferralTarget(
        company_id=company.id,
        full_name=payload.full_name,
        title=payload.title,
        linkedin_url=payload.linkedin_url,
        lead_source=payload.lead_source,
        notes=payload.notes,
        status="identified",
    )
    db.add(target)
    db.flush()

    draft = OutreachMessage(
        referral_target_id=target.id,
        message_type="connection_request",
        status="draft",
        body=(
            f"Hi {payload.full_name}, I found your profile while researching {payload.company_name}. "
            "I would love to connect and learn more about your team."
        ),
    )
    db.add(draft)
    db.commit()
    db.refresh(target)
    log_event(
        db,
        event_type="referral.created",
        entity_type="referral_target",
        entity_id=str(target.id),
        message=target.full_name,
    )
    return db.query(ReferralTarget).options(selectinload(ReferralTarget.company), selectinload(ReferralTarget.messages)).get(target.id)
