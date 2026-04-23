# OpenCode Agent Instructions

## Entrypoint and Flow
- Runtime entrypoint is `main.py`; it wires `rss_parser.py -> db_manager.py -> ai_processor.py -> discord_pusher.py`.
- Multi-channel routing is hardcoded in `CHANNELS_CONFIG` in `main.py` (RSS URLs, `topic`, and webhook env var per channel).

## Local Run Commands
- Install deps: `pip install -r requirements.txt`
- Run pipeline: `python main.py`
- There is no `pytest`/`unittest` suite; module checks are inline under each file's `if __name__ == "__main__":` block:
  - `python rss_parser.py`
  - `python db_manager.py`
  - `python ai_processor.py`
  - `python discord_pusher.py`

## Testing/Execution Gotchas
- Inline tests are not isolated unit tests; they call real external services.
- `ai_processor.py` test calls DeepSeek API (uses key/quota).
- `discord_pusher.py` test sends a real webhook message if configured.
- `db_manager.py` test writes to Turso and then deletes a test row.

## Turso Integration Constraints
- DB access is HTTP pipeline API only (`/v2/pipeline`) via `requests` in `db_manager.py`; do not introduce `sqlite3`/ORM code.
- Keep SQL execution pattern consistent with `_execute(sql, args)` where args are Turso typed objects, e.g. `{"type": "text", "value": "..."}`.
- `TURSO_DATABASE_URL` is expected as `libsql://...`; code converts it to `https://.../v2/pipeline`.

## Environment and CI Notes
- Local env is loaded with `dotenv`; required vars are in `.env.example`.
- GitHub Actions:
  - `.github/workflows/daily_push.yml` runs `python main.py` on schedule (`0 0 * * *`) and manual dispatch.
  - `.github/workflows/changelog_notify.yml` posts only commits whose first line starts with `feat:`, `fix:`, `perf:`, or `refactor:`.
