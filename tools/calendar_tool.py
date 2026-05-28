"""
Calendar Tool — CrewAI-compatible.

Talks to the aqua-os-calendar microservice (C# .NET) to:
  - Fetch upcoming events for match preparation
  - Schedule training sessions and matches as manual events

Env vars:
    CALENDAR_SERVICE_URL — base URL of the calendar service (default: http://localhost:8082)
    CALENDAR_API_KEY     — JWT token for authenticated writes (optional, only needed for writes)
"""

import json
import logging
import os
from datetime import datetime, timedelta

import requests
from crewai.tools import tool

logger = logging.getLogger(__name__)

CALENDAR_URL = os.getenv("CALENDAR_SERVICE_URL", "http://localhost:8082")
CALENDAR_API_KEY = os.getenv("CALENDAR_API_KEY", "")


def _headers():
    h = {"Content-Type": "application/json"}
    if CALENDAR_API_KEY:
        h["Authorization"] = f"Bearer {CALENDAR_API_KEY}"
    return h


@tool("get_upcoming_events")
def get_upcoming_events(series_id: str = "", days_ahead: int = 14) -> str:
    """Fetch upcoming events from the club calendar.

    Args:
        series_id: Calendar series ID (leave empty to use the default competition calendar).
        days_ahead: Number of days to look ahead (default: 14).

    Returns:
        JSON list of upcoming events with title, start/end, location, and category.
    """
    sid = series_id or os.getenv("CALENDAR_DEFAULT_SERIES", "")
    if not sid:
        return json.dumps({"error": "No series_id provided and CALENDAR_DEFAULT_SERIES not set."})

    try:
        url = f"{CALENDAR_URL}/api/calendar/{sid}/events?upcoming=true"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        events = resp.json()

        # Filter to the requested window
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)
        filtered = [e for e in events if _parse_dt(e.get("start")) <= cutoff]

        logger.info("get_upcoming_events → %d events in next %d days", len(filtered), days_ahead)
        return json.dumps(filtered, indent=2, default=str)
    except requests.RequestException as e:
        logger.error("get_upcoming_events failed: %s", e)
        return json.dumps({"error": str(e)})


@tool("get_next_match")
def get_next_match(series_id: str = "") -> str:
    """Get the next competitive match from the calendar.

    Args:
        series_id: Calendar series ID (leave empty to use default).

    Returns:
        JSON with match details (title, start, location, opponent).
    """
    sid = series_id or os.getenv("CALENDAR_DEFAULT_SERIES", "")
    if not sid:
        return json.dumps({"error": "No series_id provided."})

    try:
        url = f"{CALENDAR_URL}/api/calendar/{sid}/events?upcoming=true"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        events = resp.json()

        # Find first match or polled event
        matches = [e for e in events if e.get("category") in ("match", "polled")]
        if not matches:
            return json.dumps({"info": "No upcoming matches found."})

        match = matches[0]
        logger.info("get_next_match → %s on %s", match.get("title"), match.get("start"))
        return json.dumps(match, indent=2, default=str)
    except requests.RequestException as e:
        logger.error("get_next_match failed: %s", e)
        return json.dumps({"error": str(e)})


@tool("schedule_match")
def schedule_match(
    date_str: str,
    time_str: str,
    opponent: str,
    pool: str,
    notes: str = "",
    series_id: str = "",
) -> str:
    """Schedule a competitive match on the club calendar via aqua-os-calendar.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD).
        time_str: Time in 24h format (HH:MM).
        opponent: Opposing club name.
        pool: Pool name or location (home/away).
        notes: Additional match notes.
        series_id: Calendar series ID (optional, uses default if empty).

    Returns:
        JSON confirmation with the created event.
    """
    sid = series_id or os.getenv("CALENDAR_DEFAULT_SERIES", "")
    if not sid:
        return json.dumps({"error": "No series_id provided and CALENDAR_DEFAULT_SERIES not set."})

    try:
        start_dt = datetime.fromisoformat(f"{date_str}T{time_str}:00")
    except ValueError:
        return json.dumps({"error": f"Invalid date/time: {date_str} {time_str}"})

    payload = {
        "title": f"Match vs {opponent}",
        "start": start_dt.isoformat(),
        "end": (start_dt + timedelta(hours=2)).isoformat(),
        "location": pool,
        "description": notes or f"Match against {opponent} at {pool}",
        "category": "match",
    }

    try:
        url = f"{CALENDAR_URL}/api/calendar/{sid}/events"
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        result = resp.json()
        logger.info("schedule_match → created event %s", result.get("uid"))
        return json.dumps({"status": "created", "event": result}, indent=2, default=str)
    except requests.RequestException as e:
        logger.error("schedule_match failed: %s", e)
        return json.dumps({"error": str(e)})


@tool("schedule_training")
def schedule_training(
    date_str: str,
    time_str: str,
    pool: str,
    notes: str,
    series_id: str = "",
) -> str:
    """Schedule a training session on the club calendar via aqua-os-calendar.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD).
        time_str: Time in 24h format (HH:MM).
        pool: Pool name or location.
        notes: Session description, drills, or coaching notes.
        series_id: Calendar series ID (optional, uses default if empty).

    Returns:
        JSON confirmation with the created event.
    """
    sid = series_id or os.getenv("CALENDAR_DEFAULT_SERIES", "")
    if not sid:
        return json.dumps({"error": "No series_id provided and CALENDAR_DEFAULT_SERIES not set."})

    try:
        start_dt = datetime.fromisoformat(f"{date_str}T{time_str}:00")
    except ValueError:
        return json.dumps({"error": f"Invalid date/time: {date_str} {time_str}"})

    payload = {
        "title": f"Training Session",
        "start": start_dt.isoformat(),
        "end": (start_dt + timedelta(hours=1, minutes=30)).isoformat(),
        "location": pool,
        "description": notes,
        "category": "training",
    }

    try:
        url = f"{CALENDAR_URL}/api/calendar/{sid}/events"
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        result = resp.json()
        logger.info("schedule_training → created event %s", result.get("uid"))
        return json.dumps({"status": "created", "event": result}, indent=2, default=str)
    except requests.RequestException as e:
        logger.error("schedule_training failed: %s", e)
        return json.dumps({"error": str(e)})


def _parse_dt(val):
    """Safely parse ISO datetime string, return max datetime on failure."""
    if not val:
        return datetime.max
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.max
