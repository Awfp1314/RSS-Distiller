# OpenCode Agent Instructions

## Entrypoint and Flow
- Runtime entrypoint is `main.py`; it wires `src/rss_parser.py -> src/db_manager.py -> src/ai_processor.py -> src/discord_pusher.py`.
- Multi-channel routing is loaded from `configs/*.json` in `main.py` (RSS URLs, `topic`, and webhook env var per channel). Each channel has its own `max_items_per_source`, `max_push_per_run`, and `min_scores` thresholds. Notably, the **法律前沿资讯** channel uses lower thresholds (`relevance: 7, frontier: 6, attention: 6, final: 7`) than the others.

## Python & Execution
- Python **3.10+** required (CI pins `3.10`).
- Install deps: `pip install -r requirements.txt`
- Run pipeline: `python main.py`
- No `pytest`/`unittest` suite; module checks are inline in `test/` files, runnable via:
  - `python test/test_rss_parser.py`
  - `python test/test_db_manager.py`
  - `python test/test_ai_processor.py`
  - `python test/test_discord_pusher.py`

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

## Candidate Ranking
- After AI scoring, `main.py` sorts passing candidates by `score + frontier_score + attention_score` (descending), breaking ties by `attention_score` then `frontier_score`. Only the top `max_push_per_run` are pushed per channel per run.

## Repo-Local Skills
- `.opencode/skills/编码指南/SKILL.md` contains AI agent coding guidelines (Karpathy-inspired). Load with the `skill` tool when writing/reviewing code.
