# intervals-icu-jan v1.3.3 — Draft-state passthrough + advisory

Drop-in upgrade over v1.3.2. No config migration; existing Claude Desktop / Cowork extension settings (api_key, athlete_id, profile, log_level) are preserved.

## What's new

### Changed

`format_activity_summary` now passes data through with an advisory header instead of blocking on the draft signal when the API returned substantive fields.

**Previously (v1.3.0–v1.3.2):** any `_is_draft_activity` hit short-circuited to the remediation message regardless of payload content. This withheld real data on the documented Zwift-via-Strava case where the API returns `stream_types`, `duration`, power, and HR despite the activity still holding its raw upstream `id`.

**v1.3.3 routing:**

| Condition | Output |
|---|---|
| Draft signal + substantive data present | Full body rendered, with a one-line `advisory:` header prepended (surfaces `source`, `analyzed` flag, available `stream_types`, web URL) |
| Draft signal + empty stub | Existing v1.3.0/v1.3.1/v1.3.2 remediation message — unchanged |
| Non-draft | Existing render — unchanged |

"Substantive" is defined by `_has_substantive_activity_data`: at least one of a non-empty `name`/`type`, a positive `duration`/`elapsed_time`/`moving_time`/`distance`, a positive average-power scalar, a positive `average_heartrate`, or a non-empty `stream_types` list.

### What an advisory header looks like

```
advisory: activity is pre-normalization on intervals.icu (source=STRAVA, analyzed=False, streams=watts, heartrate, cadence). Data below is what the API returned — open https://intervals.icu/activities/18303442074 and save to force analysis.

Activity: Zwift Stock 20-min FTP
ID: 18303442074
Type: VirtualRide
...
Power Data:
Average Power: 247 watts
...
```

The coach (model or human) gets the numbers AND knows the activity is pre-normalization. The previous behavior would have blocked on the same response and printed only the remediation message.

## Why

The draft signal was being used as a gate when it should have been used as an annotation. intervals.icu's API returns whatever data it has regardless of analysis state; suppressing the render produced a worse coach-facing experience than rendering the data with an explicit advisory. The empty-stub fallback is preserved because that case is real (some Zwift uploads do sit in upstream-ID limbo with no exposed fields) and the remediation message is still the right response for it.

## What's NOT in v1.3.3

- No wrapper-side response cache exists; no `force_refresh` parameter added. The stale-data symptom (renamed activity still returns the warning on a fresh pull) must originate in the MCP host or upstream timing, not in this wrapper.
- No new tools, no profile shift, no new endpoints. Custom-items / routes / gear / segments / weather / athlete-power-curves / `fields=` selector are tracked for v1.4.
- No changes to `get_activity_intervals`' 422 handling (v1.3.0) or `link_activity_to_event`'s 422 handling (v1.3.2) — both still correct.

## Lean / full profile

Unchanged at **31 / 135 tools**. The five per-activity analysis tools (`get_activity_streams`, `get_activity_interval_stats`, `get_activity_power_curve`, `find_best_efforts`, `get_activity_hr_curve`) have been in lean since v1.3.1; no promotion needed.

## Install

Same flow as prior 1.3.x releases. See [README.md](./README.md) Quick install → Path A.

```bash
gh release download v1.3.3 -R jancrab/intervals-mcp-server
# then double-click intervals-icu-jan-1.3.3.mcpb
```

## Compatibility

- macOS / Linux / Windows
- `uv` on PATH (auto-installs Python 3.12+; no host Python requirement)
- MCPB `manifest_version: "0.3"`

## Tests

207 unit tests passing (199 from v1.3.2 + 8 new):

- `_has_substantive_activity_data` predicate: 4 tests covering name-present, power-present, stream_types-present, empty-stub-false.
- `format_activity_summary` routing: substantive-draft renders full body + advisory; empty-stub keeps remediation; non-draft unchanged.
- `_format_draft_advisory_header` content: surfaces `source`, `analyzed`, `stream_types`, web URL.

## Checksums

See `intervals-icu-jan-1.3.3.mcpb.sha256` attached to this release.

```bash
# macOS / Linux
shasum -a 256 intervals-icu-jan-1.3.3.mcpb

# Windows (PowerShell)
Get-FileHash -Algorithm SHA256 intervals-icu-jan-1.3.3.mcpb
```
