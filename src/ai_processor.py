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

# 需求文档中规定的系统提示词 (双语升级版 - 引入领域相关性硬过滤)
SYSTEM_PROMPT_TEMPLATE = (
    "You are a senior technology expert and a professional bilingual translator. "
    "Your task is to evaluate a tech article based on its Relevance to a specific Target Topic and its Frontier Value for engineering audiences.\n\n"
    "Target Topic: {topic}\n\n"
    "### Hard Rejection Rules (must score 0):\n"
    "- Q&A/help-seeking posts, beginner troubleshooting, recruitment, personal showcase, opinion/rant, unverified rumors, repost/roundup with no concrete technical updates.\n"
    "- Community discussion threads with no new release, no benchmark, no official technical detail, and no reproducible engineering value.\n"
    "- Content mainly about personal workflow or generic career advice.\n\n"
    "### Evaluation Mechanism (Dual Scoring):\n"
    "1. Relevance Score (0-10): topic alignment with Target Topic.\n"
    "2. Frontier Score (0-10): novelty, technical depth, and practical signal for professionals.\n"
    "3. Attention Score (0-10): market/industry attention level based on indicators in the provided content such as official announcement significance, broad developer impact, citation momentum, or ecosystem adoption signal. If evidence is weak, give low score.\n"
    "4. Final Score (0-10 integer): if relevance_score < {relevance_min} or frontier_score < {frontier_min} or attention_score < {attention_min}, score MUST be 0. Otherwise score reflects overall quality.\n\n"
    "### Source Reliability Hint:\n"
    "- Prefer official releases, primary technical writeups, or first-party research sources.\n"
    "- For community sources, be stricter: without concrete technical breakthroughs, score 0.\n\n"
    "### Output format:\n"
    "You MUST output strictly in JSON format containing exactly the following fields:\n"
    "- 'score': (Integer, 0-10. Return 0 if relevance to the target topic is low. Otherwise, 1-10 based on quality)\n"
    "- 'relevance_score': (Integer, 0-10)\n"
    "- 'frontier_score': (Integer, 0-10)\n"
    "- 'attention_score': (Integer, 0-10)\n"
    "- 'translated_title': (The Chinese translation of the original title)\n"
    "- 'core_breakthrough': (One-sentence core breakthrough in format: '[English text] / [中文翻译]')\n"
    "- 'bullet_points': (A list of exactly 3 key points. Each point MUST be in format: '[English text] / [中文翻译]')\n"
    "- 'impact_analysis': (Technical or industry impact analysis in format: '[English text] / [中文翻译]')"
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
    frontier_min: int = 8,
    attention_min: int = 7,
    score_min: int = 8,
) -> Optional[Dict[str, Any]]:
    """
    使用 DeepSeek API 评估文章价值，并提取结构化摘要。

    参数:
        title: 文章标题
        summary: 文章纯文本摘要
        topic: 频道关注的技术领域，用于相关性硬过滤

    返回:
        如果通过相关性/前沿性/关注度与总分阈值且 JSON 解析成功，返回包含分析结果的字典；
        如果未通过阈值，或者解析/请求失败，返回 None。
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
    
    # 动态注入 topic
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic=topic,
        relevance_min=relevance_min,
        frontier_min=frontier_min,
        attention_min=attention_min,
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
        
        # 提取评分进行判断
        score = int(result.get("score", 0) or 0)
        relevance_score = int(result.get("relevance_score", 0) or 0)
        frontier_score = int(result.get("frontier_score", 0) or 0)
        attention_score = int(result.get("attention_score", 0) or 0)

        if relevance_score < relevance_min or frontier_score < frontier_min or attention_score < attention_min:
            print(
                "  -> [过滤] 相关性/前沿性/关注度不足已过滤 "
                f"(relevance={relevance_score}, frontier={frontier_score}, attention={attention_score}): {title}"
            )
            return None

        if score < score_min:
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
