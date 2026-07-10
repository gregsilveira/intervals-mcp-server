"""
Unit tests for the profile gate (``intervals_mcp_server.tools.profile``).

Covers the three profiles exposed via ``INTERVALS_PROFILE``:

- ``lean``      — explicit tool allowlist (``LEAN_TOOLS``).
- ``analysis``  — module denylist (``ANALYSIS_CUT_MODULES``): the full surface
  minus ``custom_items`` / ``library`` / ``file_ops`` (ADR-007, issue #292).
- ``full``      — everything.

The exact profile counts depend on the *full* (ungated) registry, but the
shared ``mcp`` singleton is gated once at import time based on the env var.
So the count assertions run the real server in a subprocess with
``INTERVALS_PROFILE=full`` and re-apply the gate there, fully isolated from the
in-process (default-lean) registry other tests rely on.
"""

import os
import pathlib
import subprocess
import sys

from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from intervals_mcp_server.tools.profile import (  # pylint: disable=wrong-import-position
    ANALYSIS_CUT_MODULES,
    apply_profile,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Expected profile sizes. If a module gains/loses tools these move; update
# alongside ADR-007 so the doc and the gate never drift silently.
FULL_COUNT = 140
ANALYSIS_COUNT = 110
LEAN_COUNT = 45


def _profile_counts() -> dict[str, int]:
    """Return {profile: kept_tool_count} from a full-registry subprocess."""
    snippet = (
        "import intervals_mcp_server.server\n"
        "from intervals_mcp_server.mcp_instance import mcp\n"
        "from intervals_mcp_server.tools.profile import apply_profile\n"
        "full = len(mcp._tool_manager._tools)\n"
        "kept, _ = apply_profile(mcp, 'analysis')\n"
        "print(f'{full},{kept}')\n"
    )
    env = {
        **os.environ,
        "API_KEY": "test",
        "ATHLETE_ID": "i1",
        "INTERVALS_PROFILE": "full",
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }
    out = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    full_str, analysis_str = out.stdout.strip().splitlines()[-1].split(",")
    return {"full": int(full_str), "analysis": int(analysis_str)}


def test_analysis_denylist_membership():
    """The analysis cut is exactly the three domains from issue #292."""
    assert ANALYSIS_CUT_MODULES == frozenset({"custom_items", "library", "file_ops"})


def test_full_and_analysis_counts():
    """full = 140, analysis = 110 (full minus the three cut modules)."""
    counts = _profile_counts()
    assert counts["full"] == FULL_COUNT
    assert counts["analysis"] == ANALYSIS_COUNT
    assert FULL_COUNT - ANALYSIS_COUNT == 30  # custom_items(5)+library(16)+file_ops(9)


def test_analysis_removes_only_cut_modules():
    """A fresh registry: analysis drops cut-module tools, keeps every other.

    Registers a representative real tool from each cut module plus several
    kept modules (including the two — activity_writes, aggregators — that
    issue #292 leaves unclassified but we keep). Isolated from the shared
    singleton so it never depends on import order.
    """
    from intervals_mcp_server.tools.custom_items import get_custom_items
    from intervals_mcp_server.tools.library import list_workouts
    from intervals_mcp_server.tools.file_ops import download_workout
    from intervals_mcp_server.tools.activities import get_activities
    from intervals_mcp_server.tools.activity_writes import update_activity
    from intervals_mcp_server.tools.aggregators import get_activity_full_report
    from intervals_mcp_server.tools.wellness import get_wellness_data

    cut_fns = [get_custom_items, list_workouts, download_workout]
    kept_fns = [get_activities, update_activity, get_activity_full_report, get_wellness_data]

    fresh = FastMCP("test")
    for fn in cut_fns + kept_fns:
        fresh.add_tool(fn)

    kept, removed = apply_profile(fresh, "analysis")

    remaining = set(fresh._tool_manager._tools.keys())  # pylint: disable=protected-access
    assert removed == len(cut_fns)
    assert kept == len(kept_fns)
    for fn in cut_fns:
        assert fn.__name__ not in remaining
    for fn in kept_fns:
        assert fn.__name__ in remaining


def test_full_profile_keeps_everything():
    """A fresh registry under 'full' removes nothing."""
    from intervals_mcp_server.tools.custom_items import get_custom_items
    from intervals_mcp_server.tools.activities import get_activities

    fresh = FastMCP("test")
    for fn in (get_custom_items, get_activities):
        fresh.add_tool(fn)

    kept, removed = apply_profile(fresh, "full")
    assert removed == 0
    assert kept == 2
