"""
main.py - 自动化资讯推送器主入口

功能：
- 采用字典路由模式支持多频道推送
- 串联四大模块，实现"RSS 获取 -> 数据库防重 -> AI 打分过滤 -> 动态 Discord 推送 -> 数据库更新"的完整业务闭环。
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.ai_processor import evaluate_article
from src.db_manager import init_db, insert_link, link_exists
from src.discord_pusher import push_to_discord
from src.rss_parser import fetch_and_filter_rss

# 加载环境变量（必须尽早调用，确保能读到包含 webhook_env 在内的变量）
load_dotenv()

# ============================================================
# 从 configs/ 目录动态加载多频道路由配置
# ============================================================
_REQUIRED_FIELDS = {"channel_name", "rss_urls", "webhook_env", "topic"}
_DEFAULTS = {"max_items_per_source": 30, "max_push_per_run": 8}

def _load_channels_config() -> dict:
    configs_dir = Path(__file__).parent / "configs"
    if not configs_dir.exists():
        print(f"[错误] 配置目录不存在: {configs_dir}")
        return {}
    
    result = {}
    for json_file in sorted(configs_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            missing = _REQUIRED_FIELDS - data.keys()
            if missing:
                print(f"[警告] 跳过 {json_file.name}：缺少必填字段 {missing}")
                continue
            channel_name = data["channel_name"]
            
            # 验证 rss_urls 是列表且不为空
            if not isinstance(data.get("rss_urls"), list) or not data["rss_urls"]:
                print(f"[警告] 跳过 {json_file.name}：rss_urls 必须是非空列表")
                continue
            
            result[channel_name] = {
                "rss_urls": data["rss_urls"],
                "webhook_env": data["webhook_env"],
                "topic": data["topic"],
                "max_items_per_source": data.get("max_items_per_source", _DEFAULTS["max_items_per_source"]),
                "max_push_per_run": data.get("max_push_per_run", _DEFAULTS["max_push_per_run"]),
                "min_scores": data.get("min_scores", {}),
                "evaluation_focus": data.get("evaluation_focus"),
                "time_decay_gravity": data.get("time_decay_gravity", 0),
                "time_decay_halflife": data.get("time_decay_halflife", 12),
            }
        except (json.JSONDecodeError, OSError) as e:
            print(f"[警告] 跳过 {json_file.name}：解析失败 ({e})")
    
    if not result:
        print("[警告] 未加载到任何有效的频道配置")
    
    return result

CHANNELS_CONFIG = _load_channels_config()


def main():
    print("=" * 50)
    print("AI 自动化前沿资讯推送器 - 支持多频道路由版")
    print("=" * 50)

    # 检查是否有有效配置
    if not CHANNELS_CONFIG:
        print("[错误] 没有加载到任何有效的频道配置，程序退出")
        return

    # 1. 初始化数据库表（如果不存在）
    try:
        init_db()
    except Exception as e:
        print(f"[错误] 数据库初始化失败: {e}")
        return

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
        min_scores = config.get("min_scores", {})
        relevance_min = int(min_scores.get("relevance", 7))
        quality_min = int(min_scores.get("quality", 7))
        time_decay_gravity = float(config.get("time_decay_gravity", 0))
        time_decay_halflife = float(config.get("time_decay_halflife", 12))
        evaluation_focus = config.get("evaluation_focus")

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
                source_url=article.get("source_url", ""),
                relevance_min=relevance_min,
                quality_min=quality_min,
                evaluation_focus=evaluation_focus,
            )

            if not ai_result:
                # 已被 ai_processor 内部过滤（相关性或质量不达标）
                continue

            channel_candidates.append((article, ai_result))

        if not channel_candidates:
            print(f"\n[{channel_name}] 无通过相关性和质量双重过滤的候选文章。")
            continue

        # 排序逻辑：支持时间衰减机制
        def _calculate_sort_score(item):
            article, ai_result = item
            relevance_score = int(ai_result.get("relevance_score", 0) or 0)
            quality_score = int(ai_result.get("quality_score", 0) or 0)
            base_score = relevance_score * 0.4 + quality_score * 0.6
            
            # 如果启用时间衰减（gravity > 0）
            if time_decay_gravity > 0:
                published_time_str = article.get("published_time")
                if published_time_str:
                    try:
                        published_time = datetime.fromisoformat(published_time_str)
                        now_utc = datetime.now(timezone.utc)
                        age_hours = (now_utc - published_time).total_seconds() / 3600
                        # 时间衰减公式：time_factor = 1 / (1 + (age_hours / halflife) ^ gravity)
                        time_factor = 1 / (1 + (age_hours / time_decay_halflife) ** time_decay_gravity)
                        final_score = base_score * time_factor
                        return (final_score, quality_score)
                    except Exception:
                        pass  # 时间解析失败，使用原始分数
            
            return (base_score, quality_score)

        channel_candidates.sort(key=_calculate_sort_score, reverse=True)

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
