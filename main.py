"""
main.py - 自动化资讯推送器主入口

功能：
串联四大模块，实现“RSS 获取 -> 数据库防重 -> AI 打分过滤 -> Discord 推送 -> 数据库更新”的完整业务闭环。
"""

from ai_processor import evaluate_article
from db_manager import init_db, insert_link, link_exists
from discord_pusher import push_to_discord
from rss_parser import fetch_and_filter_rss


def main():
    print("=" * 50)
    print("🚀 AI 自动化前沿资讯推送器 - 开始运行")
    print("=" * 50)

    # 1. 初始化数据库表（如果不存在）
    init_db()

    # 2. 配置 RSS 源
    RSS_URLS = [
        "https://www.unrealengine.com/en-US/rss",
        "https://news.ycombinator.com/rss",
    ]

    # 3. 模块 1：抓取并过滤 24 小时内的文章
    print("\n[步骤 1] 开始抓取 RSS 源并执行 24 小时过滤...")
    recent_articles = fetch_and_filter_rss(RSS_URLS)
    print(f"-> 共抓取到 {len(recent_articles)} 篇 24 小时内发布的文章。")

    if not recent_articles:
        print("\n当前没有 24 小时内的新文章，任务结束。")
        return

    print("\n[步骤 2 & 3 & 4] 开始处理文章队列...")
    stats_new = 0
    stats_pushed = 0

    for idx, article in enumerate(recent_articles, 1):
        title = article["title"]
        link = article["link"]
        summary = article["summary"]

        print(f"\n--- 处理进度: {idx}/{len(recent_articles)} ---")
        print(f"标题: {title}")

        # 4. 模块 2：状态检查与防重
        if link_exists(link):
            print("  -> [跳过] 数据库记录显示该文章之前已推送过。")
            continue

        stats_new += 1
        print("  -> [新文章] 调用 DeepSeek AI 进行价值评估...")

        # 5. 模块 3：AI 打分与深度提炼
        ai_result = evaluate_article(title, summary)

        if not ai_result:
            # 评分低于 7 分，或解析异常，已被 ai_processor 内部过滤
            continue

        # 6. 模块 4：推送到 Discord
        print("  -> [高分通过] 正在推送到 Discord 频道...")
        push_success = push_to_discord(article, ai_result)

        # 7. 闭环：推送成功后更新数据库
        if push_success:
            print("  -> [记录状态] 写入 Turso 数据库，以防未来重复推送。")
            insert_link(link)
            stats_pushed += 1
        else:
            print("  -> [推送失败] 放弃写入数据库，将在下一次运行时自动重试。")

    # 8. 任务总结与日志打印
    print("\n" + "=" * 50)
    print("✅ 任务执行完毕！本次工作流统计：")
    print(f"- 抓取近期文章总数: {len(recent_articles)}")
    print(f"- 数据库查重新文章数: {stats_new}")
    print(f"- 成功推送高价值文章: {stats_pushed}")
    print("=" * 50)


if __name__ == "__main__":
    main()
