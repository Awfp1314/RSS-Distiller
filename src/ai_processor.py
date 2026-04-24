"""
ai_processor.py - AI 打分与深度提炼模块

功能：
- 调用 DeepSeek 官方 API 进行新闻价值评估
- 强制模型输出预定义的 JSON 格式
- 根据相关性/前沿性/关注度与总分阈值进行拦截与过滤
"""

import json
import os
import re
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

# 简化的系统提示词 - 双维度评分
SYSTEM_PROMPT_TEMPLATE = (
    "You are a senior expert and professional bilingual translator. "
    "Your task is to evaluate an article based on two dimensions:\n\n"
    "Target Topic: {topic}\n\n"
    "### Hard Rejection Rules (must score 0 for both dimensions):\n"
    "- Q&A/help-seeking posts, beginner troubleshooting, recruitment, personal showcase\n"
    "- Opinion/rant without data, unverified rumors, repost/roundup with no new information\n"
    "- Community discussion threads with no concrete updates or reproducible value\n\n"
    "### Evaluation Dimensions:\n"
    "1. **Relevance Score (0-10)**: How well does this article align with the Target Topic?\n"
    "   - 10: Directly addresses core concepts of the topic\n"
    "   - 7-9: Related to the topic with substantial overlap\n"
    "   - 4-6: Tangentially related\n"
    "   - 0-3: Unrelated or off-topic\n\n"
    "2. **Quality Score (0-10)**: Overall content quality combining:\n"
    "   - Information density: Does it provide substantial new information?\n"
    "   - Source credibility: Official release > Primary analysis > Secondary report\n"
    "   - Technical depth: Does it include technical details, data, or evidence?\n"
    "   - Novelty: Does it present new developments (within 24 hours)?\n\n"
    "### Scoring Rules:\n"
    "- If relevance_score < {relevance_min} OR quality_score < {quality_min}, BOTH scores MUST be 0\n"
    "- Prioritize official sources and first-party technical content\n"
    "- For community sources: require concrete breakthroughs, not just discussion\n\n"
    "### Output format:\n"
    "You MUST output strictly in JSON format containing exactly the following fields:\n"
    "- 'relevance_score': (Integer, 0-10)\n"
    "- 'quality_score': (Integer, 0-10)\n"
    "- 'translated_title': (Chinese translation of the original title)\n"
    "- 'core_breakthrough': (One-sentence summary in format: '[English] / [中文]')\n"
    "- 'bullet_points': (List of exactly 3 key points, each in format: '[English] / [中文]')\n"
    "- 'impact_analysis': (Impact analysis in format: '[English] / [中文]')"
)


def _looks_like_low_signal_discussion(title: str, source_url: str) -> bool:
    """对社区问答/求助类标题做轻量硬过滤，避免明显噪声进入模型。"""
    if "reddit.com" not in (source_url or ""):
        return False

    title_l = (title or "").strip().lower()
    patterns = [
        r"\?$",
        r"^\[?help\]?",
        r"^\[?question\]?",
        r"\bhow do i\b",
        r"\banyone else\b",
        r"\bcan someone\b",
        r"\bwhy is my\b",
        r"\bissue\b",
        r"\bproblem\b",
    ]
    return any(re.search(p, title_l) for p in patterns)


def evaluate_article(
    title: str,
    summary: str,
    topic: str = "general technology",
    source_name: str = "",
    source_url: str = "",
    relevance_min: int = 7,
    quality_min: int = 7,
) -> Optional[Dict[str, Any]]:
    """
    使用 DeepSeek API 评估文章价值，并提取结构化摘要。

    参数:
        title: 文章标题
        summary: 文章纯文本摘要
        topic: 频道关注的技术领域
        relevance_min: 相关性最低阈值
        quality_min: 质量最低阈值

    返回:
        如果通过阈值且 JSON 解析成功，返回包含分析结果的字典；否则返回 None。
    """
    if not API_KEY:
        print("[错误] 未找到 DEEPSEEK_API_KEY 环境变量！")
        return None

    if _looks_like_low_signal_discussion(title, source_url):
        print(f"  -> [过滤] 社区问答/求助类标题已拦截: {title}")
        return None

    # 构建用户输入，避免摘要太长消耗过多 Token（截断前 1500 个字符）
    user_content = (
        f"Source Name: {source_name or 'Unknown'}\n"
        f"Source URL: {source_url or 'Unknown'}\n"
        f"Title: {title}\n\n"
        f"Summary: {summary[:1500]}"
    )
    
    # 动态注入 topic 和阈值
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic=topic,
        relevance_min=relevance_min,
        quality_min=quality_min,
    )

    def _parse_json_with_fallback(raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            repaired = re.sub(r",\s*([}\]])", r"\1", raw)
            return json.loads(repaired)

    try:
        # DeepSeek 官方建议指定 response_format={"type": "json_object"} 强制输出 JSON
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
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
        result = _parse_json_with_fallback(raw_content)
        
        # 提取简化后的两个维度
        relevance_score = int(result.get("relevance_score", 0) or 0)
        quality_score = int(result.get("quality_score", 0) or 0)

        if relevance_score < relevance_min or quality_score < quality_min:
            print(
                "  -> [过滤] 评分不足已过滤 "
                f"(relevance={relevance_score}, quality={quality_score}): {title}"
            )
            return None
            
        print(f"  -> [保留] 发现高价值文章 (relevance={relevance_score}, quality={quality_score}): {title}")
        return result

    except json.JSONDecodeError:
        print(f"  -> [错误] 模型未返回有效 JSON 格式: {title}")
        print(f"原始输出: {raw_content}")
        return None
    except Exception as e:
        print(f"  -> [错误] DeepSeek API 请求失败: {e}")
        return None
