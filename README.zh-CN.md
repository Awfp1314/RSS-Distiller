# RSS Distiller 🔬

<div align="center">

[![Daily AI News Pusher](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml/badge.svg)](https://github.com/Awfp1314/RSS-Distiller/actions/workflows/daily_push.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/j556gmgY4)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Awfp1314/RSS-Distiller/pulls)

**在信息爆炸时代，我们不需要更多资讯 - 我们需要更精准的过滤。**

[English](README.md) | [简体中文](README.zh-CN.md)

[加入社区](https://discord.gg/j556gmgY4) · [提交 Issue](https://github.com/Awfp1314/RSS-Distiller/issues/new) · [发起 PR](https://github.com/Awfp1314/RSS-Distiller/pulls)

</div>

---

## 项目简介

RSS Distiller 是一个基于 DeepSeek AI 的技术情报自动过滤与分发系统。

它会定时抓取 RSS 文章，并执行**双重评估机制**：
- 第一步：**Relevance Check（领域相关性硬过滤）**，不相关直接 `score=0` 丢弃。
- 第二步：**Quality Score（内容质量评分）**，仅高分文章进入推送。

最终，系统把高价值内容整理为中英双语摘要并推送到 Discord 对应频道。

---

## 核心特性

- 🎯 **领域路由**：`CHANNELS_CONFIG` 支持多频道配置，不同频道拥有独立 RSS、Webhook 与 topic。
- 🧠 **双重评估**：先相关性、后质量，避免“高质量但不相关”的内容污染频道。
- 🌐 **双语输出**：自动生成中英双语标题、要点和影响分析。
- 🔁 **防重推送**：基于 Turso 数据库存储已推送链接，杜绝重复消息。
- ⚙️ **零成本部署**：通过 GitHub Actions 定时运行，无需常驻服务器。

---

## 架构说明

```text
RSS 源
   -> 24小时过滤（rss_parser.py）
   -> 数据库查重（db_manager.py / Turso）
   -> AI 评估（ai_processor.py）
        1) Relevance Check 硬过滤（不相关 score=0）
        2) Quality Score 质量评分
   -> Discord 推送（discord_pusher.py）
   -> 推送成功后写回数据库防重
```

---

## 快速开始

### 1) 安装

```bash
git clone https://github.com/Awfp1314/RSS-Distiller.git
cd RSS-Distiller
pip install -r requirements.txt
```

### 2) 配置环境变量

```bash
cp .env.example .env
```

在 `.env` 中填写：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxx

TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-token

DISCORD_WEBHOOK_AI=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_UE=https://discord.com/api/webhooks/...
```

### 3) 运行

```bash
python main.py
```

---

## 参与贡献

欢迎加入“硬核技术情报共建计划”：

1. 提交高质量 RSS 订阅源
2. 优化 `ai_processor.py` 中的 `SYSTEM_PROMPT_TEMPLATE`
3. 新增频道（如数字孪生、机器人、网络安全等）
4. 通过 Issue 或 PR 参与协作

---

## 社区与联系

- 💬 Discord 社区：https://discord.gg/j556gmgY4
- 📧 联系邮箱：w1849619997@gmail.com
- 🐛 问题反馈：https://github.com/Awfp1314/RSS-Distiller/issues

---

## 许可证

MIT License。
