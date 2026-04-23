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

RSS Distiller is an AI-powered tech intelligence pipeline that fetches RSS articles, applies a **topic-aware dual evaluation** with DeepSeek (**Relevance Check + Quality Score**), and pushes only high-value bilingual summaries to Discord.

Why it exists:
- Developers subscribe to many sources but still miss signal in noise.
- Generic summarizers rank quality but often ignore domain relevance.
- RSS Distiller adds a **hard relevance filter**: if an article is off-topic for a channel, it gets `score=0` and is dropped.

---

## Key Features

- 🎯 **Topic Routing**: multi-channel routing via `CHANNELS_CONFIG`, each with independent RSS sources, Discord webhook, and domain `topic`.
- 🧠 **Dual Evaluation**: DeepSeek first checks relevance to channel topic; low relevance is hard-filtered (`score=0`), then quality is scored.
- 🌐 **Bilingual Output**: auto-generates EN/ZH title translation, key points, and impact analysis.
- 🔁 **Deduplication**: Turso-backed link storage prevents duplicate pushes.
- ⚙️ **Zero-Cost Scheduling**: GitHub Actions runs daily (and supports manual dispatch).

---

## Architecture

```text
RSS Sources
   -> 24h Time Filter (rss_parser.py)
   -> Link Dedup Check (db_manager.py / Turso)
   -> AI Evaluation (ai_processor.py)
        1) Relevance Check (hard filter, score=0 if off-topic)
        2) Quality Score (1-10)
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

Workflow file: `.github/workflows/daily_push.yml`

- Scheduled run: daily at `00:00 UTC` (08:00 Beijing Time)
- Manual run: `workflow_dispatch`
- Required repository secrets:
  - `DEEPSEEK_API_KEY`
  - `TURSO_DATABASE_URL`
  - `TURSO_AUTH_TOKEN`
  - `DISCORD_WEBHOOK_AI`
  - `DISCORD_WEBHOOK_UE`

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
