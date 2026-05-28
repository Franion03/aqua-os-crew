"""
Injury Response Crew.

Trigger: Event-driven — when a coach flags a player injury.
Agents: Physical Coach → Technical Coach → Marketing
Outputs: Recovery plan, modified training regimen, parent notification.
"""

import logging

from crewai import Agent, Crew, Process, Task
from llm_config import model_for

from tools.player_db import get_player_details, add_progress_log
from tools.email_tool import send_parent_email

logger = logging.getLogger(__name__)


# ── Agents ──────────────────────────────────────────────────────────────

physical_coach = Agent(
    role="Physical Conditioning Coach",
    goal="Assess injury severity and design safe return-to-play protocols",
    backstory=(
        "Sports medicine-informed conditioning coach specializing in aquatic "
        "athlete injuries — swimmer's shoulder, rotator cuff strains, hip "
        "flexor tendinitis, and concussion protocols. You always err on the "
        "side of caution with youth athletes and follow a 'heal first, "
        "train later' philosophy."
    ),
    tools=[get_player_details],
    allow_delegation=False,
    verbose=True,
    llm=model_for("physical"),
)

technical_coach = Agent(
    role="Technical Head Coach",
    goal="Adapt training plans to accommodate injured players",
    backstory=(
        "Experienced coach who knows how to keep injured players engaged "
        "without risking re-injury. You modify drills so players can practice "
        "passing from a seated position, observe tactics, or work on "
        "non-injured-side skills while recovering."
    ),
    tools=[get_player_details, add_progress_log],
    allow_delegation=False,
    verbose=True,
    llm=model_for("technical"),
)

marketing_agent = Agent(
    role="Marketing & Communications Director",
    goal="Communicate injury status to parents with clarity and care",
    backstory=(
        "Empathetic communicator who has handled dozens of youth sports "
        "injury notifications. You know parents need: (1) clear diagnosis "
        "in plain language, (2) estimated recovery timeline, (3) what the "
        "club is doing to support their child, (4) return-to-play criteria."
    ),
    tools=[send_parent_email, get_player_details],
    allow_delegation=False,
    verbose=True,
    llm=model_for("marketing"),
)


# ── Crew Builder ────────────────────────────────────────────────────────

def build_injury_response_crew(
    player_id: int,
    injury_description: str,
    severity: str = "moderate",
) -> Crew:
    """Assemble the injury response crew.

    Args:
        player_id: The injured player's ID.
        injury_description: Coach's description of the injury.
        severity: mild, moderate, or severe.
    """

    assessment = Task(
        description=(
            f"Assess the injury reported for player #{player_id}: "
            f"'{injury_description}'. Severity: {severity}. "
            "Based on the description, produce: (1) likely injury type in "
            "plain language, (2) recommended recovery timeline (days/weeks), "
            "(3) specific activities to AVOID during recovery, "
            "(4) safe activities the player CAN do to stay engaged, "
            "(5) clear return-to-full-training criteria. "
            "If severity is 'severe', recommend medical evaluation."
        ),
        agent=physical_coach,
        expected_output=(
            "Injury assessment with recovery timeline, activity restrictions, "
            "safe alternatives, and return-to-play criteria."
        ),
    )

    modified_training = Task(
        description=(
            f"For player #{player_id}, design a modified training plan that "
            "respects the injury restrictions from the assessment. "
            "Specify: (1) which regular drills they skip, "
            "(2) 3-4 alternative drills they can do (e.g., seated passing, "
            "tactical observation with coaching points, one-arm sculling), "
            "(3) how to keep them integrated with the team during recovery. "
            "Record a progress log entry noting the injury and modified plan."
        ),
        agent=technical_coach,
        tools=[add_progress_log],
        context=[assessment],
        expected_output=(
            "Modified training plan with drill substitutions, integration "
            "strategies, and progress log confirmation."
        ),
    )

    parent_notification = Task(
        description=(
            f"Draft a compassionate email to the parents of player #{player_id} "
            "about the injury. The email should: (1) describe what happened "
            "in simple, non-alarming terms, (2) explain the modified training "
            "plan and how the club is supporting their child, (3) provide the "
            "estimated recovery timeline, (4) list warning signs that would "
            "warrant a doctor visit, (5) invite them to contact the coaching "
            "staff with any concerns. Use a warm, reassuring tone. "
            "Do NOT actually send — produce the draft."
        ),
        agent=marketing_agent,
        context=[assessment, modified_training],
        expected_output="Compassionate parent notification email draft.",
    )

    crew = Crew(
        agents=[physical_coach, technical_coach, marketing_agent],
        tasks=[assessment, modified_training, parent_notification],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_injury_response(
    player_id: int,
    injury_description: str,
    severity: str = "moderate",
) -> dict:
    """Run the injury response crew and return structured results."""
    crew = build_injury_response_crew(
        player_id=player_id,
        injury_description=injury_description,
        severity=severity,
    )
    result = crew.kickoff()
    return {
        "crew_type": "injury_response",
        "player_id": player_id,
        "severity": severity,
        "raw_output": str(result),
    }
