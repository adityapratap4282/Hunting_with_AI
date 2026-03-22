from fastapi import APIRouter

from app.schemas import SettingsRead

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def get_settings() -> SettingsRead:
    return SettingsRead(
        ai_provider="OpenAI (ChatGPT) + hybrid rules",
        model_name="gpt-4.1-mini or similar cost-aware default",
        routing_notes=[
            "Use rules-based ranking for title, skills, freshness, and dedupe.",
            "Reserve LLM calls for JD summarization, rewrite suggestions, and referral drafts.",
            "Keep browser-extension capture in phase 2 to reduce maintenance risk.",
        ],
    )
