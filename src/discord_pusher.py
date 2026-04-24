"""
discord_pusher.py - Discord 格式化推送模块

功能：
- 接收文章基础信息和 AI 提炼结果
- 严格按照预定的 Markdown 模板格式化文本
- 通过 Webhook 动态推送到对应的 Discord 频道
"""

from datetime import datetime, timezone
from typing import Any, Dict

import requests


def push_to_discord(article_data: Dict[str, Any], ai_result: Dict[str, Any], webhook_url: str) -> bool:
    """
    将处理后的文章推送到 Discord。

    参数:
        article_data: 包含 'title' 和 'link' 的原文数据
        ai_result: 包含 'relevance_score', 'quality_score', 'bullet_points', 'impact_analysis' 的 AI 解析结果
        webhook_url: 目标频道的动态 Webhook URL

    返回:
        bool: 推送是否成功。主流程将依据此结果决定是否将 link 写入 Turso 数据库防重。
    """
    if not webhook_url:
        print("  -> [错误] 未传入有效的 Webhook URL！")
        return False

    title = article_data.get("title", "未知标题")
    link = article_data.get("link", "#")
    
    relevance_score = ai_result.get("relevance_score", 0)
    quality_score = ai_result.get("quality_score", 0)
    composite_score = round(relevance_score * 0.4 + quality_score * 0.6, 1)
    
    translated_title = ai_result.get("translated_title", title)
    
    # 新格式：英文和中文分开
    core_breakthrough = ai_result.get("core_breakthrough", "")
    core_breakthrough_cn = ai_result.get("core_breakthrough_cn", "")
    
    bullet_points = ai_result.get("bullet_points", [])
    bullet_points_cn = ai_result.get("bullet_points_cn", [])
    
    impact_analysis = ai_result.get("impact_analysis", "No analysis available.")
    impact_analysis_cn = ai_result.get("impact_analysis_cn", "无分析。")
    
    # 计算文章年龄
    published_time_str = article_data.get("published_time", "")
    age_display = "unknown"
    if published_time_str:
        try:
            published_time = datetime.fromisoformat(published_time_str)
            now_utc = datetime.now(timezone.utc)
            age_hours = (now_utc - published_time).total_seconds() / 3600
            
            # 格式化显示：小于 1 小时显示分钟，否则显示小时
            if age_hours < 1:
                age_minutes = int(age_hours * 60)
                age_display = f"{age_minutes}m ago"
            else:
                age_display = f"{age_hours:.1f}h ago"
        except Exception:
            pass  # 时间解析失败，保持 "unknown"

    # 容错：确保 bullet_points 至少有 3 项，避免索引越界
    while len(bullet_points) < 3:
        bullet_points.append("No data")
    while len(bullet_points_cn) < 3:
        bullet_points_cn.append("无")

    # 优化后的排版：英文/中文分开，紧凑格式（Discord 需要双换行）
    # 末尾添加零宽空格以保持空行（Discord 会去除纯空白）
    markdown_content = (
        f"🔥 **[{title}]** (R:{relevance_score} Q:{quality_score} ≈{composite_score}/10 | {age_display})\n"
        f"🇨🇳 **[{translated_title}]**\n\n\n"
        f"📝 **KEY TAKEAWAYS/核心速览**\n"
        f"• {bullet_points[0]}\n"
        f"• {bullet_points[1]}\n"
        f"• {bullet_points[2]}\n"
        f"• {bullet_points_cn[0]}\n"
        f"• {bullet_points_cn[1]}\n"
        f"• {bullet_points_cn[2]}\n\n\n"
        f"💡 **IMPACT ANALYSIS/深度分析**\n"
        f"💡 {impact_analysis}\n"
        f"💡 {impact_analysis_cn}\n\n\n"
        f"🔗 **ORIGINAL LINK/原文链接**\n"
        f"🔗 <{link}>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"**dividing line**\n"
        f"━━━━━━━━━━━━━━━\n\n\n"
        f"\u200B"  # 零宽空格，防止 Discord 去除末尾空行
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
