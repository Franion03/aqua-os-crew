"""
Player Progress Review Crew.

Trigger: Every 2 weeks (or on-demand for a specific player).
Agents: Technical Coach → Physical Coach
Outputs: Individual progress reports, level-up recommendations, next-cycle drill focus.
"""

import logging

from crewai import Agent, Crew, Process, Task
from llm_config import model_for

from tools.player_db import get_roster_players, get_player_details, add_progress_log

logger = logging.getLogger(__name__)


# ── Agents ──────────────────────────────────────────────────────────────

technical_coach = Agent(
    role="Technical Head Coach",
    goal="Evaluate player technical progression and recommend level changes",
    backstory=(
        "Youth development specialist who has written water polo leveling "
        "rubrics for three national federations. You assess players against "
        "4 benchmark levels (Pups → Bronze → Silver → Gold) and provide "
        "specific, actionable feedback for each athlete."
    ),
    tools=[get_roster_players, get_player_details],
    allow_delegation=False,
    verbose=True,
    llm=model_for("technical"),
)

physical_coach = Agent(
    role="Physical Conditioning Coach",
    goal="Assess physical readiness and prescribe conditioning adjustments",
    backstory=(
        "Sports scientist who tracks swim benchmarks, lactate thresholds, "
        "and injury risk markers for youth aquatic athletes. You translate "
        "physical performance data into individualized conditioning plans."
    ),
    tools=[get_player_details],
    allow_delegation=False,
    verbose=True,
    llm=model_for("physical"),
)


# ── Crew Builder ────────────────────────────────────────────────────────

def build_progress_review_crew(player_id: int | None = None) -> Crew:
    """Assemble the progress review crew.

    Args:
        player_id: Optional specific player ID. If None, review all players.
    """

    if player_id is not None:
        review_scope = f"Review the single player with ID {player_id}"
    else:
        review_scope = "Review ALL players in the club roster"

    technical_assessment = Task(
        description=(
            f"{review_scope}. For each player, evaluate their current level "
            "(1-4) against the benchmarks for the NEXT level up. "
            "For each player, determine: "
            "(1) Are they ready to level up? (yes / almost / not yet) "
            "(2) What is the single most important skill gap blocking "
            "advancement? "
            "(3) Which 2 drills from the next level's rubric should they "
            "focus on in the coming 2 weeks? "
            "Output as a structured per-player report."
        ),
        agent=technical_coach,
        expected_output=(
            "Per-player assessment with level-up readiness, skill gaps, "
            "and recommended drills for the next 2 weeks."
        ),
    )

    physical_assessment = Task(
        description=(
            f"{review_scope}. For each player, assess their physical "
            "conditioning metrics (swimming stamina, vertical eggbeater "
            "duration). Identify: "
            "(1) Any injury risk indicators (e.g., shoulder asymmetry, "
            "low core stability scores). "
            "(2) Whether the player's current conditioning level supports "
            "their technical level. "
            "(3) One specific dryland or swim-set adjustment for the "
            "next training block. "
            "Output as structured notes appended to the technical report."
        ),
        agent=physical_coach,
        context=[technical_assessment],
        expected_output=(
            "Physical conditioning notes per player with injury risk flags "
            "and conditioning adjustments."
        ),
    )

    log_progress = Task(
        description=(
            "For any player identified as 'ready to level up', record a "
            "progress log entry using add_progress_log with the note "
            "format: 'Progress Review: Recommended promotion to Level X: "
            "[Level Name]. Key achievement: [brief detail].' "
            "Only log entries for players ready to advance."
        ),
        agent=technical_coach,
        tools=[add_progress_log],
        context=[technical_assessment],
        expected_output="Confirmation of progress log entries recorded.",
    )

    crew = Crew(
        agents=[technical_coach, physical_coach],
        tasks=[technical_assessment, physical_assessment, log_progress],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_progress_review(player_id: int | None = None) -> dict:
    """Run the progress review crew and return structured results."""
    crew = build_progress_review_crew(player_id=player_id)
    result = crew.kickoff()
    return {
        "crew_type": "progress_review",
        "player_id": player_id,
        "raw_output": str(result),
    }
