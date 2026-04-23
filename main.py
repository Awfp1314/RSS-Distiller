"""
main.py - 自动化资讯推送器主入口

功能：
- 采用字典路由模式支持多频道推送
- 串联四大模块，实现"RSS 获取 -> 数据库防重 -> AI 打分过滤 -> 动态 Discord 推送 -> 数据库更新"的完整业务闭环。
"""

import os

from dotenv import load_dotenv

from ai_processor import evaluate_article
from db_manager import init_db, insert_link, link_exists
from discord_pusher import push_to_discord
from rss_parser import fetch_and_filter_rss

# 加载环境变量（必须尽早调用，确保能读到包含 webhook_env 在内的变量）
load_dotenv()

# ============================================================
# 多频道路由配置字典 (Dictionary Routing)
# ============================================================
CHANNELS_CONFIG = {
    "AI前沿资讯": {
        "rss_urls": [
            "https://openai.com/blog/rss.xml",                                 # OpenAI 官方博客 RSS（稳定可抓取）
            "https://huggingface.co/blog/feed.xml",                            # Hugging Face 官方博客与动态
            "https://www.technologyreview.com/topic/artificial-intelligence/feed/", # MIT Technology Review (AI 分类)
            "https://venturebeat.com/category/ai/feed/",                       # VentureBeat AI 行业动态
            "https://export.arxiv.org/rss/cs.AI",                              # arXiv cs.AI 研究前沿
        ],
        "webhook_env": "DISCORD_WEBHOOK_AI",
        "topic": "Artificial Intelligence, Machine Learning, Large Language Models (LLMs), AI Industry News",
        "max_items_per_source": 30,
        "max_push_per_run": 8,
    },
    "虚幻引擎开发": {
        "rss_urls": [
            "https://www.unrealengine.com/en-US/rss",                          # Unreal Engine 官方 RSS
            "https://80.lv/category/unreal-engine/feed/",                      # 80 Level (UE 技术美术与开发)
            "https://www.cgchannel.com/tag/unreal-engine/feed/",               # CG Channel UE 行业与技术动态
            "https://www.unrealengine.com/en-US/spotlights/rss",               # Unreal Engine 官方案例与技术实践
        ],
        "webhook_env": "DISCORD_WEBHOOK_UE",
        "topic": "Unreal Engine, 3D Rendering, Game Development, Tech Art, Epic Games",
        "max_items_per_source": 20,
        "max_push_per_run": 6,
    }
}


def main():
    print("=" * 50)
    print("AI 自动化前沿资讯推送器 - 支持多频道路由版")
    print("=" * 50)

    # 1. 初始化数据库表（如果不存在）
    init_db()

    total_stats_new = 0
    total_stats_pushed = 0

    # 外层路由循环：遍历每一个领域/频道
    for channel_name, config in CHANNELS_CONFIG.items():
        print("\n" + "#" * 50)
        print(f"正在处理频道: 【{channel_name}】")
        print("#" * 50)

        # 提取当前频道的 Webhook
        webhook_env_key = config["webhook_env"]
        webhook_url = os.environ.get(webhook_env_key)

        if not webhook_url:
            print(f"[跳过] 环境变量中未找到 {webhook_env_key}，跳过此频道。")
            continue

        rss_urls = config["rss_urls"]
        topic = config["topic"]
        max_items_per_source = config.get("max_items_per_source", 30)
        max_push_per_run = config.get("max_push_per_run", 8)

        # 2. 模块 1：抓取并过滤当前频道 24 小时内的文章
        print(f"\n[{channel_name} - 步骤 1] 抓取并执行 24 小时过滤...")
        recent_articles = fetch_and_filter_rss(rss_urls, max_items_per_source=max_items_per_source)
        print(f"-> 共抓取到 {len(recent_articles)} 篇 24 小时内发布的文章。")

        if not recent_articles:
            print(f"\n[{channel_name}] 任务结束，当前没有新文章。")
            continue

        print(f"\n[{channel_name} - 步骤 2 & 3 & 4] 开始处理文章队列...")

        channel_candidates = []

        for idx, article in enumerate(recent_articles, 1):
            title = article["title"]
            link = article["link"]
            summary = article["summary"]

            print(f"\n--- {channel_name} 进度: {idx}/{len(recent_articles)} ---")
            print(f"标题: {title}")

            # 3. 模块 2：状态检查与防重
            if link_exists(link):
                print("  -> [跳过] 数据库记录显示该文章之前已推送过。")
                continue

            total_stats_new += 1
            print("  -> [新文章] 调用 DeepSeek AI 进行价值评估...")

            # 4. 模块 3：AI 打分与深度提炼（传入频道 topic 进行相关性硬过滤）
            ai_result = evaluate_article(
                title,
                summary,
                topic=topic,
                source_name=article.get("source_name", ""),
                source_url=article.get("source_url", "")
            )

            if not ai_result:
                # 已被 ai_processor 内部过滤（相关性/前沿性/关注度不达标）
                continue

            channel_candidates.append((article, ai_result))

        if not channel_candidates:
            print(f"\n[{channel_name}] 无通过“前沿+关注度”双重过滤的候选文章。")
            continue

        channel_candidates.sort(
            key=lambda item: (
                int(item[1].get("score", 0) or 0)
                + int(item[1].get("frontier_score", 0) or 0)
                + int(item[1].get("attention_score", 0) or 0),
                int(item[1].get("attention_score", 0) or 0),
                int(item[1].get("frontier_score", 0) or 0),
            ),
            reverse=True,
        )

        selected_candidates = channel_candidates[:max_push_per_run]
        print(
            f"\n[{channel_name}] 通过过滤 {len(channel_candidates)} 篇，"
            f"按综合分选取前 {len(selected_candidates)} 篇进行推送。"
        )

        for article, ai_result in selected_candidates:
            title = article["title"]
            link = article["link"]

            # 5. 模块 4：动态推送到对应频道的 Discord
            print(f"  -> [高分通过] 正在推送到 【{channel_name}】 频道...")
            push_success = push_to_discord(article, ai_result, webhook_url)

            # 6. 闭环：推送成功后更新数据库
            if push_success:
                print("  -> [记录状态] 写入 Turso 数据库，以防未来重复推送。")
                insert_link(link)
                total_stats_pushed += 1
            else:
                print("  -> [推送失败] 放弃写入数据库，将在下一次运行时自动重试。")

    # 7. 全局任务总结
    print("\n" + "=" * 50)
    print("所有频道任务处理完毕！本次全局工作流统计：")
    print(f"- 参与路由的频道数: {len(CHANNELS_CONFIG)}")
    print(f"- 数据库查重新文章总计: {total_stats_new}")
    print(f"- 成功推送到 Discord 文章总计: {total_stats_pushed}")
    print("=" * 50)


if __name__ == "__main__":
    main()
