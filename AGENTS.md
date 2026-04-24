# OpenCode Agent Instructions

## Entrypoint and Flow
- Runtime entrypoint is `main.py`; it wires `src/rss_parser.py -> src/db_manager.py -> src/ai_processor.py -> src/discord_pusher.py`.
- Multi-channel routing is loaded from `configs/*.json` in `main.py` (RSS URLs, `topic`, webhook env var, and domain-specific `evaluation_focus` per channel). Each channel has its own `max_items_per_source`, `max_push_per_run`, and `min_scores` thresholds (e.g., Legal channel uses `relevance: 7, quality: 6`).

## Python & Execution
- Python **3.10+** required (CI pins `3.10`).
- Install deps: `pip install -r requirements.txt`
- Run pipeline: `python main.py`
- No `pytest`/`unittest` suite; module checks are inline in `tests/` files, runnable via:
  - `python tests/test_rss_parser.py`
  - `python tests/test_db_manager.py`
  - `python tests/test_ai_processor.py`
  - `python tests/test_discord_pusher.py`

## Testing/Execution Gotchas
- Inline tests are **not** isolated unit tests; they call real external services (DeepSeek API, Turso DB, Discord webhook).
- `src/ai_processor.py` test calls DeepSeek API (uses key/quota). The API call uses `response_format={"type": "json_object"}` with `temperature=0.3`. JSON repair fallback handles trailing commas: `re.sub(r",\s*([}\]])", r"\1", raw)`. Article summaries are truncated to 1500 chars before being sent to the API.
- `src/db_manager.py` test writes to Turso then deletes a test row.
- `src/discord_pusher.py` test falls back to `DISCORD_WEBHOOK_URL` if `DISCORD_WEBHOOK_AI` is not set (legacy var). Sends a real webhook message if either is configured. The message template wraps links in `<url>` angle brackets to suppress Discord link previews — preserve this when editing the template.
- `src/rss_parser.py` disables SSL verification (`verify=False`) for RSS fetches. arXiv sources use stratified sampling (fresh/quality/explore layers), not simple top-N truncation. A Reddit early-filter (`_looks_like_low_signal_discussion`) drops Q&A/help posts before they reach the AI — this filter is Reddit-only (checks `source_url` for `reddit.com`).

## Turso Integration Constraints
- DB access is HTTP pipeline API only (`/v2/pipeline`) via `requests` in `src/db_manager.py`; do not introduce `sqlite3`/ORM code.
- Keep SQL execution pattern consistent with `_execute(sql, args)` where args are Turso typed objects, e.g. `{"type": "text", "value": "..."}`.
- `TURSO_DATABASE_URL` is expected as `libsql://...`; code converts it to `https://.../v2/pipeline`.

## Environment and CI Notes
- Local env is loaded with `dotenv`; required vars are in `.env.example`. `DISCORD_WEBHOOK_CHANGELOG` is only used by the changelog workflow, not the main pipeline.
- GitHub Actions:
  - `.github/workflows/daily_push.yml` runs `python main.py` on schedule (`0 0 * * *`) and manual dispatch.
  - `.github/workflows/changelog_notify.yml` triggers on every push to `main` (not scheduled); posts only commits whose first line starts with `feat:`, `fix:`, `perf:`, or `refactor:`. Silently skips if no matching commits or if `DISCORD_WEBHOOK_CHANGELOG` is unset/invalid.

## AI Scoring and Ranking
- DeepSeek evaluates articles on **two dimensions**: `relevance_score` (0-10) and `quality_score` (0-10). If either score falls below the channel's `min_scores` threshold, both are set to 0 and the article is rejected.
- Ranking formula in `main.py`: `base_score = relevance_score * 0.4 + quality_score * 0.6`. If `time_decay_gravity > 0`, applies time decay: `final_score = base_score * (1 / (1 + (age_hours / halflife) ^ gravity))`. Sorts by `(final_score, quality_score)` descending.
- Only the top `max_push_per_run` candidates are pushed per channel per run.

## Repo-Local Skills
- `.opencode/skills/编码指南/SKILL.md` contains AI agent coding guidelines (Karpathy-inspired). Load with the `skill` tool when writing/reviewing code.
