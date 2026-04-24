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

# 默认评分标准（当配置文件未提供时使用）
DEFAULT_EVALUATION_FOCUS = {
    "relevance_criteria": [
        "Directly addresses core concepts of the target topic",
        "Provides substantial new information or insights",
        "Comes from credible sources (official releases, research papers, expert analysis)"
    ],
    "quality_indicators": [
        "Includes concrete details, data, or evidence",
        "Provides technical depth beyond surface-level reporting",
        "Offers actionable insights or reproducible information",
        "Clearly explains significance and implications"
    ],
    "reject_patterns": [
        "Q&A/help-seeking posts or beginner troubleshooting",
        "Opinion/rant without supporting data or evidence",
        "Reposted content with no new information or analysis",
        "Community discussion with no concrete updates or breakthroughs"
    ]
}

# 基础 Prompt 模板（框架部分）
BASE_PROMPT_TEMPLATE = (
    "You are a senior expert and professional bilingual translator. "
    "Evaluate an article based on two dimensions:\n\n"
    "Target Topic: {topic}\n\n"
    "{evaluation_focus}\n\n"
    "### Scoring Rules:\n"
    "- If relevance_score < {relevance_min} OR quality_score < {quality_min}, BOTH scores MUST be 0\n"
    "- Use the evaluation focus above to guide your scoring\n\n"
    "{output_format}"
)

# 将 SYSTEM_PROMPT_TEMPLATE 指向 BASE_PROMPT_TEMPLATE（保持兼容性）
SYSTEM_PROMPT_TEMPLATE = BASE_PROMPT_TEMPLATE

# 输出格式（固定部分，确保 JSON 解析稳定）
OUTPUT_FORMAT = (
    "### Output format:\n"
    "You MUST output strictly in JSON format containing exactly the following fields:\n"
    "- 'relevance_score': (Integer, 0-10)\n"
    "- 'quality_score': (Integer, 0-10)\n"
    "- 'translated_title': (Chinese translation of the original title)\n"
    "- 'core_breakthrough': (One-sentence summary, pure English text)\n"
    "- 'core_breakthrough_cn': (Chinese translation of core_breakthrough)\n"
    "- 'bullet_points': (List of exactly 3 key points in pure English)\n"
    "- 'bullet_points_cn': (List of exactly 3 key points in Chinese, corresponding to bullet_points)\n"
    "- 'impact_analysis': (Impact analysis in pure English)\n"
    "- 'impact_analysis_cn': (Chinese translation of impact_analysis)"
)


def _build_evaluation_focus(focus_config: Dict[str, Any]) -> str:
    """
    从配置构建评分重点说明。
    
    如果配置为空或字段缺失，使用默认值。
    """
    # 使用配置值，如果不存在则使用默认值
    relevance_criteria = focus_config.get("relevance_criteria") or DEFAULT_EVALUATION_FOCUS["relevance_criteria"]
    quality_indicators = focus_config.get("quality_indicators") or DEFAULT_EVALUATION_FOCUS["quality_indicators"]
    reject_patterns = focus_config.get("reject_patterns") or DEFAULT_EVALUATION_FOCUS["reject_patterns"]
    
    focus_text = ""
    
    # 拒绝规则
    focus_text += "### Hard Rejection Rules (score 0 for both dimensions):\n"
    for pattern in reject_patterns:
        focus_text += f"- {pattern}\n"
    
    focus_text += "\n### Evaluation Dimensions:\n\n"
    
    # 相关性标准
    focus_text += "**1. Relevance Score (0-10)**: How well does this align with the target topic?\n"
    focus_text += "   Prioritize articles that:\n"
    for criterion in relevance_criteria:
        focus_text += f"   - {criterion}\n"
    
    # 质量指标
    focus_text += "\n**2. Quality Score (0-10)**: Overall content quality.\n"
    focus_text += "   High-quality articles typically:\n"
    for indicator in quality_indicators:
        focus_text += f"   - {indicator}\n"
    
    return focus_text


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
    evaluation_focus: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    使用 DeepSeek API 评估文章价值，并提取结构化摘要。

    参数:
        title: 文章标题
        summary: 文章纯文本摘要
        topic: 频道关注的技术领域
        relevance_min: 相关性最低阈值
        quality_min: 质量最低阈值
        evaluation_focus: 领域定制的评分标准（可选）

    返回:
        如果通过阈值且 JSON 解析成功，返回包含分析结果的字典；否则返回 None。
    """
    if not API_KEY:
        print("[错误] 未找到 DEEPSEEK_API_KEY 环境变量！")
        return None

    if _looks_like_low_signal_discussion(title, source_url):
        print(f"  -> [过滤] 社区问答/求助类标题已拦截: {title}")
        return None

    # 如果摘要为空或太短，使用标题作为补充
    effective_summary = summary.strip() if summary else ""
    if len(effective_summary) < 20:
        effective_summary = f"{title}. {effective_summary}".strip()
        print(f"  -> [提示] 摘要过短，使用标题补充: {title}")

    # 构建用户输入，避免摘要太长消耗过多 Token（截断前 1500 个字符）
    user_content = (
        f"Source Name: {source_name or 'Unknown'}\n"
        f"Source URL: {source_url or 'Unknown'}\n"
        f"Title: {title}\n\n"
        f"Summary: {effective_summary[:1500]}"
    )
    
    # 构建评分标准文本
    focus_text = _build_evaluation_focus(evaluation_focus or {})
    
    # 动态注入 topic、阈值和评分标准
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic=topic,
        relevance_min=relevance_min,
        quality_min=quality_min,
        evaluation_focus=focus_text,
        output_format=OUTPUT_FORMAT,
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
