"""
test_time_decay.py - 时间衰减机制测试脚本

功能：
- 读取指定配置文件的RSS源
- 抓取真实文章数据
- 模拟AI评分（随机生成）
- 对比"启用时间衰减"和"禁用时间衰减"的排序结果
- 可视化展示时间衰减效果
"""

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from src.rss_parser import fetch_and_filter_rss


def load_config(config_name: str) -> dict:
    """加载指定的配置文件"""
    config_path = Path(__file__).parent / "configs" / f"{config_name}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def simulate_ai_score() -> tuple:
    """模拟AI评分（随机生成7-10分）"""
    relevance = random.randint(7, 10)
    quality = random.randint(7, 10)
    return relevance, quality


def calculate_base_score(relevance: int, quality: int) -> float:
    """计算基础分数"""
    return relevance * 0.4 + quality * 0.6


def calculate_time_factor(age_hours: float, gravity: float) -> float:
    """计算时间衰减因子"""
    if gravity <= 0:
        return 1.0
    return 1 / (1 + (age_hours / 12) ** gravity)


def format_age(age_hours: float) -> str:
    """格式化文章年龄"""
    if age_hours < 1:
        return f"{int(age_hours * 60)}分钟前"
    elif age_hours < 24:
        return f"{age_hours:.1f}小时前"
    else:
        return f"{age_hours / 24:.1f}天前"


def main():
    print("=" * 80)
    print("时间衰减机制测试脚本")
    print("=" * 80)
    
    # 列出可用的配置文件
    configs_dir = Path(__file__).parent / "configs"
    available_configs = [f.stem for f in configs_dir.glob("*.json")]
    
    print("\n可用的配置文件:")
    for idx, config_name in enumerate(available_configs, 1):
        print(f"  {idx}. {config_name}")
    
    # 用户选择配置
    while True:
        try:
            choice = input(f"\n请选择配置文件 (1-{len(available_configs)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_configs):
                selected_config = available_configs[choice_idx]
                break
            else:
                print(f"请输入 1 到 {len(available_configs)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")
    
    # 加载配置
    print(f"\n正在加载配置: {selected_config}.json")
    config = load_config(selected_config)
    
    channel_name = config["channel_name"]
    rss_urls = config["rss_urls"]
    time_decay_gravity = float(config.get("time_decay_gravity", 0))
    max_items = config.get("max_items_per_source", 30)
    
    print(f"频道名称: {channel_name}")
    print(f"RSS源数量: {len(rss_urls)}")
    print(f"时间衰减系数 (gravity): {time_decay_gravity}")
    
    # 抓取真实RSS数据
    print(f"\n正在抓取RSS数据（最多 {max_items} 篇/源）...")
    articles = fetch_and_filter_rss(rss_urls, max_items_per_source=max_items)
    
    if not articles:
        print("\n[错误] 未抓取到任何文章，请检查RSS源是否可用。")
        return
    
    print(f"成功抓取 {len(articles)} 篇文章（24小时内）")
    
    # 为每篇文章模拟AI评分
    print("\n正在为文章生成模拟AI评分...")
    now_utc = datetime.now(timezone.utc)
    scored_articles = []
    
    for article in articles:
        relevance, quality = simulate_ai_score()
        base_score = calculate_base_score(relevance, quality)
        
        # 计算文章年龄
        published_time = datetime.fromisoformat(article["published_time"])
        age_hours = (now_utc - published_time).total_seconds() / 3600
        
        # 计算时间衰减后的分数
        time_factor = calculate_time_factor(age_hours, time_decay_gravity)
        final_score = base_score * time_factor
        
        scored_articles.append({
            "title": article["title"],
            "published_time": published_time,
            "age_hours": age_hours,
            "relevance": relevance,
            "quality": quality,
            "base_score": base_score,
            "time_factor": time_factor,
            "final_score": final_score,
        })
    
    # 排序对比
    print("\n" + "=" * 80)
    print("排序结果对比")
    print("=" * 80)
    
    # 方案1：不使用时间衰减（按base_score排序）
    sorted_without_decay = sorted(scored_articles, key=lambda x: x["base_score"], reverse=True)
    
    # 方案2：使用时间衰减（按final_score排序）
    sorted_with_decay = sorted(scored_articles, key=lambda x: x["final_score"], reverse=True)
    
    # 显示前10篇对比
    display_count = min(10, len(scored_articles))
    
    print(f"\n【方案1：不使用时间衰减】前 {display_count} 篇:")
    print("-" * 80)
    for idx, article in enumerate(sorted_without_decay[:display_count], 1):
        print(f"{idx}. [{article['base_score']:.2f}分] {format_age(article['age_hours'])}")
        print(f"   R:{article['relevance']} Q:{article['quality']}")
        print(f"   {article['title'][:70]}...")
        print()
    
    print(f"\n【方案2：使用时间衰减 (gravity={time_decay_gravity})】前 {display_count} 篇:")
    print("-" * 80)
    for idx, article in enumerate(sorted_with_decay[:display_count], 1):
        print(f"{idx}. [{article['final_score']:.2f}分] {format_age(article['age_hours'])} (衰减因子: {article['time_factor']:.2f})")
        print(f"   R:{article['relevance']} Q:{article['quality']} (基础分: {article['base_score']:.2f})")
        print(f"   {article['title'][:70]}...")
        print()
    
    # 统计分析
    print("\n" + "=" * 80)
    print("统计分析")
    print("=" * 80)
    
    # 计算平均年龄
    avg_age_without = sum(a["age_hours"] for a in sorted_without_decay[:display_count]) / display_count
    avg_age_with = sum(a["age_hours"] for a in sorted_with_decay[:display_count]) / display_count
    
    print(f"\n前 {display_count} 篇的平均年龄:")
    print(f"  不使用时间衰减: {avg_age_without:.1f} 小时")
    print(f"  使用时间衰减:   {avg_age_with:.1f} 小时")
    print(f"  差异: {avg_age_without - avg_age_with:.1f} 小时")
    
    # 计算排名变化
    print(f"\n排名变化分析:")
    rank_changes = []
    for idx, article_with in enumerate(sorted_with_decay[:display_count], 1):
        # 找到这篇文章在不使用时间衰减时的排名
        old_rank = next(
            (i + 1 for i, a in enumerate(sorted_without_decay) if a["title"] == article_with["title"]),
            None
        )
        if old_rank:
            change = old_rank - idx
            rank_changes.append(change)
            if change > 0:
                print(f"  ↑ {article_with['title'][:50]}... (从第{old_rank}名 → 第{idx}名, +{change})")
            elif change < 0:
                print(f"  ↓ {article_with['title'][:50]}... (从第{old_rank}名 → 第{idx}名, {change})")
    
    if rank_changes:
        avg_change = sum(abs(c) for c in rank_changes) / len(rank_changes)
        print(f"\n  平均排名变化幅度: {avg_change:.1f} 位")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
