"""
ai_processor.py - AI 打分与深度提炼模块

功能：
- 调用 DeepSeek 官方 API 进行新闻价值评估
- 强制模型输出预定义的 JSON 格式
- 根据评分（阈值 >= 7）进行拦截与过滤
"""

import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 初始化 OpenAI 客户端 (DeepSeek 兼容 API)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)

# 需求文档中规定的系统提示词 (双语升级版)
SYSTEM_PROMPT = (
    "You are a senior technology expert and a professional bilingual translator. "
    "Evaluate the provided tech news title and summary for its value to developers on a scale of 1 to 10. "
    "You MUST output strictly in JSON format containing exactly the following fields:\n"
    "- 'score': (Integer, 1-10)\n"
    "- 'translated_title': (The Chinese translation of the original title)\n"
    "- 'core_breakthrough': (One-sentence core breakthrough in format: '[English text] / [中文翻译]')\n"
    "- 'bullet_points': (A list of exactly 3 key points. Each point MUST be in format: '[English text] / [中文翻译]')\n"
    "- 'impact_analysis': (Technical or industry impact analysis in format: '[English text] / [中文翻译]')"
)


def evaluate_article(title: str, summary: str) -> Optional[Dict[str, Any]]:
    """
    使用 DeepSeek API 评估文章价值，并提取结构化摘要。

    参数:
        title: 文章标题
        summary: 文章纯文本摘要

    返回:
        如果评分 >= 7 且 JSON 解析成功，返回包含分析结果的字典；
        如果评分 < 7，或者解析/请求失败，返回 None。
    """
    if not API_KEY:
        print("[错误] 未找到 DEEPSEEK_API_KEY 环境变量！")
        return None

    # 构建用户输入，避免摘要太长消耗过多 Token（截断前 1500 个字符）
    user_content = f"标题: {title}\n\n摘要: {summary[:1500]}"

    try:
        # DeepSeek 官方建议指定 response_format={"type": "json_object"} 强制输出 JSON
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3, # 使用较低温度保证 JSON 输出稳定
            timeout=30       # 防止长时间挂起
        )

        raw_content = response.choices[0].message.content
        if not raw_content:
            print(f"  -> [跳过] API 返回内容为空: {title}")
            return None

        # 解析 JSON
        result = json.loads(raw_content)
        
        # 提取评分进行判断
        score = result.get("score", 0)
        
        if score < 7:
            print(f"  -> [过滤] 评分不足已过滤 (得分: {score}/10): {title}")
            return None
            
        print(f"  -> [保留] 发现高价值文章 (得分: {score}/10): {title}")
        return result

    except json.JSONDecodeError:
        print(f"  -> [错误] 模型未返回有效 JSON 格式: {title}")
        print(f"原始输出: {raw_content}")
        return None
    except Exception as e:
        print(f"  -> [错误] DeepSeek API 请求失败: {e}")
        return None


# ============================================================
# 测试入口：验证 API 连通性、JSON 解析与评分阈值拦截
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("ai_processor.py 功能验证")
    print("=" * 50)

    # 测试用例 1：明显的高价值前沿技术文章（预期得分较高）
    test_title_1 = "Epic Games 发布虚幻引擎 5.4，引入革命性的局部动画与渲染优化"
    test_summary_1 = "今天，Epic Games 正式发布了虚幻引擎 5.4 版本。这一重大更新带来了全新的局部动作匹配(Motion Matching)动画系统，极大地减少了动画师的工作量。同时，Nanite 渲染管线获得了深度优化，大幅提升了在主机平台的帧率表现。"
    
    # 测试用例 2：低价值/普通文章（预期得分较低）
    test_title_2 = "今天天气真好，公司楼下的咖啡店打折"
    test_summary_2 = "本周三到周五，楼下星巴克全场饮品买一送一，快叫上同事一起来喝咖啡吧。"

    print(f"\n[测试 1] 高价值文章打分测试...")
    print(f"标题: {test_title_1}")
    result_1 = evaluate_article(test_title_1, test_summary_1)
    if result_1:
        print("提炼结果:")
        print(json.dumps(result_1, ensure_ascii=False, indent=2))
    else:
        print("未通过筛选（这可能不符合预期，请检查 API 或 Prompt）。")

    print(f"\n[测试 2] 低价值文章拦截测试...")
    print(f"标题: {test_title_2}")
    result_2 = evaluate_article(test_title_2, test_summary_2)
    if not result_2:
        print("测试通过：成功拦截低价值文章。")
    else:
        print(f"测试失败：低价值文章未被拦截 (得分: {result_2.get('score')})。")
