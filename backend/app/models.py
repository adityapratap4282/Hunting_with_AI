from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    jobs: Mapped[list[JobPost]] = relationship(back_populates="company")
    referral_targets: Mapped[list[ReferralTarget]] = relationship(back_populates="company")


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    versions: Mapped[list[ResumeVersion]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class ResumeVersion(TimestampMixin, Base):
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    version_label: Mapped[str] = mapped_column(String(120))
    source_text: Mapped[str] = mapped_column(Text)
    structured_profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume: Mapped[Resume] = relationship(back_populates="versions")
    scores: Mapped[list[JobScore]] = relationship(back_populates="resume_version")


class JobPost(TimestampMixin, Base):
    __tablename__ = "job_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text)
    source_posted_at_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    freshness_bucket: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    company: Mapped[Company | None] = relationship(back_populates="jobs")
    scores: Mapped[list[JobScore]] = relationship(back_populates="job_post", cascade="all, delete-orphan")


class JobScore(TimestampMixin, Base):
    __tablename__ = "job_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_post_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id", ondelete="CASCADE"))
    resume_version_id: Mapped[int] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(Float)
    title_score: Mapped[float] = mapped_column(Float, default=0)
    skill_score: Mapped[float] = mapped_column(Float, default=0)
    freshness_score: Mapped[float] = mapped_column(Float, default=0)
    llm_score: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[str] = mapped_column(Text)
    gap_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(120), default="gpt-hybrid-placeholder")
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_post: Mapped[JobPost] = relationship(back_populates="scores")
    resume_version: Mapped[ResumeVersion] = relationship(back_populates="scores")


class ReferralTarget(TimestampMixin, Base):
    __tablename__ = "referral_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    full_name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(60), default="identified")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[Company] = relationship(back_populates="referral_targets")
    messages: Mapped[list[OutreachMessage]] = relationship(back_populates="target", cascade="all, delete-orphan")


class OutreachMessage(TimestampMixin, Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referral_target_id: Mapped[int] = mapped_column(ForeignKey("referral_targets.id", ondelete="CASCADE"))
    message_type: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="draft")
    reminder_at: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target: Mapped[ReferralTarget] = relationship(back_populates="messages")


class SkillDictionaryTerm(TimestampMixin, Base):
    __tablename__ = "skill_dictionary_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role_family: Mapped[str | None] = mapped_column(String(80), nullable=True)
    default_weight: Mapped[float] = mapped_column(Float, default=1.0)
    aliases: Mapped[list[SkillDictionaryAlias]] = relationship(back_populates="term", cascade="all, delete-orphan")


class SkillDictionaryAlias(TimestampMixin, Base):
    __tablename__ = "skill_dictionary_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("skill_dictionary_terms.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(120), index=True)
    term: Mapped[SkillDictionaryTerm] = relationship(back_populates="aliases")


class ActivityLog(TimestampMixin, Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
