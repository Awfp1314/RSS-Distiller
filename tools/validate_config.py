"""
RSS 配置验证工具

用于验证用户提交的频道配置 JSON 是否符合规范。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from urllib.parse import urlparse

def validate_rss_url(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    验证 RSS URL 是否可访问
    
    返回: (是否有效, 错误信息)
    """
    try:
        # 基本 URL 格式检查
        parsed = urlparse(url)
        if not parsed.scheme in ['http', 'https']:
            return False, f"无效的 URL 协议: {parsed.scheme}"
        
        if not parsed.netloc:
            return False, "缺少域名"
        
        # 尝试访问
        response = requests.get(url, timeout=timeout, verify=False, headers={
            'User-Agent': 'RSS-Distiller-Validator/1.0'
        })
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        # 检查内容类型
        content_type = response.headers.get('Content-Type', '').lower()
        valid_types = ['xml', 'rss', 'atom', 'feed']
        
        if not any(t in content_type for t in valid_types):
            # 尝试检查内容
            content = response.text[:500].lower()
            if not any(tag in content for tag in ['<rss', '<feed', '<channel']):
                return False, f"内容类型可能不是 RSS/Atom: {content_type}"
        
        return True, "OK"
        
    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, "连接失败"
    except Exception as e:
        return False, f"未知错误: {str(e)}"


