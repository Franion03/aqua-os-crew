"""
Enrollment Campaign Crew.

Trigger: 1st of each month (or on-demand).
Agents: Marketing → Technical Coach
Outputs: Social media posts, enrollment email campaign, trial-day coordination.
"""

import logging

from crewai import Agent, Crew, Process, Task
from llm_config import model_for

from tools.email_tool import send_parent_email
from tools.player_db import get_roster_players

logger = logging.getLogger(__name__)


# ── Agents ──────────────────────────────────────────────────────────────

marketing_agent = Agent(
    role="Marketing & Communications Director",
    goal="Drive new player enrollment and retain existing families",
    backstory=(
        "Charismatic sports marketer who transformed a small local swim club "
        "into a 200-member water polo powerhouse. You write copy that parents "
        "trust — highlighting safety, certified coaching, and the life skills "
        "kids gain through team sport. You know Instagram, newsletters, and "
        "community outreach channels intimately."
    ),
    tools=[send_parent_email, get_roster_players],
    allow_delegation=False,
    verbose=True,
    llm=model_for("marketing"),
)

technical_coach = Agent(
    role="Technical Head Coach",
    goal="Design trial-day experiences that convert visitors into members",
    backstory=(
        "Coach who has run dozens of 'Bring a Friend' and trial days. "
        "You know exactly which drills impress parents (eggbeater jumps, "
        "fast passing cycles) and which ones get kids hooked on water polo. "
        "You structure trial sessions so every child leaves feeling successful."
    ),
    tools=[get_roster_players],
    allow_delegation=False,
    verbose=True,
    llm=model_for("technical"),
)


# ── Crew Builder ────────────────────────────────────────────────────────

def build_enrollment_crew(season: str = "Summer 2026", camp_start: str = "2026-07-05") -> Crew:
    """Assemble the enrollment campaign crew.

    Args:
        season: Season name (e.g., "Summer 2026").
        camp_start: Start date of the camp/trial period.
    """

    social_post = Task(
        description=(
            f"Write 3 high-energy Instagram posts promoting our {season} "
            "Water Polo enrollment campaign for kids ages 8-15. "
            "Post 1: General club introduction + parent testimonial angle. "
            "Post 2: Focus on safety, certified coaches, and pool facilities. "
            "Post 3: Call-to-action with trial day registration link and "
            "'no experience needed' messaging. Each post should be under 150 "
            "words, include emoji, and end with a clear CTA."
        ),
        agent=marketing_agent,
        expected_output="3 Instagram posts with emoji and CTAs.",
    )

    enrollment_email = Task(
        description=(
            f"Draft an enrollment outreach email to send to all existing "
            "parent contacts in our database. Subject: '🏊‍♂️ {season} Water "
            "Polo Season is Open — Bring a Friend!' The email should: "
            "(1) celebrate recent club achievements, "
            "(2) invite families to register for the new season, "
            "(3) offer a 'bring a friend' incentive (first trial free), "
            "(4) list the 3 things parents care about most: safety, "
            "certified coaching, and flexible schedule. "
            "End with a warm president signature. "
            "Do NOT actually send — produce the draft."
        ),
        agent=marketing_agent,
        expected_output="Complete enrollment email draft with subject line and signature.",
    )

    trial_day_plan = Task(
        description=(
            f"Design a 60-minute 'Trial Day' session plan for new kids "
            "(ages 8-15, no water polo experience) starting {camp_start}. "
            "Structure: (1) 10 min — pool familiarization + safety briefing, "
            "(2) 15 min — basic eggbeater + sculling taught with fun games, "
            "(3) 15 min — two-hand ball passing in shallow end, "
            "(4) 10 min — mini scrimmage with floating goals, "
            "(5) 10 min — cool-down + parent Q&A talking points for coaches. "
            "Include exact drill names and coaching cues."
        ),
        agent=technical_coach,
        expected_output="60-minute trial day session plan with timed blocks and drill names.",
    )

    crew = Crew(
        agents=[marketing_agent, technical_coach],
        tasks=[social_post, enrollment_email, trial_day_plan],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_enrollment(season: str = "Summer 2026", camp_start: str = "2026-07-05") -> dict:
    """Run the enrollment campaign crew and return structured results."""
    crew = build_enrollment_crew(season=season, camp_start=camp_start)
    result = crew.kickoff()
    return {
        "crew_type": "enrollment",
        "season": season,
        "camp_start": camp_start,
        "raw_output": str(result),
    }
