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

它会定时抓取 RSS 文章，并执行**三重评估机制**：
- 第一步：**Relevance Score（领域相关性）**
- 第二步：**Frontier Score（前沿性）**
- 第三步：**Attention Score（关注度）**

若任一核心指标不达标，内容会被硬过滤（`score=0`）直接丢弃。

最终，系统把高价值内容整理为中英双语摘要并推送到 Discord 对应频道。

---

## 核心特性

- 🎯 **领域路由**：`CHANNELS_CONFIG` 支持多频道配置，不同频道拥有独立 RSS、Webhook 与 topic。
- 🧠 **三重评估**：相关性 + 前沿性 + 关注度联合判定，低信号内容硬过滤。
- 🌐 **双语输出**：自动生成中英双语标题、要点和影响分析。
- 🔁 **防重推送**：基于 Turso 数据库存储已推送链接，杜绝重复消息。
- 📉 **单源限流**：按源设置候选上限，避免单一 RSS 源淹没候选池。
- 🧪 **arXiv 分层采样**：兼顾最新内容、中后段潜在高价值条目和探索抽样，降低漏报风险。
- 🏁 **Top-K 推送**：按综合分排序后仅推送每轮最有价值候选。
- ⚙️ **零成本部署**：通过 GitHub Actions 定时运行，无需常驻服务器。

---

## 架构说明

```text
RSS 源
   -> 24小时过滤（rss_parser.py）
   -> 数据库查重（db_manager.py / Turso）
   -> AI 评估（ai_processor.py）
        1) Relevance Score 相关性
        2) Frontier Score 前沿性
        3) Attention Score 关注度
        4) 未达阈值硬过滤（score=0）
   -> 候选排序（综合分）
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

## GitHub Actions 部署

工作流文件：
- `.github/workflows/daily_push.yml`（每日资讯抓取与推送）
- `.github/workflows/changelog_notify.yml`（推送提交更新到 Discord `#changelog`）

- 定时触发时区说明：当前 cron 使用 `UTC`，工作流触发后会立即通过 Webhook 推送；不会按每位用户本地时区统一在早上 8 点送达。

需要在仓库 `Settings -> Secrets and variables -> Actions` 中配置：
- `DEEPSEEK_API_KEY`
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`
- `DISCORD_WEBHOOK_AI`
- `DISCORD_WEBHOOK_UE`
- `DISCORD_WEBHOOK_CHANGELOG`

`changelog_notify.yml` 会监听 `main` 分支的 `push` 事件，并自动发送提交摘要（作者、提交数量、短 SHA + 提交标题、compare 链接、工作流运行链接）到更新记录频道。

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
