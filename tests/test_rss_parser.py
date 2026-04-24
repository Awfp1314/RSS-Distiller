import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime, timezone
from src.rss_parser import fetch_and_filter_rss

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
    print("=" * 50)
    print("rss_parser.py 功能验证")
    print("=" * 50)

    configs = load_configs()
    print(f"加载了 {len(configs)} 个配置文件\n")

    now = datetime.now(timezone.utc)
    print(f"当前 UTC 时间: {now.isoformat()}")
    print("抓取并筛选 24 小时内的文章...\n")

    for config in configs:
        print("=" * 50)
        print(f"测试配置: {config['_filename']} - {config['channel_name']}")
        print("=" * 50)
        print(f"RSS 源数量: {len(config['rss_urls'])}")
        print(f"max_items_per_source: {config['max_items_per_source']}")
        
        results = fetch_and_filter_rss(
            config['rss_urls'], 
            max_items_per_source=config['max_items_per_source']
        )

        print(f"\n[结果] 共提取到 {len(results)} 篇 24 小时内的有效文章:")
        print("-" * 50)

        for idx, article in enumerate(results, 1):
            try:
                published_time = datetime.fromisoformat(article['published_time'])
                age_hours = (now - published_time).total_seconds() / 3600
                age_display = f"{age_hours:.1f}h ago"
            except Exception:
                age_display = "unknown"
            
            print(f"{idx}. {article['title']}")
            print(f"   发布时间: {article['published_time']} ({age_display})")
            print(f"   来源: {article.get('source_name', 'Unknown')}")
            print(f"   文章链接: {article['link']}")
            print(f"   摘要摘录: {article['summary'][:60]}...")
            print("-" * 50)

            if idx >= 3:
                if len(results) > 3:
                    print(f"... 还有 {len(results) - 3} 篇文章被隐藏 ...")
                break

        print()

    print("\n测试完成。请确认：")
    print("  1. 所有文章的发布时间都在 24 小时以内")
    print("  2. published_time 字段格式正确（ISO 8601 格式）")
    print("  3. 文章年龄计算正确")
    print("  4. 每个配置的 RSS 源都能正常抓取")
