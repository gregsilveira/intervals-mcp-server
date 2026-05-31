# intervals-icu-jan v1.4.0 — Strava-source restriction + lean expansion

Drop-in upgrade over v1.3.3. No config migration; existing Claude Desktop / Cowork extension settings are preserved.

## The headline: a corrected root cause

Live read-only API probing (2026-05-31) overturned the v1.3.x "pre-normalization" theory. Every "draft" activity on the test account is **Strava-sourced**, and intervals.icu returns a 5-key stub:

```json
{ "id": "18728161934", "icu_athlete_id": "i141174",
  "start_date_local": "2026-05-31T12:40:44", "source": "STRAVA",
  "_note": "STRAVA activities are not available via the API" }
```

Derived endpoints (streams, power curve, …) return `{"status":422,"error":"Cannot read Strava activities via the API"}`.

This is a **permanent Strava API-licensing restriction** at intervals.icu's API-serving layer — not a transient analysis state. **No rename, reprocess, or wait resolves it.** The data only becomes API-readable if the same ride reaches intervals.icu via a **non-Strava** route (Garmin Connect, direct `.fit` upload). On the test account, the non-Strava sources (`WAHOO`, `OAUTH_CLIENT`, `UPLOAD` — 19 of 26 activities) are fully readable.

**`normalize_activity` was therefore not built.** There is nothing to normalize — the block is on serving, not analysis. An auto-trigger would have written to the account on every read for zero data gain.

## What changed

### Changed

- **Strava-restricted activities now render a compact, honest 3-line message** (cause + real remediation), checked before the generic draft heuristic. No `N/A` wall, no misleading "rename to fix" wording.
- **API error bodies are no longer discarded.** A 422 now surfaces "Cannot read Strava activities via the API" instead of a generic canned message — across every tool, including `get_activity_streams` / `_power_curve` / `_hr_curve` / `_power_vs_hr`.

### Added — lean profile expansion (31 → 40 tools, ~11.9k → ~13.9k tokens)

Promoted to lean (each live-tested): `get_athlete_summary`, `list_athlete_power_curves`, `list_athlete_hr_curves`, `list_sport_settings`, `get_activity_power_vs_hr`, `get_activity_hr_load_model`, `get_activity_segments`, `get_activity_map`, `list_gear`, `get_weather_forecast`.

Moved out of lean to full-only: `get_activity_full_report` (heaviest single tool; internally pulls several now-lean tools).

Lean is still ~68% smaller than full (135 tools / ~44k tokens).

## The real fix for Zwift data (your side, not the MCP)

Route Zwift to intervals.icu via a **non-Strava** path:
- **Best:** Zwift → Garmin Connect → intervals.icu (free Garmin account, carries power + HR + cadence, fully API-readable). One-time setup, automatic after.
- Alternatives: direct `.fit` upload, or Dropbox auto-import (PC/Mac Zwift).

No MCP change can lift the Strava restriction.

## Compatibility

- macOS / Linux / Windows; `uv` on PATH (auto-installs Python 3.12+); MCPB `manifest_version: "0.3"`.

## Tests

214 unit tests passing (was 207 in v1.3.3 + 7 new): Strava-restriction detection + render, the real 5-key stub shape, error-body detail extraction, and the corrected v1.3.3 advisory test (now non-Strava-sourced, reflecting that real Strava activities never carry substantive data).

## Checksums

See `intervals-icu-jan-1.4.0.mcpb.sha256` attached to this release.

```bash
# macOS / Linux
shasum -a 256 intervals-icu-jan-1.4.0.mcpb
# Windows (PowerShell)
Get-FileHash -Algorithm SHA256 intervals-icu-jan-1.4.0.mcpb
```
