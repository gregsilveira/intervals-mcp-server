"""
Configuration management for Intervals.icu MCP Server.

This module handles loading and validation of configuration from environment variables.
"""

import os
from dataclasses import dataclass

from intervals_mcp_server.utils.validation import validate_athlete_id

# Try to load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv

    _ = load_dotenv()
except ImportError:
    # python-dotenv not installed, proceed without it
    pass


@dataclass
class Config:
    """Configuration settings for the Intervals.icu MCP Server."""

    api_key: str
    athlete_id: str
    intervals_api_base_url: str
    user_agent: str
    profile: str  # "lean" (default, 45 tools), "analysis" (110), or "full" (all 140)


_config_instance: Config | None = None  # pylint: disable=invalid-name


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Returns:
        Config: Configuration instance with loaded values.

    Raises:
        ValueError: If athlete_id is invalid (when non-empty).
    """
    api_key = os.getenv("API_KEY", "")
    athlete_id = os.getenv("ATHLETE_ID", "")
    intervals_api_base_url = os.getenv("INTERVALS_API_BASE_URL", "https://intervals.icu/api/v1")
    user_agent = "intervalsicu-mcp-server/1.0"

    # Profile gate (see tools/profile.py). Three profiles:
    #   - "lean" (default): 45 high-value tools — keeps context cost low for
    #     Claude Desktop / DXT installs.
    #   - "analysis": 110 tools — full API surface minus the three domains
    #     that are noise for the EnduranceIQ connector (custom_items, library,
    #     file_ops). Cut by module; see ADR-007 (issue #292).
    #   - "full": all 140 tools — SDK-style coverage of the whole API.
    # Any value other than "full"/"analysis" is treated as "lean" so
    # misspellings don't accidentally expose a larger surface area.
    profile_raw = os.getenv("INTERVALS_PROFILE", "lean").strip().lower()
    if profile_raw in ("full", "analysis"):
        profile = profile_raw
    else:
        profile = "lean"

    # Validate athlete_id if provided (empty string is allowed)
    if athlete_id:
        validate_athlete_id(athlete_id)

    return Config(
        api_key=api_key,
        athlete_id=athlete_id,
        intervals_api_base_url=intervals_api_base_url,
        user_agent=user_agent,
        profile=profile,
    )


def get_config() -> Config:
    """
    Get the configuration instance (singleton pattern).

    Returns:
        Config: The configuration instance.
    """
    global _config_instance  # pylint: disable=global-statement  # noqa: PLW0603 - singleton pattern
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance
