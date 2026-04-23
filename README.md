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

RSS Distiller is an AI-powered tech intelligence pipeline that fetches RSS articles, applies a **topic-aware triple evaluation** with DeepSeek (**Relevance + Frontier Value + Attention**), and pushes only high-value bilingual summaries to Discord.

Why it exists:
- Developers subscribe to many sources but still miss signal in noise.
- Generic summarizers rank quality but often ignore domain relevance and actual market attention.
- RSS Distiller adds strict hard filters: if an article is off-topic, not frontier enough, or lacks attention signal, it gets `score=0` and is dropped.

---

## Key Features

- 🎯 **Topic Routing**: multi-channel routing via `CHANNELS_CONFIG`, each with independent RSS sources, Discord webhook, and domain `topic`.
- 🧠 **Triple Evaluation**: DeepSeek scores `relevance_score`, `frontier_score`, and `attention_score`; low-signal content is hard-filtered.
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
        2) Frontier Score (0-10)
        3) Attention Score (0-10)
        4) Hard thresholds -> score=0 if not qualified
   -> Candidate Ranking (composite score)
   -> Discord Push (discord_pusher.py)
   -> Insert Link to DB (on successful push)
```

Core modules:
- `main.py`: orchestration and channel routing
- `rss_parser.py`: feed fetch, parsing, time-window filtering
- `ai_processor.py`: DeepSeek prompt + scoring + structured extraction
- `discord_pusher.py`: markdown message formatting + webhook push
- `db_manager.py`: Turso HTTP pipeline API (init/check/insert)

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

### 4) Inline module tests

```bash
python rss_parser.py
python db_manager.py
python ai_processor.py
python discord_pusher.py
```

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

1. **Submit high-quality RSS sources**
   - Add trustworthy sources to the proper channel in `main.py`.
2. **Improve the system prompt**
   - Tune `SYSTEM_PROMPT_TEMPLATE` in `ai_processor.py` to improve relevance and summary quality.
3. **Add new channels**
   - Example: Digital Twin, WebAssembly, Robotics, Cybersecurity.
4. **Open Issues / PRs**
   - Bug reports, feature requests, prompt experiments, and architecture improvements are all welcome.

---

## Community

- 💬 Discord: https://discord.gg/j556gmgY4
- 📧 Email: w1849619997@gmail.com
- 🐛 Issues: https://github.com/Awfp1314/RSS-Distiller/issues

---

## License

MIT License.
