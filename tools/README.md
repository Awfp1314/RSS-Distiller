# 🛠️ RSS Distiller 社区工具集

这个目录包含用于社区贡献和管理的工具。

## 📁 文件说明

### 用户端工具

- **`QUICK_START.md`** - 快速开始指南（推荐）
  - 包含一键复制的 AI 提示词
  - 最简单的使用方式
  
- **`USER_PROMPT.md`** - 详细使用说明
  - 完整的使用流程
  - 常见问题解答
  
- **`channel_config_generator_prompt.md`** - AI 助手提示词（技术文档）
  - 给 AI 的完整指令
  - 开发者参考

### 管理员工具

- **`validate_config.py`** - 配置验证工具
  - 验证 JSON 格式和字段
  - 检查 RSS 源可访问性
  - 检测配置冲突
  
- **`add_channel.py`** - 快速添加频道
  - 自动验证配置
  - 生成文件名
  - 提交到 Git

## 🚀 用户使用流程

### 第一步：生成配置

1. 打开 `QUICK_START.md`
2. 复制提示词
3. 发送给任何 AI（ChatGPT/Claude/Kimi）
4. 回答 AI 的问题
5. 获得标准 JSON 配置

### 第二步：提交到 Discord

1. 前往 Discord 论坛的 `#rss-suggestions` 频道
2. 创建新帖子
3. 标题格式：`[新频道] 你的频道名称`
4. 粘贴 AI 生成的 JSON 配置
5. 等待管理员审核

### 示例帖子

```
标题：[新频道] Rust前沿资讯

内容：
{
  "channel_name": "Rust前沿资讯",
  "rss_urls": [
    "https://blog.rust-lang.org/feed.xml",
    "https://this-week-in-rust.org/rss.xml"
  ],
  "webhook_env": "DISCORD_WEBHOOK_RUST",
  "topic": "Rust Programming Language, Systems Programming, Memory Safety",
  "max_items_per_source": 30,
  "max_push_per_run": 8,
  "time_decay_gravity": 1.8,
  "time_decay_halflife": 6,
  "min_scores": {
    "relevance": 7,
    "quality": 7
  },
  "evaluation_focus": {
    "relevance_criteria": [
      "Official Rust releases or RFC announcements",
      "Performance improvements or language feature proposals",
      "Production case studies from major projects"
    ],
    "quality_indicators": [
      "Includes code examples or benchmarks",
      "Discusses technical trade-offs and design decisions",
      "Provides actionable insights for Rust developers"
    ],
    "reject_patterns": [
      "Beginner tutorials or getting started guides",
      "Q&A posts without solutions",
      "Opinion pieces without technical depth"
    ]
  }
}
```

## 🔧 管理员使用流程

### 验证用户提交的配置

```bash
# 基本验证
python tools/validate_config.py user_config.json

# 验证 + 检查 RSS 源可访问性
python tools/validate_config.py --check-urls user_config.json
```

输出示例：
```
============================================================
RSS Distiller 配置验证工具
============================================================

📄 配置文件: user_config.json
📋 频道名称: Rust前沿资讯
🔗 RSS 源数量: 2

🔍 验证配置结构...
✅ 配置结构验证通过

🌐 验证 RSS 源可访问性...

  [1/2] https://blog.rust-lang.org/feed.xml
    ✅ OK

  [2/2] https://this-week-in-rust.org/rss.xml
    ✅ OK

🔍 检查配置冲突...
✅ 无配置冲突

📝 建议配置：
  文件名: configs/Rust.json
  环境变量: DISCORD_WEBHOOK_RUST
  需要在 GitHub Secrets 中配置对应的 Webhook URL

============================================================
✅ 验证完成！配置可以使用。
============================================================
```

### 添加配置到项目

```bash
# 从文件添加
python tools/add_channel.py user_config.json

# 从 JSON 字符串添加
python tools/add_channel.py '{"channel_name": "..."}'
```

工具会：
1. ✅ 验证配置
2. 📝 写入 `configs/` 目录
3. 💡 提示需要配置的环境变量
4. 🔄 询问是否立即提交到 Git

### 配置 GitHub Secrets

1. 前往 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加：
   - Name: `DISCORD_WEBHOOK_RUST`（根据配置中的 webhook_env）
   - Value: `https://discord.com/api/webhooks/...`（Discord Webhook URL）

### 更新 GitHub Actions 工作流

编辑 `.github/workflows/daily_push.yml`，在 `env` 部分添加：

```yaml
env:
  DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
  # ... 其他现有配置 ...
  DISCORD_WEBHOOK_RUST: ${{ secrets.DISCORD_WEBHOOK_RUST }}  # 新增
```

### 提交并推送

```bash
git push
```

## 📋 配置字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `channel_name` | string | 频道名称 | "Rust前沿资讯" |
| `rss_urls` | array | RSS 源列表 | ["https://..."] |
| `webhook_env` | string | 环境变量名 | "DISCORD_WEBHOOK_RUST" |
| `topic` | string | 主题关键词（英文） | "Rust, Systems Programming" |
| `max_items_per_source` | int | 每个源最多抓取数 | 30 |
| `max_push_per_run` | int | 每次最多推送数 | 8 |
| `time_decay_gravity` | float | 时间衰减强度 | 1.8 |
| `time_decay_halflife` | float | 半衰期（小时） | 6 |
| `min_scores.relevance` | int | 相关性最低分 | 7 |
| `min_scores.quality` | int | 质量最低分 | 7 |
| `evaluation_focus` | object | 评分标准 | 见示例 |

## 🎯 参数推荐值

### 推送频率

- **保守型**：`max_push_per_run: 5`（精选）
- **平衡型**：`max_push_per_run: 8`（推荐）
- **激进型**：`max_push_per_run: 12`（快速追踪）

### 时间衰减

- **极高**：`gravity: 2.0, halflife: 4`（只要最新）
- **高**：`gravity: 1.8, halflife: 6`（偏好新内容）
- **中等**：`gravity: 1.5, halflife: 12`（平衡）
- **低**：`gravity: 1.2, halflife: 24`（质量优先）
- **无**：`gravity: 0`（不考虑时间）

### 评分阈值

- **严格**：`relevance: 8, quality: 8`（最高质量）
- **标准**：`relevance: 7, quality: 7`（推荐）
- **宽松**：`relevance: 6, quality: 6`（更多候选）

## 🐛 故障排查

### 配置验证失败

**问题**：`缺少必填字段: evaluation_focus`

**解决**：确保 JSON 包含所有必填字段，使用 AI 生成的配置通常不会有这个问题。

### RSS 源无法访问

**问题**：`连接失败` 或 `请求超时`

**解决**：
1. 检查 URL 是否正确
2. 尝试在浏览器中打开
3. 某些源可能需要特定的 User-Agent

### webhook_env 冲突

**问题**：`webhook_env 冲突: AI.json`

**解决**：选择不同的 webhook_env 名称，如 `DISCORD_WEBHOOK_RUST2`

## 📞 获取帮助

- Discord: https://discord.gg/j556gmgY4
- GitHub Issues: https://github.com/Awfp1314/RSS-Distiller/issues
- Email: w1849619997@gmail.com
