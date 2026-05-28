"""
AquaOS CrewAI Microservice — Standalone FastAPI wrapper for water polo agent crews.

Usage:
    pip install -r requirements.txt
    cp .env.example .env  # fill in your API keys
    uvicorn main:app --port 8001
"""

import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── LLM Provider Detection ──────────────────────────────────────────
_openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
_gemini_key = os.getenv("GEMINI_API_KEY", "")

_llm_provider: str
_llm_default_model: str

if _openrouter_key:
    _llm_provider = "openrouter"
    _llm_default_model = "openrouter/google/gemini-2.0-flash-001"
    os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    os.environ.setdefault("OPENAI_API_KEY", _openrouter_key)
    os.environ.setdefault("OR_SITE_URL", "https://github.com/franion03/aqua-os")
    os.environ.setdefault("OR_APP_NAME", "AquaOS")
elif _gemini_key:
    _llm_provider = "gemini"
    _llm_default_model = "gemini-2.0-flash"
    os.environ.setdefault("OPENAI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/")
    os.environ.setdefault("OPENAI_API_KEY", _gemini_key)
else:
    _llm_provider = "none"
    _llm_default_model = "none"

# ── CrewAI Imports ──────────────────────────────────────────────────
from crews import CREW_REGISTRY

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("aquaos-crew")

# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="AquaOS CrewAI Microservice", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CREW_TYPES = sorted(CREW_REGISTRY.keys()) if CREW_REGISTRY else []

# ── Health ──────────────────────────────────────────────────────────
@app.get("/health")
def health():
    try:
        from importlib.metadata import version
        cv = version("crewai")
    except Exception:
        cv = "unknown"
    return {
        "status": "ok",
        "service": "aqua-os-crew",
        "llm_provider": _llm_provider,
        "llm_default_model": _llm_default_model,
        "crews_available": CREW_TYPES,
        "crewai_version": cv,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Crew Types ──────────────────────────────────────────────────────

CREW_DESCRIPTIONS = {
    "match_prep": {
        "description": "Prepare for an upcoming match",
        "params": {"opponent": "str", "match_date": "YYYY-MM-DD", "pool": "str (optional)"},
    },
    "enrollment": {
        "description": "Monthly enrollment campaign",
        "params": {"season": "str (optional)", "camp_start": "YYYY-MM-DD (optional)"},
    },
    "progress_review": {
        "description": "Review player progress (all or single)",
        "params": {"player_id": "int (optional, omit for all)"},
    },
    "season_plan": {
        "description": "Full-season planning",
        "params": {"season_name": "str (optional)", "season_start": "YYYY-MM-DD (optional)", "season_end": "YYYY-MM-DD (optional)"},
    },
    "injury_response": {
        "description": "Respond to a player injury",
        "params": {"player_id": "int (required)", "injury_description": "str (required)", "severity": "mild|moderate|severe"},
    },
}

@app.get("/crew/types")
def crew_types():
    return {"crews": CREW_DESCRIPTIONS}

# ── Crew Runner ─────────────────────────────────────────────────────

class CrewRunRequest(BaseModel):
    crew_type: str
    params: dict = {}

@app.post("/crew/run")
def run_crew(req: CrewRunRequest):
    if req.crew_type not in CREW_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown crew type '{req.crew_type}'. Options: {CREW_TYPES}")
    if _llm_provider == "none":
        raise HTTPException(status_code=503, detail="No LLM provider configured. Set OPENROUTER_API_KEY or GEMINI_API_KEY.")

    run_fn = CREW_REGISTRY[req.crew_type]
    logger.info("Starting crew '%s' with params: %s", req.crew_type, req.params)
    try:
        result = run_fn(**req.params)
    except Exception as exc:
        logger.exception("Crew '%s' failed", req.crew_type)
        raise HTTPException(status_code=500, detail=f"Crew failed: {exc}")
    return result


# ── Notification Webhook ─────────────────────────────────────────────

class CalendarChangePayload(BaseModel):
    series_name: str
    series_id: str
    summary: str
    added: list[dict] = []
    removed: list[dict] = []
    modified: list[dict] = []
    timestamp: str = ""

@app.post("/notify/calendar-change")
def notify_calendar_change(payload: CalendarChangePayload):
    """Receive calendar change events from aqua-os-calendar and dispatch notifications.

    Dispatches through available channels:
      - Telegram channel (TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID)
      - Log output (always, for observability)
    """
    message = _format_calendar_message(payload)
    results = {"channels": {}}

    # ── Telegram ──
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHANNEL_ID"):
        try:
            import httpx
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = httpx.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
            results["channels"]["telegram"] = "sent"
            logger.info("Notification → Telegram channel %s", chat_id)
        except Exception as exc:
            results["channels"]["telegram"] = f"failed: {exc}"
            logger.error("Telegram notification failed: %s", exc)
    else:
        results["channels"]["telegram"] = "not configured"

    # ── Log ──
    logger.info(
        "📅 Calendar Change — %s: %s (%d added, %d removed, %d modified)",
        payload.series_name, payload.summary,
        len(payload.added), len(payload.removed), len(payload.modified)
    )
    results["channels"]["log"] = "ok"

    return {
        "status": "ok",
        "message_preview": message[:300],
        **results,
    }


def _format_calendar_message(payload: CalendarChangePayload) -> str:
    """Format a calendar change into a human-readable Telegram/email message."""
    lines = [
        f"📅 <b>Calendar Update — {payload.series_name}</b>",
        f"<i>{payload.summary}</i>",
        "",
    ]

    if payload.added:
        lines.append("🆕 <b>New events:</b>")
        for e in payload.added:
            lines.append(f"  • {e.get('title', '?')} — {e.get('start', '?')[:16]}")
        lines.append("")

    if payload.removed:
        lines.append("❌ <b>Cancelled:</b>")
        for e in payload.removed:
            lines.append(f"  • {e.get('title', '?')}")
        lines.append("")

    if payload.modified:
        lines.append("✏️ <b>Modified:</b>")
        for e in payload.modified:
            lines.append(f"  • {e.get('title', '?')} — {e.get('start', '?')[:16]}")
        lines.append("")

    lines.append(f"<i>⏱ {payload.timestamp[:19]}</i>")
    return "\n".join(lines)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AquaOS CrewAI microservice on :8001")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
