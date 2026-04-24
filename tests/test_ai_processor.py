import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_processor import evaluate_article
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
    print("ai_processor.py 功能验证")
    print("=" * 50)

    configs = load_configs()
    print(f"\n可用配置:")
    for i, cfg in enumerate(configs, 1):
        print(f"  {i}. {cfg['_filename']} - {cfg['channel_name']}")
    
    print(f"\n请选择配置 (1-{len(configs)}) 或按 Enter 使用默认测试: ", end="")
    choice = input().strip()
    
    if choice and choice.isdigit() and 1 <= int(choice) <= len(configs):
        # 使用选定的配置
        config = configs[int(choice) - 1]
        print(f"\n使用配置: {config['channel_name']}")
        print("=" * 50)
        
        print(f"\n正在从 RSS 源获取文章...")
        articles = fetch_and_filter_rss(config['rss_urls'], max_items_per_source=5)
        
        if not articles:
            print("未获取到 24 小时内的文章，使用默认测试用例。\n")
            use_default = True
        else:
            print(f"获取到 {len(articles)} 篇文章，开始逐一测试\n")
            use_default = False
            
            for idx, article in enumerate(articles, 1):
                print("=" * 50)
                print(f"[测试 {idx}/{len(articles)}] 真实文章评估")
                print("=" * 50)
                print(f"标题: {article['title'][:80]}...")
                print(f"来源: {article.get('source_name', 'Unknown')}")
                print(f"发布时间: {article['published_time']}")
                
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
                    print("\n提炼结果:")
                    print(f"  相关性评分: {result.get('relevance_score')}/10")
                    print(f"  质量评分: {result.get('quality_score')}/10")
                    print(f"  综合评分: {result.get('relevance_score', 0) * 0.4 + result.get('quality_score', 0) * 0.6:.1f}/10")
                    print(f"  翻译标题: {result.get('translated_title')}")
                    print(f"  核心突破: {result.get('core_breakthrough')[:100]}...")
                else:
                    print("\n未通过筛选（相关性或质量评分低于阈值）")
                print()
    else:
        use_default = True
    
    if use_default:
        print("\n使用默认测试用例")
        print("=" * 50)
        
        test_title_1 = "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化"
        test_summary_1 = "今天，Epic Games 正式发布了虚幻引擎 5.4 版本。这一重大更新带来了全新的局部动作匹配(Motion Matching)动画系统，极大地减少了动画师的工作量。同时，Nanite 渲染管线获得了深度优化，大幅提升了在主机平台的帧率表现。"

        test_title_2 = "今天天气真好，公司楼下的咖啡店打折"
        test_summary_2 = "本周三到周五，楼下星巴克全场饮品买一送一，快叫上同事一起来喝咖啡吧。"

        test_title_3 = "米其林三星主厨揭秘：如何煎出完美的牛排"
        test_summary_3 = "在这篇独家专访中，主厨分享了他经过二十年积累的煎牛排秘诀。从选肉的静置时间到黄油的焦化温度，每一个细节都决定了这块肉的最终口感。"

        print(f"\n[测试 1] 高价值文章打分测试...")
        print(f"标题: {test_title_1}")
        result_1 = evaluate_article(
            test_title_1, 
            test_summary_1, 
            topic="Unreal Engine, 3D Rendering, Game Development",
            relevance_min=7,
            quality_min=7
        )
        if result_1:
            print("提炼结果:")
            print(f"  相关性评分: {result_1.get('relevance_score')}/10")
            print(f"  质量评分: {result_1.get('quality_score')}/10")
            print(f"  综合评分: {result_1.get('relevance_score', 0) * 0.4 + result_1.get('quality_score', 0) * 0.6:.1f}/10")
            print(f"  翻译标题: {result_1.get('translated_title')}")
            print(f"  核心突破: {result_1.get('core_breakthrough')}")
        else:
            print("未通过筛选（这可能不符合预期，请检查 API 或 Prompt）。")

        print(f"\n[测试 2] 低价值文章拦截测试...")
        print(f"标题: {test_title_2}")
        result_2 = evaluate_article(
            test_title_2, 
            test_summary_2, 
            topic="general technology",
            relevance_min=7,
            quality_min=7
        )
        if not result_2:
            print("测试通过：成功拦截低价值文章。")
        else:
            print(f"测试失败：低价值文章未被拦截")
            print(f"  相关性: {result_2.get('relevance_score')}, 质量: {result_2.get('quality_score')}")

        print(f"\n[测试 3] 领域不相关拦截测试 (Hard Filter)...")
        print(f"标题: {test_title_3}")
        result_3 = evaluate_article(
            test_title_3, 
            test_summary_3, 
            topic="Artificial Intelligence, Large Language Models",
            relevance_min=7,
            quality_min=7
        )
        if not result_3:
            print("测试通过：成功拦截领域不相关文章。")
        else:
            print(f"测试失败：领域不相关文章未被拦截")
            print(f"  相关性: {result_3.get('relevance_score')}, 质量: {result_3.get('quality_score')}")
