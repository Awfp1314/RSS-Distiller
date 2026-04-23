# RSS Distiller 🔬

<div align="center">

[![Daily AI News Pusher](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml/badge.svg)](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/j556gmgY4)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Awfp1314/RSS-Distiller/pulls)

**在信息爆炸时代，我们不需要更多资讯——我们需要更精准的过滤。**

*In the age of information overload, we don't need more news — we need smarter filters.*

[加入社区 Join Community](https://discord.gg/j556gmgY4) · [提交 RSS 源 Submit RSS](https://github.com/Awfp1314/RSS-Distiller/issues/new) · [优化 Prompt](https://github.com/Awfp1314/RSS-Distiller/pulls)

</div>

---

## 📖 项目简介 Introduction

RSS Distiller 是一个基于 **DeepSeek AI** 的技术情报自动过滤与分发系统。

它每天定时从数十个顶级技术 RSS 源抓取文章，通过 **领域感知双重评估机制（Relevance Check + Quality Score）** 过滤掉与目标领域无关或价值不高的噪音，最终将精炼后的双语摘要自动推送至 Discord 的对应技术频道。

> **为什么需要它？**
> 
> 订阅了 Hacker News、Hugging Face Blog、TechCrunch……结果每天刷到的全是与自己领域无关的内容。RSS Distiller 解决的核心问题是：**让 AI 替你读，只给你送真正有用的**。

RSS Distiller is an AI-powered tech news filtering and distribution system. It fetches articles from top RSS feeds daily, applies a **topic-aware dual evaluation** (relevance hard-filter + quality scoring) to eliminate noise, and pushes bilingual summaries to dedicated Discord channels automatically.

---

## ✨ 核心特性 Key Features

| 特性 | 说明 |
|---|---|
| 🎯 **领域路由** | `CHANNELS_CONFIG` 支持多频道独立分发，每个频道拥有独立的 RSS 源、`topic` 领域描述和 Discord Webhook，目前覆盖 AI 前沿资讯和虚幻引擎开发，可无限扩展。 |
| 🧠 **双重评估** | 第一步 Relevance Check 硬过滤：与目标 `topic` 无关的文章直接返回 `score=0` 丢弃；第二步 Quality Score 评估内容深度，阈值 ≥ 7 分方可推送。 |
| 🌐 **双语输出** | 自动生成中英对照标题、核心突破、3 条要点速览和深度影响分析，无需人工翻译。 |
| 🔁 **防重推送** | 基于 [Turso](https://turso.tech/) 云边缘数据库，每条推送成功后写入链接记录，同一文章在任何时间都不会重复推送。 |
| ⚙️ **零成本运行** | 完整部署于 GitHub Actions，每天北京时间 08:00 自动触发，无需购置任何服务器。 |

---

## 🏗️ 项目架构 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CHANNELS_CONFIG                    │
│          (AI频道 / 虚幻引擎频道 / 可扩展...)          │
└───────────────────────┬─────────────────────────────┘
                        │ rss_urls + topic
                        ▼
              ┌─────────────────┐
              │   rss_parser    │  feedparser 抓取 + 24h 时间过滤
              └────────┬────────┘
                       │ 24h 内新文章
                       ▼
              ┌─────────────────┐
              │   db_manager    │  Turso HTTP API 防重查询
              └────────┬────────┘
                       │ 未推送过的新文章
                       ▼
              ┌─────────────────┐
              │  ai_processor   │  DeepSeek AI 双重评估
              │                 │
              │  Step 1: 领域   │──→ score=0 → 丢弃 ✗
              │  相关性硬过滤   │
              │                 │
              │  Step 2: 质量   │──→ score<7 → 丢弃 ✗
              │  评分 (1-10)    │
              └────────┬────────┘
                       │ score ≥ 7
                       ▼
              ┌─────────────────┐
              │ discord_pusher  │  Webhook 推送双语格式卡片
              └────────┬────────┘
                       │ 推送成功
                       ▼
              ┌─────────────────┐
              │   db_manager    │  写入 Turso 防重记录
              └─────────────────┘
```

### 模块说明 Module Overview

| 文件 | 职责 |
|---|---|
| `main.py` | 主入口，定义 `CHANNELS_CONFIG` 多频道路由，串联所有模块 |
| `rss_parser.py` | 从 RSS URL 列表抓取文章，处理时区并过滤 24 小时内的条目 |
| `ai_processor.py` | 调用 DeepSeek API，执行领域相关性硬过滤 + 质量评分，返回结构化双语摘要 |
| `discord_pusher.py` | 将 AI 摘要格式化为 Markdown 卡片，通过 Webhook 推送至 Discord |
| `db_manager.py` | 封装 Turso HTTP Pipeline API，提供建表、防重查询、链接写入能力 |

---

## 🚀 快速开始 Quick Start

### 前置条件 Prerequisites

- Python 3.10+
- [DeepSeek API Key](https://platform.deepseek.com/)
- [Turso](https://turso.tech/) 数据库（免费套餐足够）
- Discord 频道 Webhook URL

### 本地运行 Local Setup

```bash
# 1. 克隆仓库
git clone https://github.com/Awfp1314/RSS-Distiller.git
cd RSS-Distiller

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env  # 然后填入你的密钥
```

在 `.env` 中填写以下变量：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxx

TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-token

DISCORD_WEBHOOK_AI=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_UE=https://discord.com/api/webhooks/...
```

```bash
# 4. 运行
python main.py
```

### 模块独立测试 Module Tests

```bash
python rss_parser.py    # 验证 RSS 抓取与 24h 过滤
python db_manager.py    # 验证 Turso 数据库连通性与读写
python ai_processor.py  # 验证 DeepSeek AI 评分与硬过滤
python discord_pusher.py # 验证 Discord Webhook 推送与排版
```

### GitHub Actions 部署 Deploy

1. Fork 本仓库
2. 在 `Settings → Secrets and variables → Actions` 中添加上述所有环境变量
3. 工作流文件 `.github/workflows/daily_push.yml` 已配置好，每天 UTC 00:00（北京时间 08:00）自动运行
4. 也可在 Actions 页面手动触发

---

## 🤝 参与贡献 How to Contribute

我们正在招募**硬核技术情报共建者**。以下是三种最直接的贡献方式：

### 1. 🌐 提交高质量 RSS 订阅源

发现一个高质量的技术 RSS 源？通过 PR 将它加入 `main.py` 的对应频道 `rss_urls` 列表中。

**好的 RSS 源标准：**
- 更新频率稳定（至少每周更新）
- 内容以原创技术文章为主，非聚合转载
- 有明确的技术领域指向

```python
# 示例：在 AI频道 添加一个新订阅源
"rss_urls": [
    ...
    "https://your-new-source.com/feed.xml",  # 来源说明
]
```

### 2. 🧠 优化 AI 评分提示词 (System Prompt)

`ai_processor.py` 中的 `SYSTEM_PROMPT_TEMPLATE` 是过滤质量的核心。如果你有提示词工程经验，欢迎：
- 提高相关性判断的准确率
- 改善双语摘要的表达质量
- 为特定领域设计更精准的评分维度

通过 PR 提交你的 Prompt 改进方案，并在 PR 描述中附上改进前后的对比测试结果。

### 3. 📡 新增技术频道

想订阅数字孪生、WebAssembly、量子计算等领域？在 `CHANNELS_CONFIG` 中新增一个频道条目：

```python
"数字孪生前沿": {
    "rss_urls": [
        "https://example.com/digital-twin/feed",
    ],
    "webhook_env": "DISCORD_WEBHOOK_DT",
    "topic": "Digital Twin, IoT, Industrial Simulation, Metaverse"
}
```

然后提交 PR 并告知你希望加入 Discord 社区的哪个分区。

### 参与流程 Contribution Flow

```
发现问题或想法
    → 搜索现有 Issue，避免重复
    → 新建 Issue（Bug / RSS源推荐 / Prompt优化提案）
    → Fork → 修改 → 提交 PR
    → 等待 Review & 合并
```

---

## 🌍 联系与社区 Community

| 渠道 | 地址 |
|---|---|
| 💬 Discord 社区 | [discord.gg/j556gmgY4](https://discord.gg/j556gmgY4) |
| 📧 联系邮箱 | [w1849619997@gmail.com](mailto:w1849619997@gmail.com) |
| 🐛 Issue 反馈 | [GitHub Issues](https://github.com/Awfp1314/RSS-Distiller/issues) |

---

## 📄 许可证 License

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。

```
MIT License

Copyright (c) 2026 Awfp1314

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

<div align="center">

如果这个项目对你有帮助，请点一个 ⭐ Star，让更多开发者发现它。

*If this project helps you, please give it a ⭐ Star to help others discover it.*

</div>
