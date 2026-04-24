# RSS Distiller 🔬

<div align="center">

[![Daily AI News Pusher](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml/badge.svg)](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/j556gmgY4)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Awfp1314/RSS-Distiller/pulls)

**In the age of information overload, we don't need more news - we need smarter filters.**

[English](README.md) | [简体中文](README.zh-CN.md)

[Join Discord](https://discord.gg/j556gmgY4) · [Open an Issue](https://github.com/Awfp1314/RSS-Distiller/issues/new) · [Submit a PR](https://github.com/Awfp1314/RSS-Distiller/pulls)

</div>

---

## Introduction

RSS Distiller is an AI-powered tech intelligence pipeline that fetches RSS articles, applies a **topic-aware dual evaluation** with DeepSeek (**Relevance + Quality**), and pushes only high-value bilingual summaries to Discord.

Why it exists:
- Developers subscribe to many sources but still miss signal in noise.
- Generic summarizers rank quality but often ignore domain relevance.
- RSS Distiller adds strict hard filters: if an article is off-topic or lacks quality, it gets `score=0` and is dropped.

---

## Key Features

- 🎯 **Topic Routing**: multi-channel routing via `configs/*.json` files, each with independent RSS sources, Discord webhook, and domain `topic`.
- 🧠 **Dual Evaluation**: DeepSeek scores `relevance_score` and `quality_score`; low-signal content is hard-filtered.
- 🌐 **Bilingual Output**: auto-generates EN/ZH title translation, key points, and impact analysis.
- 🔁 **Deduplication**: Turso-backed link storage prevents duplicate pushes.
- 📉 **Source Flood Control**: per-source candidate caps prevent a single feed from dominating the queue.
- 🧪 **Stratified arXiv Sampling**: combines newest, keyword-strong mid-tail, and exploration samples to avoid missing high-value items beyond the top slice.
- 🏁 **Top-K Push Selection**: candidates are ranked by composite AI signals and only top items are pushed each run.
- ⚙️ **Zero-Cost Scheduling**: GitHub Actions runs daily (and supports manual dispatch).

---

## Architecture

```text
RSS Sources
   -> 24h Time Filter (rss_parser.py)
   -> Link Dedup Check (db_manager.py / Turso)
   -> AI Evaluation (ai_processor.py)
        1) Relevance Score (0-10)
        2) Quality Score (0-10)
        3) Hard thresholds -> score=0 if not qualified
   -> Candidate Ranking (composite score: relevance * 0.4 + quality * 0.6)
   -> Discord Push (discord_pusher.py)
   -> Insert Link to DB (on successful push)
```

Core modules:
- `main.py`: orchestration and channel routing (loads `configs/*.json`)
- `src/rss_parser.py`: feed fetch, parsing, time-window filtering
- `src/ai_processor.py`: DeepSeek prompt + scoring + structured extraction
- `src/discord_pusher.py`: markdown message formatting + webhook push
- `src/db_manager.py`: Turso HTTP pipeline API (init/check/insert)

---

## Quick Start

### 1) Install

```bash
git clone https://github.com/Awfp1314/RSS-Distiller.git
cd RSS-Distiller
pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
```

Set values in `.env`:

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxx

TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-token

DISCORD_WEBHOOK_AI=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_UE=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_LEGAL=https://discord.com/api/webhooks/...
```

### 3) Run

```bash
python main.py
```

### 4) Module tests

```bash
python test/test_rss_parser.py
python test/test_db_manager.py
python test/test_ai_processor.py
python test/test_discord_pusher.py
```

> Tests call real external services (DeepSeek API, Turso DB, Discord webhook). Ensure your `.env` is configured before running them.

---

## GitHub Actions Deployment

Workflow files:
- `.github/workflows/daily_push.yml` (daily RSS distillation)
- `.github/workflows/changelog_notify.yml` (post commit updates to Discord `#changelog`)

- Scheduled run: daily at `00:00 UTC` (08:00 Beijing Time)
- Manual run: `workflow_dispatch`
- Timezone behavior: schedule is fixed in `UTC`; Discord posts are sent immediately when the workflow runs (not per-user local 08:00 delivery)
- Required repository secrets:
  - `DEEPSEEK_API_KEY`
  - `TURSO_DATABASE_URL`
  - `TURSO_AUTH_TOKEN`
  - `DISCORD_WEBHOOK_AI`
  - `DISCORD_WEBHOOK_UE`
  - `DISCORD_WEBHOOK_LEGAL`
  - `DISCORD_WEBHOOK_CHANGELOG`

`changelog_notify.yml` listens to `push` on `main` and posts a commit summary (author, commit count, short SHA + title, compare link, workflow link) to your Discord changelog channel.

---

## How to Contribute

We are building a community-driven **hardcore tech intelligence project**. Contributions are welcome:

### 1. Suggest New Channels (Easiest Way)

Use our AI-powered configuration generator:

1. Open [`CHANNEL_CONFIG_PROMPT.md`](CHANNEL_CONFIG_PROMPT.md)
2. Copy the prompt and send it to ChatGPT/Claude/Kimi
3. Answer the AI's questions about your desired channel
4. Post the generated JSON config in our [Discord forum](https://discord.gg/j556gmgY4) `#rss-suggestions`
5. We'll review and add it within 24 hours!

No coding required — just chat with AI and get a standard config.

### 2. Direct Contribution (For Developers)

- **Add/Edit RSS sources**: Modify JSON files in `configs/` (e.g., `configs/AI.json`)
- **Create new channels**: Add a new `configs/<channel>.json` file following the existing schema
- **Improve AI prompts**: Tune `SYSTEM_PROMPT_TEMPLATE` in `src/ai_processor.py`
- **Open Issues/PRs**: Bug reports, feature requests, and architecture improvements are welcome

---

## Community

- 💬 Discord: https://discord.gg/j556gmgY4
- 📧 Email: w1849619997@gmail.com
- 🐛 Issues: https://github.com/Awfp1314/RSS-Distiller/issues

---

## License

MIT License.
