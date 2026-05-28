"""
Shared LLM model resolver for AquaOS crew agents.

Returns the appropriate model string based on the active LLM provider:
  - OpenRouter → per-agent optimal model (DeepSeek, Gemini, Claude)
  - Gemini direct → gemini-2.0-flash for all agents
  - None → raises error

Usage in crew modules:
    from llm_config import model_for

    agent = Agent(
        role="Tactical Analyst",
        llm=model_for("tactical"),
        ...
    )
"""

import os

# Model assignments per agent role, using OpenRouter paths
_OPENROUTER_MODELS = {
    "tactical": "openrouter/deepseek/deepseek-chat",          # DeepSeek V3 — best reasoning
    "technical": "openrouter/google/gemini-2.0-flash-001",    # Gemini 2.0 Flash — structured output
    "physical": "openrouter/google/gemini-2.0-flash-001",     # Gemini 2.0 Flash — cheap + fast
    "marketing": "openrouter/anthropic/claude-3.5-haiku",     # Claude 3.5 Haiku — best copy/tone
    "default": "openrouter/google/gemini-2.0-flash-001",      # Fallback
}

# Free-tier fallback models (for when OpenRouter credit runs out)
_OPENROUTER_FREE_MODELS = {
    "tactical": "openrouter/meta-llama/llama-3.3-70b-instruct",     # Llama 3.3 — free on OpenRouter
    "technical": "openrouter/google/gemini-2.0-flash-001",          # Gemini — near-free
    "physical": "openrouter/google/gemini-2.0-flash-001",
    "marketing": "openrouter/meta-llama/llama-3.3-70b-instruct",    # Llama 3.3 — free
    "default": "openrouter/google/gemini-2.0-flash-001",
}

# Gemini-direct fallback (single model for all)
_GEMINI_MODEL = "gemini-2.0-flash"


def model_for(agent_role: str, prefer_free: bool = False) -> str:
    """Return the best model string for a given agent role.

    Args:
        agent_role: One of "tactical", "technical", "physical", "marketing", "default".
        prefer_free: If True, use free-tier models on OpenRouter (Llama instead of DeepSeek/Claude).

    Returns:
        Model string compatible with CrewAI Agent(llm=...).
    """
    provider = _detect_provider()
    model_map = _OPENROUTER_FREE_MODELS if prefer_free else _OPENROUTER_MODELS

    if provider == "openrouter":
        return model_map.get(agent_role, model_map["default"])
    elif provider == "gemini":
        return _GEMINI_MODEL
    else:
        # No provider configured — CrewAI will fail with a clear error
        return _GEMINI_MODEL


def get_provider() -> str:
    """Return the active LLM provider: 'openrouter', 'gemini', or 'none'."""
    return _detect_provider()


def _detect_provider() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "none"
