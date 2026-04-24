"""
快速添加用户提交的频道配置

用法：
    python add_channel.py <json_file_or_json_string>
    
示例：
    python add_channel.py user_config.json
    python add_channel.py '{"channel_name": "..."}'
"""

import json
import sys
from pathlib import Path
import subprocess

def add_channel_config(config: dict) -> bool:
    """
    添加频道配置到 configs/ 目录
    
    返回: 是否成功
    """
    # 验证配置
    print("🔍 验证配置...")
    from validate_config import validate_config
    
    errors = validate_config(config)
    if errors:
        print("❌ 配置验证失败：")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ 配置验证通过")
    
    # 确定文件名
    webhook_env = config.get('webhook_env', '')
    if webhook_env.startswith('DISCORD_WEBHOOK_'):
        filename = webhook_env.replace('DISCORD_WEBHOOK_', '').capitalize() + '.json'
    else:
        print("❌ 无效的 webhook_env")
        return False
    
    # 检查文件是否已存在
    configs_dir = Path(__file__).parent.parent / "configs"
    target_file = configs_dir / filename
    
    if target_file.exists():
        print(f"⚠️  文件已存在: {filename}")
        response = input("是否覆盖？(y/N): ").strip().lower()
        if response != 'y':
            print("❌ 取消操作")
            return False
    
    # 写入文件
    print(f"\n📝 写入配置到: configs/{filename}")
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("✅ 配置文件已创建")
    
    # 提示需要配置的环境变量
    print(f"\n⚙️  下一步：配置环境变量")
    print(f"  在 GitHub Repository Secrets 中添加：")
    print(f"  名称: {webhook_env}")
    print(f"  值: https://discord.com/api/webhooks/...")
    
    # 提示更新工作流
    print(f"\n📋 更新 GitHub Actions 工作流：")
    print(f"  编辑 .github/workflows/daily_push.yml")
    print(f"  在 env 部分添加：")
    print(f"    {webhook_env}: ${{{{ secrets.{webhook_env} }}}}")
    
    # 询问是否立即提交
    print(f"\n🔄 是否立即提交到 Git？")
    response = input("(y/N): ").strip().lower()
    
    if response == 'y':
        try:
            channel_name = config.get('channel_name', 'Unknown')
            commit_message = f"feat: add {channel_name} channel configuration"
            
            subprocess.run(['git', 'add', str(target_file)], check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            print("✅ 已提交到 Git")
            print("\n💡 记得运行: git push")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 操作失败: {e}")
            return False
    
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python add_channel.py <config.json>")
        print("或者: python add_channel.py '{\"channel_name\": \"...\"}'")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # 判断是文件还是 JSON 字符串
    if input_arg.startswith('{'):
        # JSON 字符串
        try:
            config = json.loads(input_arg)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            sys.exit(1)
    else:
        # 文件路径
        try:
            with open(input_arg, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"❌ 文件不存在: {input_arg}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            sys.exit(1)
    
    print("=" * 60)
    print("RSS Distiller 频道配置添加工具")
    print("=" * 60)
    print(f"\n📋 频道名称: {config.get('channel_name', '未知')}")
    print(f"🔗 RSS 源数量: {len(config.get('rss_urls', []))}")
    print(f"🎯 主题: {config.get('topic', '未知')}")
    
    success = add_channel_config(config)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 频道配置添加成功！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 操作失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
