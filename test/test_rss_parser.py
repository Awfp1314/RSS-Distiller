import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from src.rss_parser import fetch_and_filter_rss

if __name__ == "__main__":
    TEST_URLS = [
        "https://www.unrealengine.com/en-US/rss",
        "https://news.ycombinator.com/rss",
    ]

    print("=" * 50)
    print("rss_parser.py 功能验证")
    print("=" * 50)

    now = datetime.now(timezone.utc)
    print(f"当前 UTC 时间: {now.isoformat()}")
    print("抓取并筛选 24 小时内的文章...\n")

    results = fetch_and_filter_rss(TEST_URLS, max_items_per_source=30)

    print(f"\n[结果] 共提取到 {len(results)} 篇 24 小时内的有效文章:")
    print("-" * 50)

    for idx, article in enumerate(results, 1):
        # 计算文章年龄
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

        if idx >= 5:
            if len(results) > 5:
                print(f"... 还有 {len(results) - 5} 篇文章被隐藏 ...")
            break

    print("\n测试完成。请确认：")
    print("  1. 所有文章的发布时间都在 24 小时以内")
    print("  2. published_time 字段格式正确（ISO 8601 格式）")
    print("  3. 文章年龄计算正确")
