import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.discord_pusher import push_to_discord

if __name__ == "__main__":
    load_dotenv()

    print("=" * 50)
    print("discord_pusher.py 功能验证")
    print("=" * 50)

    mock_article = {
        "title": "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化",
        "link": "https://www.unrealengine.com/en-US/blog/unreal-engine-5-4-released"
    }

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
    test_webhook = os.environ.get("DISCORD_WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK_AI")

    if test_webhook:
        success = push_to_discord(mock_article, mock_ai_result, test_webhook)
        if success:
            print("\n测试通过！请查看你的 Discord 频道，检查排版效果是否满意。")
        else:
            print("\n推送失败，请检查请求日志。")
    else:
        print("\n测试失败，未在 .env 中找到 DISCORD_WEBHOOK_URL 或 DISCORD_WEBHOOK_AI。")
