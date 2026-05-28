"""
Match Preparation Crew.

Trigger: 3-5 days before a competitive match.
Agents: Tactical Analyst → Technical Coach → Marketing → Physical Coach
Outputs: Tactical briefing, 13-player roster, parent email, warmup plan.
"""

import logging

from crewai import Agent, Crew, Process, Task
from llm_config import model_for

from tools.player_db import get_roster_players
from tools.email_tool import send_parent_email
from tools.calendar_tool import schedule_match, get_next_match, get_upcoming_events

logger = logging.getLogger(__name__)


# ── Agents ──────────────────────────────────────────────────────────────

tactical_analyst = Agent(
    role="Tactical Analyst & Opposition Scout",
    goal="Analyze opponents and produce actionable tactical briefings",
    backstory=(
        "Data-driven water polo analyst with 15 years of experience scouting "
        "regional youth leagues. You study opponent formations, key player "
        "tendencies, and exploitable defensive gaps. Your briefings are concise, "
        "visual, and immediately useful for the coaching staff."
    ),
    tools=[get_roster_players, get_next_match, get_upcoming_events],
    allow_delegation=False,
    verbose=True,
    llm=model_for("tactical"),
)

technical_coach = Agent(
    role="Technical Head Coach",
    goal="Select optimal rosters and design match strategies",
    backstory=(
        "Former national team head coach with deep expertise in FINA training "
        "methodology. You know every player in the club intimately — their "
        "strengths, development edges, and position compatibility. You build "
        "rosters that balance experience with development opportunity."
    ),
    tools=[get_roster_players],
    allow_delegation=False,
    verbose=True,
    llm=model_for("technical"),
)

marketing_agent = Agent(
    role="Marketing & Communications Director",
    goal="Draft parent communications and promote club visibility",
    backstory=(
        "Professional sports club marketer who knows how to craft warm, "
        "professional emails that parents actually read. You handle match "
        "logistics, registration deadlines, equipment checklists, and "
        "volunteer coordination with precision."
    ),
    tools=[send_parent_email, get_roster_players],
    allow_delegation=False,
    verbose=True,
    llm=model_for("marketing"),
)

physical_coach = Agent(
    role="Physical Conditioning Coach",
    goal="Design warmup protocols and prevent match-day injuries",
    backstory=(
        "Sports scientist specializing in aquatic athlete physiology. "
        "You design evidence-based warmup sequences that activate the "
        "rotator cuff, thoracic spine, and hip flexors — the three "
        "injury hotspots for water polo athletes aged 8-15."
    ),
    allow_delegation=False,
    verbose=True,
    llm=model_for("physical"),
)


# ── Crew Builder ────────────────────────────────────────────────────────

def build_match_prep_crew(opponent: str, match_date: str, pool: str = "Home Pool") -> Crew:
    """Assemble the match preparation crew for a specific fixture.

    Args:
        opponent: Name of the opposing club.
        match_date: Match date in ISO format (YYYY-MM-DD).
        pool: Pool name or location (default: Home Pool).
    """

    schedule = Task(
        description=(
            f"Schedule the match against '{opponent}' on {match_date} "
            f"at '{pool}' on the club calendar."
        ),
        agent=tactical_analyst,
        tools=[schedule_match],
        expected_output="Calendar confirmation with match details.",
    )

    analyze_opponent = Task(
        description=(
            f"Analyze the opponent '{opponent}' playing in our regional youth "
            "water polo league. Identify their likely formation (press, zone, "
            "M-drop), their strongest players by position, and 2-3 tactical "
            "weaknesses our team can exploit. Write a structured briefing "
            "document with clear sections: Formation, Key Players, Weaknesses, "
            "Recommended Counter-Strategy."
        ),
        agent=tactical_analyst,
        expected_output=(
            "Tactical briefing document with sections: Formation Analysis, "
            "Key Opposition Players, Exploitable Weaknesses, Counter-Strategy."
        ),
    )

    generate_roster = Task(
        description=(
            f"Based on the tactical analysis of '{opponent}', select the "
            "optimal 13-player match roster from our club database. Consider: "
            "player levels (1-4), skill ratings (swimming, ballHandling, "
            "shooting, tactics, stamina), position compatibility, and the need "
            "to rotate less-experienced players for development. "
            "Output a structured roster with: starting 7, substitute blocks "
            "of 3, player-position assignments, and rotation timing notes."
        ),
        agent=technical_coach,
        context=[analyze_opponent],
        expected_output=(
            "Structured 13-player roster with starting 7, substitute blocks, "
            "position assignments, and rotation strategy."
        ),
    )

    draft_parent_email = Task(
        description=(
            "Draft a warm, professional email to the parents of all selected "
            "roster players. Include: match date/time, opponent, arrival time "
            "(08:45 AM), equipment checklist (cap, weight belt, towel, water "
            "bottle), volunteer assignments, and a brief note about this "
            "week's training focus. End with club president signature block. "
            "Use the player database to get email addresses. "
            "Do NOT actually send — just produce the draft."
        ),
        agent=marketing_agent,
        context=[generate_roster],
        expected_output=(
            "Complete parent email draft with match logistics, equipment "
            "checklist, volunteer assignments, and president signature."
        ),
    )

    design_warmup = Task(
        description=(
            "Design a 20-minute pre-match warmup protocol for youth water polo "
            "athletes (ages 10-14). Structure it in 4 blocks of 5 minutes each: "
            "(1) dryland mobility — rotator cuff bands + thoracic spine, "
            "(2) pool entry + light swim activation, "
            "(3) eggbeater elevation drills, "
            "(4) passing pairs + shot warmup. "
            "Include exact drill names, durations, and coaching cues."
        ),
        agent=physical_coach,
        expected_output=(
            "Timed 20-minute warmup protocol with 4 blocks, drill names, "
            "durations, and coaching cues."
        ),
    )

    crew = Crew(
        agents=[tactical_analyst, technical_coach, marketing_agent, physical_coach],
        tasks=[schedule, analyze_opponent, generate_roster, draft_parent_email, design_warmup],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_match_prep(opponent: str = "Regional Rivals", match_date: str = "2026-06-07", pool: str = "Home Pool") -> dict:
    """Run the match preparation crew and return structured results."""
    crew = build_match_prep_crew(opponent=opponent, match_date=match_date, pool=pool)
    result = crew.kickoff()
    return {
        "crew_type": "match_prep",
        "opponent": opponent,
        "match_date": match_date,
        "pool": pool,
        "raw_output": str(result),
    }
