"""Tests for AquaOS CrewAI microservice API endpoints."""

from unittest.mock import patch


def test_app_imports():
    from main import app
    assert app.title == "AquaOS CrewAI Microservice"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "aqua-os-crew"
    assert "crews_available" in data
    assert "timestamp" in data


def test_crew_types(client):
    resp = client.get("/crew/types")
    assert resp.status_code == 200
    data = resp.json()
    assert "crews" in data
    for crew in ("match_prep", "enrollment", "progress_review", "season_plan", "injury_response"):
        assert crew in data["crews"]


def test_crew_run_unknown_type(client):
    resp = client.post("/crew/run", json={"crew_type": "nonexistent", "params": {}})
    assert resp.status_code == 400
    assert "Unknown crew type" in resp.json()["detail"]


@patch("main._llm_provider", "none")
def test_crew_run_no_llm(client):
    resp = client.post("/crew/run", json={"crew_type": "match_prep", "params": {}})
    assert resp.status_code == 503
    assert "No LLM provider" in resp.json()["detail"]


@patch("main._llm_provider", "openrouter")
@patch("main.CREW_REGISTRY", {"match_prep": lambda **kw: {"result": "mocked"}})
def test_crew_run_success(client):
    resp = client.post("/crew/run", json={"crew_type": "match_prep", "params": {"opponent": "Team X"}})
    assert resp.status_code == 200
    assert resp.json() == {"result": "mocked"}


@patch("main._llm_provider", "openrouter")
@patch("main.CREW_REGISTRY", {"match_prep": lambda **kw: (_ for _ in ()).throw(RuntimeError("boom"))})
def test_crew_run_failure(client):
    resp = client.post("/crew/run", json={"crew_type": "match_prep", "params": {}})
    assert resp.status_code == 500
    assert "Crew failed" in resp.json()["detail"]


def test_notify_calendar_change(client):
    payload = {
        "series_name": "Training",
        "series_id": "abc",
        "summary": "1 event added",
        "added": [{"title": "Practice", "start": "2026-06-25T18:00"}],
        "removed": [],
        "modified": [],
        "timestamp": "2026-06-22T10:00:00Z",
    }
    resp = client.post("/notify/calendar-change", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "message_preview" in data


def test_notify_calendar_change_minimal(client):
    payload = {"series_name": "X", "series_id": "1", "summary": "test"}
    resp = client.post("/notify/calendar-change", json=payload)
    assert resp.status_code == 200
