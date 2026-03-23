from sqlalchemy.orm import Session

from app.models import SkillDictionaryAlias, SkillDictionaryTerm

SEED_TERMS = [
    ("python", "language", "data", 1.0, ["py"]),
    ("sql", "querying", "data", 1.0, ["postgresql", "mysql"]),
    ("power bi", "bi", "analytics", 0.8, ["powerbi"]),
    ("tableau", "bi", "analytics", 0.8, []),
    ("airflow", "orchestration", "data-engineering", 0.9, []),
    ("excel", "analysis", "analytics", 0.7, ["spreadsheets"]),
    ("machine learning", "ml", "data-science", 0.9, ["ml"]),
]


def seed_dictionary(db: Session) -> None:
    if db.query(SkillDictionaryTerm).count() > 0:
        return

    for canonical_name, category, role_family, weight, aliases in SEED_TERMS:
        term = SkillDictionaryTerm(
            canonical_name=canonical_name,
            category=category,
            role_family=role_family,
            default_weight=weight,
        )
        db.add(term)
        db.flush()
        for alias in aliases:
            db.add(SkillDictionaryAlias(term_id=term.id, alias=alias))
    db.commit()
