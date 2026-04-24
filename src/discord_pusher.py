"""
discord_pusher.py - Discord 格式化推送模块

功能：
- 接收文章基础信息和 AI 提炼结果
- 严格按照预定的 Markdown 模板格式化文本
- 通过 Webhook 动态推送到对应的 Discord 频道
"""

from typing import Any, Dict

import requests


def push_to_discord(article_data: Dict[str, Any], ai_result: Dict[str, Any], webhook_url: str) -> bool:
    """
    将处理后的文章推送到 Discord。

    参数:
        article_data: 包含 'title' 和 'link' 的原文数据
        ai_result: 包含 'score', 'bullet_points', 'impact_analysis' 的 AI 解析结果
        webhook_url: 目标频道的动态 Webhook URL

    返回:
        bool: 推送是否成功。主流程将依据此结果决定是否将 link 写入 Turso 数据库防重。
    """
    if not webhook_url:
        print("  -> [错误] 未传入有效的 Webhook URL！")
        return False

    title = article_data.get("title", "未知标题")
    link = article_data.get("link", "#")
    
    score = ai_result.get("score", 0)
    translated_title = ai_result.get("translated_title", title)
    bullet_points = ai_result.get("bullet_points", [])
    impact_analysis = ai_result.get("impact_analysis", "No analysis / 无分析。")

    # 容错：确保 bullet_points 至少有 3 项，避免索引越界
    while len(bullet_points) < 3:
        bullet_points.append("No data / 无")

    # 严格遵循需求文档的排版模板，包含手机端分割线防折行优化与链接防预览膨胀 (双语版)
    markdown_content = (
        f"🔥 **[{title}]** (AI Score: {score}/10)\n"
        f"🇨🇳 **[{translated_title}]**\n\n"
        f"📝 **Key Takeaways / 核心速览**：\n"
        f"• {bullet_points[0]}\n"
        f"• {bullet_points[1]}\n"
        f"• {bullet_points[2]}\n\n"
        f"💡 **Impact Analysis / 深度分析**：\n"
        f"{impact_analysis}\n\n"
        f"🔗 **Link / 原文链接**：<{link}>\n\n"
        f"━━━━━━━━━━━━━━━"
    )

    payload = {
        "content": markdown_content
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print(f"  -> [推送成功] 频道已接收: {title}")
            return True
        else:
            print(f"  -> [推送失败] Discord 返回状态码 {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"  -> [推送异常] 网络或请求错误: {e}")
        return False
