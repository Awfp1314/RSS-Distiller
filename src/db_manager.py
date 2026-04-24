"""
db_manager.py - Turso 数据库交互模块

通过 Turso HTTP Pipeline API 实现：
- 建表（articles 表，link 为主键）
- 查询链接是否已存在（防重）
- 插入新链接（推送成功后调用）

使用 requests 直接调用 HTTP API，不引入 ORM 或额外抽象。
"""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

# 本地开发时从 .env 加载环境变量，GitHub Actions 中由 secrets 提供
load_dotenv()

# --- 配置 ---
# libsql:// 开头的 URL 需转换为 https:// 才能调用 HTTP API
_raw_url = os.environ.get("TURSO_DATABASE_URL", "")
TURSO_API_URL = _raw_url.replace("libsql://", "https://") + "/v2/pipeline"
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")


def _execute(sql: str, args: Optional[list] = None) -> dict:
    """
    向 Turso HTTP Pipeline API 发送单条 SQL 语句并返回结果。

    参数:
        sql:  要执行的 SQL 语句
        args: 可选的参数列表，每个元素为 {"type": "text", "value": "..."} 格式

    返回:
        Turso API 返回的完整 JSON（包含 results 数组）

    异常:
        如果 HTTP 状态码非 200 或 API 返回错误，则抛出 RuntimeError。
    """
    # 构造 pipeline 请求体：一条 execute + 一条 close
    stmt = {"sql": sql}
    if args:
        stmt["args"] = args

    payload = {
        "requests": [
            {"type": "execute", "stmt": stmt},
            {"type": "close"},
        ]
    }

    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    resp = requests.post(TURSO_API_URL, json=payload, headers=headers, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Turso API 请求失败 (HTTP {resp.status_code}): {resp.text}"
        )

    data = resp.json()

    # 检查 pipeline 中第一条语句是否执行成功
    first_result = data.get("results", [{}])[0]
    if first_result.get("type") == "error":
        error_info = first_result.get("error", {})
        raise RuntimeError(
            f"Turso SQL 执行错误: {error_info.get('message', '未知错误')}"
        )

    return data


def init_db():
    """
    创建 articles 表（如果不存在）。
    表结构：link TEXT PRIMARY KEY
    """
    _execute("CREATE TABLE IF NOT EXISTS articles (link TEXT PRIMARY KEY)")
    print("[DB] articles 表已就绪。")


def link_exists(link: str) -> bool:
    """
    查询指定链接是否已存在于数据库中。

    参数:
        link: 文章的 URL

    返回:
        True 表示已存在（之前推送过），False 表示不存在
    """
    data = _execute(
        "SELECT link FROM articles WHERE link = ?",
        [{"type": "text", "value": link}],
    )

    # 从 pipeline 响应中提取第一条语句的执行结果
    # 结构: results[0] -> response -> result -> rows
    rows = (
        data.get("results", [{}])[0]
        .get("response", {})
        .get("result", {})
        .get("rows", [])
    )
    return len(rows) > 0


def insert_link(link: str):
    """
    将链接插入 articles 表。
    使用 INSERT OR IGNORE 避免主键冲突时报错。

    参数:
        link: 文章的 URL
    """
    _execute(
        "INSERT OR IGNORE INTO articles (link) VALUES (?)",
        [{"type": "text", "value": link}],
    )
    print(f"[DB] 已插入链接: {link}")
