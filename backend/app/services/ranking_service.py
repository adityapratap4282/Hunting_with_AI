from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import JobPost, JobScore, ResumeVersion, SkillDictionaryTerm


@dataclass
class ScoreBreakdown:
    title_score: float
    skill_score: float
    freshness_score: float
    llm_score: float

    @property
    def total(self) -> float:
        return round(self.title_score + self.skill_score + self.freshness_score + self.llm_score, 2)


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9+#.]+", text.lower()))


FRESHNESS_MAP = {
    "24h": 15,
    "7d": 10,
    "30d": 5,
}


def extract_priority_terms(db: Session) -> list[tuple[str, float]]:
    terms = db.query(SkillDictionaryTerm).all()
    return [(term.canonical_name.lower(), term.default_weight) for term in terms]


def compute_score(db: Session, resume_version: ResumeVersion, job_post: JobPost) -> JobScore:
    resume_tokens = tokenize(resume_version.source_text)
    job_tokens = tokenize(job_post.jd_text)
    title_tokens = tokenize(job_post.title)

    title_score = 20 if title_tokens & resume_tokens else 5

    priority_terms = extract_priority_terms(db)
    matched_weights = sum(weight for term, weight in priority_terms if term in resume_tokens and term in job_tokens)
    total_weights = sum(weight for _, weight in priority_terms) or 1
    skill_score = round((matched_weights / total_weights) * 45, 2)

    freshness_score = FRESHNESS_MAP.get((job_post.freshness_bucket or "").lower(), 3)

    overlap_ratio = len(resume_tokens & job_tokens) / max(len(job_tokens), 1)
    llm_score = round(min(overlap_ratio * 20, 20), 2)

    missing_terms = [term for term, _ in priority_terms if term in job_tokens and term not in resume_tokens][:5]
    explanation = (
        f"Hybrid scoring blended title overlap, weighted skill matches, freshness, and a low-cost semantic proxy. "
        f"Resume/job token overlap was {overlap_ratio:.1%}."
    )
    gap_summary = (
        "Top gaps to address: " + ", ".join(missing_terms)
        if missing_terms
        else "No obvious skill gaps were detected from the current dictionary."
    )

    breakdown = ScoreBreakdown(
        title_score=title_score,
        skill_score=skill_score,
        freshness_score=freshness_score,
        llm_score=llm_score,
    )

    return JobScore(
        job_post_id=job_post.id,
        resume_version_id=resume_version.id,
        score=breakdown.total,
        title_score=breakdown.title_score,
        skill_score=breakdown.skill_score,
        freshness_score=breakdown.freshness_score,
        llm_score=breakdown.llm_score,
        explanation=explanation,
        gap_summary=gap_summary,
        model_name="hybrid-rules+chatgpt-ready",
        score_breakdown_json=json.dumps(breakdown.__dict__),
    )
