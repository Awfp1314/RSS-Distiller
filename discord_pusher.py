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


# ============================================================
# 测试入口：验证 Discord Webhook 连通性及排版格式
# ============================================================
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("=" * 50)
    print("discord_pusher.py 功能验证")
    print("=" * 50)

    # 模拟模块 1 传递过来的文章基础数据
    mock_article = {
        "title": "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化",
        "link": "https://www.unrealengine.com/en-US/blog/unreal-engine-5-4-released"
    }

    # 模拟模块 3 传递过来的 AI 提炼结果
    mock_ai_result = {
        "score": 9,
        "core_breakthrough": "虚幻引擎5.4通过局部动作匹配和Nanite优化，显著提升了动画效率和渲染性能。",
        "bullet_points": [
            "局部动作匹配系统减少动画师手动调整工作量，实现更自然的角色动画。",
            "Nanite渲染管线优化，提升主机平台帧率表现，降低硬件门槛。",
            "新版本引入更高效的资源管理和内存使用，改善开发流程。"
        ],
        "impact_analysis": "技术难点在于局部动作匹配的实时计算和与现有动画系统的兼容性；行业影响上，将加速高保真游戏开发，尤其利好主机平台，可能推动更多中小团队采用虚幻引擎。"
    }

    print("\n尝试向 Discord 发送测试排版消息...")
    # 从环境获取测试 URL，这里为了测试兼容旧变量名 DISCORD_WEBHOOK_URL 或新的 _AI
    test_webhook = os.environ.get("DISCORD_WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK_AI")
    
    if test_webhook:
        success = push_to_discord(mock_article, mock_ai_result, test_webhook)
        if success:
            print("\n测试通过！请查看你的 Discord 频道，检查排版效果是否满意。")
        else:
            print("\n推送失败，请检查请求日志。")
    else:
        print("\n测试失败，未在 .env 中找到 DISCORD_WEBHOOK_URL 或 DISCORD_WEBHOOK_AI。")
