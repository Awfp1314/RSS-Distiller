#!/usr/bin/env python3
"""
Preview the final system prompt generated for a given config file.
Usage: python tools/preview_prompt.py [config_name]
Example: python tools/preview_prompt.py AI
"""
import sys
import json
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_processor import _build_evaluation_focus, BASE_PROMPT_TEMPLATE, OUTPUT_FORMAT


def preview_prompt(config_name: str):
    """Load config and preview the generated system prompt."""
    config_path = Path(__file__).parent.parent / "configs" / f"{config_name}.json"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    topic = config.get("topic", "Unknown")
    evaluation_focus_config = config.get("evaluation_focus", {})
    min_scores = config.get("min_scores", {})
    relevance_min = min_scores.get("relevance", 7)
    quality_min = min_scores.get("quality", 7)
    
    # Build evaluation focus text
    evaluation_focus = _build_evaluation_focus(evaluation_focus_config)
    
    # Build final system prompt
    system_prompt = BASE_PROMPT_TEMPLATE.format(
        topic=topic,
        evaluation_focus=evaluation_focus,
        relevance_min=relevance_min,
        quality_min=quality_min,
        output_format=OUTPUT_FORMAT
    )
    
    print(f"{'='*80}")
    print(f"Config: {config_name}.json")
    print(f"Topic: {topic}")
    print(f"Min Scores: relevance={relevance_min}, quality={quality_min}")
    print(f"{'='*80}\n")
    print("SYSTEM PROMPT:")
    print(f"{'-'*80}")
    print(system_prompt)
    print(f"{'-'*80}\n")
    print(f"Prompt length: {len(system_prompt)} characters")
    print(f"Estimated tokens: ~{len(system_prompt) // 4}")
    print(f"{'='*80}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/preview_prompt.py [config_name]")
        print("Available configs: AI, Legal, UE")
        sys.exit(1)
    
    config_name = sys.argv[1]
    preview_prompt(config_name)
