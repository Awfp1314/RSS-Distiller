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

    results = fetch_and_filter_rss(TEST_URLS)

    print(f"\n[结果] 共提取到 {len(results)} 篇 24 小时内的有效文章:")
    print("-" * 50)

    for idx, article in enumerate(results, 1):
        print(f"{idx}. {article['title']}")
        print(f"   发布时间: {article['published_time']}")
        print(f"   文章链接: {article['link']}")
        print(f"   摘要摘录: {article['summary'][:60]}...")
        print("-" * 50)

        if idx >= 5:
            if len(results) > 5:
                print(f"... 还有 {len(results) - 5} 篇文章被隐藏 ...")
            break

    print("\n测试完成。请确认上述文章的发布时间是否都在当前 UTC 时间的 24 小时以内。")
