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
import requests
import urllib3

# 禁用 requests 的 SSL 验证警告，保持日志整洁
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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


def _is_arxiv_source(source_url: str) -> bool:
    return "arxiv.org/rss/" in (source_url or "")


def _keyword_signal_score(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    keyword_weights = {
        "state-of-the-art": 4,
        "sota": 3,
        "benchmark": 3,
        "code": 2,
        "github": 2,
        "dataset": 2,
        "leaderboard": 2,
        "evaluation": 1,
        "inference": 2,
        "efficiency": 2,
        "reasoning": 2,
        "multimodal": 2,
        "agent": 1,
        "rl": 1,
        "distillation": 2,
    }
    score = 0
    for key, weight in keyword_weights.items():
        if key in text:
            score += weight
    return score


def _select_articles_for_source(
    source_articles: List[Dict[str, Any]],
    source_url: str,
    max_items_per_source: int,
) -> List[Dict[str, Any]]:
    """
    通用源默认按最新截断；arXiv 使用分层采样，兼顾“最新”与“潜在高价值尾部”。
    """
    if max_items_per_source <= 0:
        return source_articles

    if not _is_arxiv_source(source_url):
        return source_articles[:max_items_per_source]

    if len(source_articles) <= max_items_per_source:
        return source_articles

    fresh_quota = max(10, int(max_items_per_source * 0.5))
    quality_quota = max(8, int(max_items_per_source * 0.35))
    explore_quota = max_items_per_source - fresh_quota - quality_quota
    if explore_quota < 0:
        explore_quota = 0

    selected: List[Dict[str, Any]] = []
    selected_links = set()

    def _append_unique(items: List[Dict[str, Any]]) -> None:
        for item in items:
            link = item.get("link", "")
            if link and link in selected_links:
                continue
            selected.append(item)
            if link:
                selected_links.add(link)
            if len(selected) >= max_items_per_source:
                return

    # 1) 新鲜层：优先保证最新内容
    _append_unique(source_articles[:fresh_quota])
    if len(selected) >= max_items_per_source:
        return selected[:max_items_per_source]

    # 2) 质量层：从中后段按关键词信号提分，补足可能的高质量尾部
    mid_tail = source_articles[fresh_quota:]
    scored_mid_tail = sorted(
        mid_tail,
        key=lambda item: _keyword_signal_score(item.get("title", ""), item.get("summary", "")),
        reverse=True,
    )
    _append_unique(scored_mid_tail[:quality_quota])
    if len(selected) >= max_items_per_source:
        return selected[:max_items_per_source]

    # 3) 探索层：从剩余内容按步长抽样，避免长期固定盲区
    remaining = [
        item for item in source_articles
        if not item.get("link") or item.get("link") not in selected_links
    ]
    if remaining and explore_quota > 0:
        step = max(1, len(remaining) // explore_quota)
        exploratory = remaining[::step][:explore_quota]
        _append_unique(exploratory)

    return selected[:max_items_per_source]


def fetch_and_filter_rss(rss_urls: List[str], max_items_per_source: int = 30) -> List[Dict[str, Any]]:
    """
    抓取指定的 RSS 源，并过滤出 24 小时内的文章。

    参数:
        rss_urls: RSS 订阅源 URL 列表
        max_items_per_source: 每个源最多保留的文章数

    返回:
        List[Dict]: 包含标题、链接、纯文本摘要、发布时间的文章字典列表
    """
    if not rss_urls:
        print("[警告] RSS URL 列表为空")
        return []
    
    filtered_articles: List[Dict[str, Any]] = []
    
    # 获取当前 UTC 时间
    now_utc = datetime.now(timezone.utc)
    time_limit = timedelta(hours=24)

    for url in rss_urls:
        if not url or not isinstance(url, str):
            print(f"[警告] 跳过无效的 RSS URL: {url}")
            continue
            
        print(f"[RSS] 正在解析: {url}")
        source_articles: List[Dict[str, Any]] = []
        try:
            # 伪装请求头，模拟真实浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # 使用 requests 先抓取原始数据，忽略 SSL 验证，增加超时控制
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            
            if response.status_code != 200:
                print(f"  -> [请求失败] HTTP 状态码: {response.status_code}")
                continue
                
            # 将获取到的原始内存数据交给 feedparser 解析
            feed = feedparser.parse(response.content)
            
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
                    source_name = feed.feed.get("title", "Unknown Source")

                    source_articles.append({
                        "title": title,
                        "link": link,
                        "summary": clean_summary,
                        "published_time": article_utc_date.isoformat(),
                        "source_name": source_name,
                        "source_url": url,
                    })

            source_articles.sort(key=lambda item: item.get("published_time", ""), reverse=True)
            selected_articles = _select_articles_for_source(
                source_articles,
                source_url=url,
                max_items_per_source=max_items_per_source,
            )
            filtered_articles.extend(selected_articles)
                    
        except Exception as e:
            print(f"[错误] 处理订阅源 {url} 失败: {e}")

    return filtered_articles
