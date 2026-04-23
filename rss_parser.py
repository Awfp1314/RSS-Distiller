"""
rss_parser.py - RSS 数据获取与基础过滤模块

功能：
- 接收 RSS URL 列表并解析
- 提取标题、链接、摘要、发布时间
- 处理时区问题，转换为 UTC 时间
- 过滤并仅保留过去 24 小时内发布的条目
"""

import calendar
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import feedparser


def _strip_html(html_str: str) -> str:
    """
    轻量级移除字符串中的 HTML 标签，提取纯文本摘要。
    符合“简单优先”原则，不引入 BeautifulSoup 等重型库。
    """
    if not html_str:
        return ""
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", html_str)
    # 简单清理多余空白符
    return " ".join(text.split())


def fetch_and_filter_rss(rss_urls: List[str]) -> List[Dict[str, Any]]:
    """
    抓取指定的 RSS 源，并过滤出 24 小时内的文章。

    参数:
        rss_urls: RSS 订阅源 URL 列表

    返回:
        List[Dict]: 包含标题、链接、纯文本摘要、发布时间的文章字典列表
    """
    filtered_articles: List[Dict[str, Any]] = []
    
    # 获取当前 UTC 时间
    now_utc = datetime.now(timezone.utc)
    time_limit = timedelta(hours=24)

    for url in rss_urls:
        print(f"[RSS] 正在解析: {url}")
        try:
            # feedparser.parse 会自动处理很多网络和格式异常
            feed = feedparser.parse(url)
            
            if feed.bozo and hasattr(feed, "bozo_exception"):
                print(f"  -> [警告] 源解析异常 (可能不规范): {feed.bozo_exception}")
                # 注意：即使 bozo 为 1，feedparser 通常也会尽力解析出 entries，因此继续处理

            for entry in feed.entries:
                title = entry.get("title", "无标题")
                link = entry.get("link", "")

                # 优先取 published_parsed，没有则取 updated_parsed
                # feedparser 解析出的 parsed 时间结构体统一被转换为 UTC 视角的 time.struct_time
                parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
                
                if not parsed_time:
                    print(f"  -> [跳过] 无法提取时间: {title}")
                    continue

                try:
                    # 将 time.struct_time 转换为 UTC timestamp
                    timestamp = calendar.timegm(parsed_time)
                    # 转换为带 UTC 时区信息的 datetime 对象
                    article_utc_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except Exception as e:
                    print(f"  -> [跳过] 时间转换失败 ({title}): {e}")
                    continue

                # 核心逻辑：时间对比，判断是否超过 24 小时
                age = now_utc - article_utc_date
                
                # 如果发布时间在未来（偶尔有的源时间设置错误），或者距今 24 小时内，则保留
                if timedelta(seconds=0) <= age <= time_limit or age < timedelta(seconds=0):
                    # 获取摘要，有些 RSS 用 summary，有些用 description
                    raw_summary = entry.get("summary") or entry.get("description") or ""
                    clean_summary = _strip_html(raw_summary)

                    filtered_articles.append({
                        "title": title,
                        "link": link,
                        "summary": clean_summary,
                        "published_time": article_utc_date.isoformat()
                    })
                    
        except Exception as e:
            print(f"[错误] 处理订阅源 {url} 失败: {e}")

    return filtered_articles


# ============================================================
# 测试入口：验证 RSS 抓取、时间解析和 24 小时过滤逻辑
# ============================================================
if __name__ == "__main__":
    # 配置测试 RSS 源
    # Unreal Engine 官方博客更新较慢，为确保能测出 24h 内的数据，加上高频更新的 Hacker News
    TEST_URLS = [
        "https://www.unrealengine.com/en-US/rss",  # 虚幻引擎官方 RSS
        "https://news.ycombinator.com/rss",        # Hacker News (作为兜底高频源)
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
        
        # 为了避免打印太多刷屏，测试时最多只打印前 5 条
        if idx >= 5:
            if len(results) > 5:
                print(f"... 还有 {len(results) - 5} 篇文章被隐藏 ...")
            break

    print("\n测试完成。请确认上述文章的发布时间是否都在当前 UTC 时间的 24 小时以内。")