def validate_config(config: Dict) -> List[str]:
    """
    验证配置 JSON 的完整性和正确性
    
    返回: 错误列表（空列表表示验证通过）
    """
    errors = []
    
    # 必填字段检查
    required_fields = {
        'channel_name': str,
        'rss_urls': list,
        'webhook_env': str,
        'topic': str,
        'max_items_per_source': int,
        'max_push_per_run': int,
        'time_decay_gravity': (int, float),
        'time_decay_halflife': (int, float),
        'min_scores': dict,
        'evaluation_focus': dict
    }
    
    for field, expected_type in required_fields.items():
        if field not in config:
            errors.append(f"缺少必填字段: {field}")
        elif not isinstance(config[field], expected_type):
            errors.append(f"字段 {field} 类型错误，期望 {expected_type}，实际 {type(config[field])}")
    
    # RSS URLs 检查
    if 'rss_urls' in config:
        if not isinstance(config['rss_urls'], list):
            errors.append("rss_urls 必须是数组")
        elif len(config['rss_urls']) == 0:
            errors.append("rss_urls 不能为空")
        elif len(config['rss_urls']) > 10:
            errors.append(f"rss_urls 过多 ({len(config['rss_urls'])} 个)，建议不超过 10 个")
        else:
            for url in config['rss_urls']:
                if not isinstance(url, str):
                    errors.append(f"RSS URL 必须是字符串: {url}")
    
    # webhook_env 命名检查
    if 'webhook_env' in config:
        webhook_env = config['webhook_env']
        if not webhook_env.startswith('DISCORD_WEBHOOK_'):
            errors.append(f"webhook_env 必须以 DISCORD_WEBHOOK_ 开头: {webhook_env}")
        if not webhook_env.isupper():
            errors.append(f"webhook_env 必须全大写: {webhook_env}")
    
    # min_scores 检查
    if 'min_scores' in config:
        min_scores = config['min_scores']
        if not isinstance(min_scores, dict):
            errors.append("min_scores 必须是对象")
        else:
            if 'relevance' not in min_scores:
                errors.append("min_scores 缺少 relevance 字段")
            elif not isinstance(min_scores['relevance'], int) or not (0 <= min_scores['relevance'] <= 10):
                errors.append(f"min_scores.relevance 必须是 0-10 的整数: {min_scores['relevance']}")
            
            if 'quality' not in min_scores:
                errors.append("min_scores 缺少 quality 字段")
            elif not isinstance(min_scores['quality'], int) or not (0 <= min_scores['quality'] <= 10):
                errors.append(f"min_scores.quality 必须是 0-10 的整数: {min_scores['quality']}")
    
    # evaluation_focus 检查
    if 'evaluation_focus' in config:
        focus = config['evaluation_focus']
        if not isinstance(focus, dict):
            errors.append("evaluation_focus 必须是对象")
        else:
            required_focus_fields = ['relevance_criteria', 'quality_indicators', 'reject_patterns']
            for field in required_focus_fields:
                if field not in focus:
                    errors.append(f"evaluation_focus 缺少 {field} 字段")
                elif not isinstance(focus[field], list):
                    errors.append(f"evaluation_focus.{field} 必须是数组")
                elif len(focus[field]) < 3:
                    errors.append(f"evaluation_focus.{field} 至少需要 3 项")
    
    # 参数范围检查
    if 'max_items_per_source' in config:
        val = config['max_items_per_source']
        if not (5 <= val <= 50):
            errors.append(f"max_items_per_source 建议范围 5-50: {val}")
    
    if 'max_push_per_run' in config:
        val = config['max_push_per_run']
        if not (3 <= val <= 20):
            errors.append(f"max_push_per_run 建议范围 3-20: {val}")
    
    if 'time_decay_gravity' in config:
        val = config['time_decay_gravity']
        if not (0 <= val <= 3):
            errors.append(f"time_decay_gravity 建议范围 0-3: {val}")
    
    if 'time_decay_halflife' in config:
        val = config['time_decay_halflife']
        if not (1 <= val <= 48):
            errors.append(f"time_decay_halflife 建议范围 1-48 小时: {val}")
    
    return errors


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_config.py <config.json>")
        print("或者: python validate_config.py --check-urls <config.json>")
        sys.exit(1)
    
    check_urls = False
    config_file = sys.argv[-1]
    
    if '--check-urls' in sys.argv:
        check_urls = True
    
    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("RSS Distiller 配置验证工具")
    print("=" * 60)
    print(f"\n📄 配置文件: {config_file}")
    print(f"📋 频道名称: {config.get('channel_name', '未知')}")
    print(f"🔗 RSS 源数量: {len(config.get('rss_urls', []))}")
    
    # 验证配置结构
    print("\n🔍 验证配置结构...")
    errors = validate_config(config)
    
    if errors:
        print("\n❌ 发现以下问题：")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        sys.exit(1)
    else:
        print("✅ 配置结构验证通过")
    
    # 验证 RSS URLs（可选）
    if check_urls:
        print("\n🌐 验证 RSS 源可访问性...")
        rss_urls = config.get('rss_urls', [])
        
        for i, url in enumerate(rss_urls, 1):
            print(f"\n  [{i}/{len(rss_urls)}] {url}")
            is_valid, message = validate_rss_url(url)
            
            if is_valid:
                print(f"    ✅ {message}")
            else:
                print(f"    ⚠️  {message}")
    
    # 检查是否与现有配置冲突
    print("\n🔍 检查配置冲突...")
    configs_dir = Path(__file__).parent.parent / "configs"
    
    if configs_dir.exists():
        webhook_env = config.get('webhook_env')
        channel_name = config.get('channel_name')
        
        conflicts = []
        for existing_file in configs_dir.glob("*.json"):
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                
                if existing.get('webhook_env') == webhook_env:
                    conflicts.append(f"webhook_env 冲突: {existing_file.name}")
                
                if existing.get('channel_name') == channel_name:
                    conflicts.append(f"channel_name 冲突: {existing_file.name}")
            except Exception:
                pass
        
        if conflicts:
            print("⚠️  发现潜在冲突：")
            for conflict in conflicts:
                print(f"  - {conflict}")
        else:
            print("✅ 无配置冲突")
    
    # 生成建议的文件名
    print("\n📝 建议配置：")
    webhook_env = config.get('webhook_env', '')
    if webhook_env.startswith('DISCORD_WEBHOOK_'):
        suggested_name = webhook_env.replace('DISCORD_WEBHOOK_', '').lower().capitalize()
        print(f"  文件名: configs/{suggested_name}.json")
    
    print(f"  环境变量: {webhook_env}")
    print(f"  需要在 GitHub Secrets 中配置对应的 Webhook URL")
    
    print("\n" + "=" * 60)
    print("✅ 验证完成！配置可以使用。")
    print("=" * 60)


if __name__ == "__main__":
    main()
