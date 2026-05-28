# ── AquaOS Crews ────────────────────────────────────────────────────────
# CrewAI agent crew definitions for water polo club operations.
# Each crew is a standalone module that can be called independently.

from .match_prep import build_match_prep_crew, run_match_prep
from .enrollment import build_enrollment_crew, run_enrollment
from .progress_review import build_progress_review_crew, run_progress_review
from .season_plan import build_season_plan_crew, run_season_plan
from .injury_response import build_injury_response_crew, run_injury_response

# Registry: maps crew_type string → run function
CREW_REGISTRY = {
    "match_prep": run_match_prep,
    "enrollment": run_enrollment,
    "progress_review": run_progress_review,
    "season_plan": run_season_plan,
    "injury_response": run_injury_response,
}

__all__ = [
    "CREW_REGISTRY",
    "build_match_prep_crew",
    "build_enrollment_crew",
    "build_progress_review_crew",
    "build_season_plan_crew",
    "build_injury_response_crew",
    "run_match_prep",
    "run_enrollment",
    "run_progress_review",
    "run_season_plan",
    "run_injury_response",
]
