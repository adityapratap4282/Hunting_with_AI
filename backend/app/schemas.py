from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    name: str
    website: str | None = None
    industry: str | None = None


class CompanyRead(CompanyBase):
    id: int

    class Config:
        from_attributes = True


class ResumeVersionCreate(BaseModel):
    version_label: str
    source_text: str


class ResumeCreate(BaseModel):
    name: str
    summary: str | None = None
    initial_version: ResumeVersionCreate


class ResumeVersionRead(BaseModel):
    id: int
    version_label: str
    source_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeRead(BaseModel):
    id: int
    name: str
    summary: str | None = None
    versions: list[ResumeVersionRead] = []

    class Config:
        from_attributes = True


class JobPostCreate(BaseModel):
    title: str
    company_name: str | None = None
    source: str = "manual"
    source_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    jd_text: str
    source_posted_at_raw: str | None = None
    freshness_bucket: str | None = None


class JobPostRead(BaseModel):
    id: int
    title: str
    source: str
    source_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    jd_text: str
    freshness_bucket: str | None = None
    dedupe_key: str
    company: CompanyRead | None = None

    class Config:
        from_attributes = True


class RankingRequest(BaseModel):
    resume_version_id: int
    job_post_ids: list[int] = Field(default_factory=list)


class RankingResult(BaseModel):
    job_post_id: int
    score: float
    title_score: float
    skill_score: float
    freshness_score: float
    llm_score: float
    explanation: str
    gap_summary: str


class ReferralTargetCreate(BaseModel):
    company_name: str
    full_name: str
    title: str | None = None
    linkedin_url: str | None = None
    lead_source: str | None = None
    notes: str | None = None


class OutreachMessageRead(BaseModel):
    id: int
    message_type: str
    body: str
    status: str
    reminder_at: str | None = None

    class Config:
        from_attributes = True


class ReferralTargetRead(BaseModel):
    id: int
    status: str
    full_name: str
    title: str | None = None
    linkedin_url: str | None = None
    lead_source: str | None = None
    notes: str | None = None
    company: CompanyRead
    messages: list[OutreachMessageRead] = []

    class Config:
        from_attributes = True


class SettingsRead(BaseModel):
    ai_provider: str
    model_name: str
    routing_notes: list[str]


class DashboardRead(BaseModel):
    metrics: dict[str, Any]
    latest_resumes: list[ResumeRead]
    latest_jobs: list[JobPostRead]
    referral_queue: list[ReferralTargetRead]
