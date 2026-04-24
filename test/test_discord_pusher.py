import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.discord_pusher import push_to_discord
from src.rss_parser import fetch_and_filter_rss
from src.ai_processor import evaluate_article

def load_configs():
    """从 configs/ 目录加载所有配置文件"""
    config_dir = Path(__file__).parent.parent / "configs"
    configs = []
    for config_file in config_dir.glob("*.json"):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            config["_filename"] = config_file.name
            configs.append(config)
    return configs

if __name__ == "__main__":
    load_dotenv()

    print("=" * 50)
    print("discord_pusher.py 功能验证")
    print("=" * 50)

    configs = load_configs()
    print(f"\n可用配置:")
    for i, cfg in enumerate(configs, 1):
        print(f"  {i}. {cfg['_filename']} - {cfg['channel_name']}")
    
    print(f"\n请选择配置 (1-{len(configs)}) 或按 Enter 使用模拟数据: ", end="")
    choice = input().strip()
    
    if choice and choice.isdigit() and 1 <= int(choice) <= len(configs):
        # 使用选定的配置
        config = configs[int(choice) - 1]
        print(f"\n使用配置: {config['channel_name']}")
        print("=" * 50)
        
        print(f"\n正在从 RSS 源获取文章...")
        articles = fetch_and_filter_rss(config['rss_urls'], max_items_per_source=5)
        
        if not articles:
            print("未获取到 24 小时内的文章，使用模拟数据。\n")
            use_mock = True
        else:
            print(f"获取到 {len(articles)} 篇文章，开始 AI 评估...\n")
            
            # 评估所有文章，找到第一篇通过筛选的
            test_article = None
            test_result = None
            
            for article in articles:
                print(f"评估: {article['title'][:60]}...")
                result = evaluate_article(
                    article['title'],
                    article['summary'],
                    topic=config['topic'],
                    source_name=article.get('source_name', ''),
                    source_url=article.get('source_url', ''),
                    relevance_min=config['min_scores']['relevance'],
                    quality_min=config['min_scores']['quality'],
                    evaluation_focus=config.get('evaluation_focus')
                )
                
                if result:
                    test_article = article
                    test_result = result
                    print(f"  -> 找到高质量文章 (R:{result['relevance_score']} Q:{result['quality_score']})\n")
                    break
            
            if test_article and test_result:
                use_mock = False
                
                # 获取 webhook URL
                webhook_env = config.get('webhook_env', 'DISCORD_WEBHOOK_URL')
                test_webhook = os.environ.get(webhook_env) or os.environ.get("DISCORD_WEBHOOK_URL")
                
                if not test_webhook:
                    print(f"\n未找到 {webhook_env} 或 DISCORD_WEBHOOK_URL，无法推送。")
                else:
                    print("=" * 50)
                    print("准备推送到 Discord")
                    print("=" * 50)
                    print(f"标题: {test_article['title']}")
                    print(f"链接: {test_article['link']}")
                    print(f"发布时间: {test_article['published_time']}")
                    print(f"相关性评分: {test_result['relevance_score']}/10")
                    print(f"质量评分: {test_result['quality_score']}/10")
                    print(f"综合评分: {test_result['relevance_score'] * 0.4 + test_result['quality_score'] * 0.6:.1f}/10")
                    print(f"翻译标题: {test_result['translated_title']}")
                    
                    success = push_to_discord(test_article, test_result, test_webhook)
                    if success:
                        print("\n✓ 推送成功！请查看你的 Discord 频道。")
                    else:
                        print("\n✗ 推送失败，请检查日志。")
            else:
                print("所有文章都未通过 AI 筛选，使用模拟数据。\n")
                use_mock = True
    else:
        use_mock = True
    
    if use_mock:
        print("\n使用模拟数据")
        print("=" * 50)
        
        # 模拟文章数据（包含发布时间）
        mock_article = {
            "title": "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化",
            "link": "https://www.unrealengine.com/en-US/blog/unreal-engine-5-4-released",
            "published_time": (datetime.now(timezone.utc) - timedelta(hours=2, minutes=30)).isoformat()
        }

        # 模拟 AI 评分结果（使用新的评分维度和分离的英文/中文格式）
        mock_ai_result = {
            "relevance_score": 10,
            "quality_score": 9,
            "translated_title": "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化",
            "core_breakthrough": "Unreal Engine 5.4 introduces Motion Matching and Nanite optimizations",
            "core_breakthrough_cn": "虚幻引擎5.4通过局部动作匹配和Nanite优化，显著提升了动画效率和渲染性能",
            "bullet_points": [
                "Motion Matching system reduces animator workload and enables more natural character animations",
                "Nanite pipeline optimization improves console performance and lowers hardware requirements",
                "Enhanced resource management and memory usage improves development workflow"
            ],
            "bullet_points_cn": [
                "局部动作匹配系统减少动画师手动调整工作量，实现更自然的角色动画",
                "Nanite渲染管线优化，提升主机平台帧率表现，降低硬件门槛",
                "新版本引入更高效的资源管理和内存使用，改善开发流程"
            ],
            "impact_analysis": "Technical challenges include real-time Motion Matching computation; industry impact accelerates high-fidelity game development",
            "impact_analysis_cn": "技术难点在于局部动作匹配的实时计算和与现有动画系统的兼容性；行业影响上，将加速高保真游戏开发，尤其利好主机平台"
        }

        print("\n尝试向 Discord 发送测试排版消息...")
        print(f"模拟文章发布时间: {mock_article['published_time']}")
        print(f"相关性评分: {mock_ai_result['relevance_score']}/10")
        print(f"质量评分: {mock_ai_result['quality_score']}/10")
        print(f"综合评分: {mock_ai_result['relevance_score'] * 0.4 + mock_ai_result['quality_score'] * 0.6:.1f}/10")
        
        test_webhook = os.environ.get("DISCORD_WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK_AI")

        if test_webhook:
            success = push_to_discord(mock_article, mock_ai_result, test_webhook)
            if success:
                print("\n测试通过！请查看你的 Discord 频道，检查以下内容：")
                print("  1. 评分显示格式: (R:10 Q:9 ≈9.4/10 | 2.5h ago)")
                print("  2. 双语内容格式是否正确")
                print("  3. 链接是否被正确包裹在 <> 中（防止预览）")
            else:
                print("\n推送失败，请检查请求日志。")
        else:
            print("\n测试失败，未在 .env 中找到 DISCORD_WEBHOOK_URL 或 DISCORD_WEBHOOK_AI。")
