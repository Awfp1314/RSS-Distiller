import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_processor import evaluate_article

if __name__ == "__main__":
    print("=" * 50)
    print("ai_processor.py 功能验证")
    print("=" * 50)

    test_title_1 = "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化"
    test_summary_1 = "今天，Epic Games 正式发布了虚幻引擎 5.4 版本。这一重大更新带来了全新的局部动作匹配(Motion Matching)动画系统，极大地减少了动画师的工作量。同时，Nanite 渲染管线获得了深度优化，大幅提升了在主机平台的帧率表现。"

    test_title_2 = "今天天气真好，公司楼下的咖啡店打折"
    test_summary_2 = "本周三到周五，楼下星巴克全场饮品买一送一，快叫上同事一起来喝咖啡吧。"

    test_title_3 = "米其林三星主厨揭秘：如何煎出完美的牛排"
    test_summary_3 = "在这篇独家专访中，主厨分享了他经过二十年积累的煎牛排秘诀。从选肉的静置时间到黄油的焦化温度，每一个细节都决定了这块肉的最终口感。"

    print(f"\n[测试 1] 高价值文章打分测试...")
    print(f"标题: {test_title_1}")
    result_1 = evaluate_article(test_title_1, test_summary_1, topic="Unreal Engine, 3D Rendering, Game Development")
    if result_1:
        print("提炼结果:")
        print(json.dumps(result_1, ensure_ascii=False, indent=2))
    else:
        print("未通过筛选（这可能不符合预期，请检查 API 或 Prompt）。")

    print(f"\n[测试 2] 低价值文章拦截测试...")
    print(f"标题: {test_title_2}")
    result_2 = evaluate_article(test_title_2, test_summary_2, topic="general technology")
    if not result_2:
        print("测试通过：成功拦截低价值文章。")
    else:
        print(f"测试失败：低价值文章未被拦截 (得分: {result_2.get('score')})。")

    print(f"\n[测试 3] 领域不相关拦截测试 (Hard Filter)...")
    print(f"标题: {test_title_3}")
    result_3 = evaluate_article(test_title_3, test_summary_3, topic="Artificial Intelligence, Large Language Models")
    if not result_3:
        print("测试通过：成功拦截领域不相关文章。")
    else:
        print(f"测试失败：领域不相关文章未被拦截 (得分: {result_3.get('score')})。")
