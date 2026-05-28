"""
Season Planning Crew.

Trigger: Pre-season (once per year or on-demand).
Agents: Technical Coach → Physical Coach → Marketing → Tactical Analyst
Outputs: Full-season training calendar, tournament schedule, budget estimate.
"""

import logging

from crewai import Agent, Crew, Process, Task
from llm_config import model_for

from tools.player_db import get_roster_players
from tools.calendar_tool import schedule_training, schedule_match

logger = logging.getLogger(__name__)


# ── Agents ──────────────────────────────────────────────────────────────

technical_coach = Agent(
    role="Technical Head Coach",
    goal="Design the seasonal training macrocycle and weekly microcycles",
    backstory=(
        "Periodization expert who has planned 10+ competitive seasons for "
        "youth water polo clubs. You structure training across pre-season, "
        "competition phase, taper, and off-season blocks with clear "
        "technical objectives for each phase."
    ),
    tools=[get_roster_players, schedule_training],
    allow_delegation=False,
    verbose=True,
    llm=model_for("technical"),
)

physical_coach = Agent(
    role="Physical Conditioning Coach",
    goal="Integrate conditioning peaks into the training macrocycle",
    backstory=(
        "Sports scientist who aligns swim conditioning blocks with the "
        "technical calendar. You ensure players peak physically for "
        "regional tournaments and avoid overtraining in youth athletes."
    ),
    tools=[schedule_training],
    allow_delegation=False,
    verbose=True,
    llm=model_for("physical"),
)

marketing_agent = Agent(
    role="Marketing & Communications Director",
    goal="Plan parent communication calendar and budget",
    backstory=(
        "Club operations manager who handles tournament registrations, "
        "travel logistics, and the season budget. You produce a "
        "parent-friendly season overview and cost estimate."
    ),
    tools=[get_roster_players],
    allow_delegation=False,
    verbose=True,
    llm=model_for("marketing"),
)

tactical_analyst = Agent(
    role="Tactical Analyst & Scout",
    goal="Identify tournament targets and competitive objectives",
    backstory=(
        "Competition strategist who maps out the regional tournament "
        "calendar and sets realistic competitive objectives for each "
        "age group based on squad composition."
    ),
    tools=[schedule_match],
    allow_delegation=False,
    verbose=True,
    llm=model_for("tactical"),
)


# ── Crew Builder ────────────────────────────────────────────────────────

def build_season_plan_crew(
    season_name: str = "2026-2027",
    season_start: str = "2026-09-01",
    season_end: str = "2027-06-15",
) -> Crew:
    """Assemble the season planning crew.

    Args:
        season_name: Season identifier (e.g., "2026-2027").
        season_start: Season start date (ISO format).
        season_end: Season end date (ISO format).
    """

    training_calendar = Task(
        description=(
            f"Design the complete training macrocycle for the {season_name} "
            f"season ({season_start} to {season_end}). Structure it in 4 "
            "phases: (1) Pre-Season Foundation (6 weeks) — focus on swim "
            "conditioning + fundamental skills, (2) Competition Phase 1 "
            "(12 weeks) — tactical systems + match preparation, "
            "(3) Competition Phase 2 (12 weeks) — peak performance + "
            "tournament readiness, (4) Taper & Transition (4 weeks) — "
            "recovery + off-season recommendations. "
            "For each phase, specify: weekly training frequency, key "
            "technical objectives, and milestone assessments. "
            "Output as a structured seasonal calendar."
        ),
        agent=technical_coach,
        expected_output=(
            "4-phase training macrocycle with weekly objectives, training "
            "frequency, and milestone assessments."
        ),
    )

    conditioning_plan = Task(
        description=(
            f"Align the physical conditioning plan with the {season_name} "
            "training calendar. For each phase, define: (1) swim set focus "
            "(e.g., aerobic base, lactate threshold, speed/power), "
            "(2) dryland emphasis (e.g., mobility, strength, plyometrics), "
            "(3) key conditioning benchmarks to test at phase transitions. "
            "Ensure the plan prevents overtraining in U12 and U14 athletes."
        ),
        agent=physical_coach,
        context=[training_calendar],
        expected_output=(
            "Phase-aligned conditioning plan with swim set focus, dryland "
            "emphasis, and benchmark tests."
        ),
    )

    tournament_plan = Task(
        description=(
            f"Identify and schedule the key tournaments for the {season_name} "
            "season. Assume a typical regional youth calendar: 2 pre-season "
            "friendly tournaments, 4 regular-season tournaments, 1 regional "
            "championship. Schedule them at realistic intervals (every 6-8 "
            "weeks during competition phases). For each, note the competitive "
            "objective (e.g., 'development focus', 'peak performance target')."
        ),
        agent=tactical_analyst,
        expected_output=(
            "Tournament schedule with dates, competitive objectives, and "
            "age-group targets."
        ),
    )

    parent_overview = Task(
        description=(
            f"Produce a parent-friendly season overview document for the "
            f"{season_name} season. Include: (1) key dates (season start/end, "
            "tournaments, school holiday breaks), (2) weekly time commitment "
            "(training sessions + match days), (3) estimated season cost "
            "(registration, tournament fees, equipment), (4) volunteer "
            "expectations (table timing, transport, team snacks). "
            "Keep it warm, clear, and formatted for a club newsletter."
        ),
        agent=marketing_agent,
        context=[training_calendar, tournament_plan],
        expected_output=(
            "Parent-friendly season overview with dates, time commitment, "
            "cost estimate, and volunteer expectations."
        ),
    )

    crew = Crew(
        agents=[technical_coach, physical_coach, marketing_agent, tactical_analyst],
        tasks=[training_calendar, conditioning_plan, tournament_plan, parent_overview],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_season_plan(
    season_name: str = "2026-2027",
    season_start: str = "2026-09-01",
    season_end: str = "2027-06-15",
) -> dict:
    """Run the season planning crew and return structured results."""
    crew = build_season_plan_crew(
        season_name=season_name,
        season_start=season_start,
        season_end=season_end,
    )
    result = crew.kickoff()
    return {
        "crew_type": "season_plan",
        "season_name": season_name,
        "raw_output": str(result),
    }
