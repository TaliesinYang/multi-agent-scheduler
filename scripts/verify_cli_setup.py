#!/usr/bin/env python3
"""
验证CLI客户端设置

检查GitHub Copilot、Claude CLI等是否正确安装和配置
"""

import subprocess
import sys
import os

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_command(cmd, name, test_args=None):
    """
    检查命令是否可用

    Args:
        cmd: 命令名
        name: 显示名称
        test_args: 测试参数列表

    Returns:
        bool: 命令是否可用
    """
    test_args = test_args or ['--help']

    try:
        result = subprocess.run(
            [cmd] + test_args,
            capture_output=True,
            timeout=10,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {name:20s} 可用")

            # 尝试获取版本信息
            try:
                version_result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if version_result.returncode == 0:
                    version = version_result.stdout.strip().split('\n')[0]
                    print(f"   版本: {version}")
            except:
                pass

            return True
        else:
            print(f"❌ {name:20s} 不可用 (返回码: {result.returncode})")
            if result.stderr:
                print(f"   错误: {result.stderr[:100]}")
            return False

    except FileNotFoundError:
        print(f"❌ {name:20s} 未安装 (命令: {cmd})")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠️  {name:20s} 超时")
        return False
    except Exception as e:
        print(f"❌ {name:20s} 错误: {str(e)[:100]}")
        return False

def check_github_copilot():
    """检查GitHub Copilot设置"""
    print_header("GitHub Copilot / Codex")

    results = {}

    # 检查GitHub CLI
    results['gh'] = check_command('gh', 'GitHub CLI')

    # 检查Copilot扩展
    if results['gh']:
        try:
            result = subprocess.run(
                ['gh', 'extension', 'list'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if 'copilot' in result.stdout.lower():
                print("✅ Copilot扩展        已安装")
                results['copilot_ext'] = True
            else:
                print("❌ Copilot扩展        未安装")
                print("   安装: gh extension install github/gh-copilot")
                results['copilot_ext'] = False
        except Exception as e:
            print(f"⚠️  无法检查Copilot扩展: {e}")
            results['copilot_ext'] = False

    # 检查codex命令
    results['codex'] = check_command('codex', 'Codex命令', ['--help'])

    # 如果codex不可用，检查gh copilot
    if not results['codex'] and results['gh']:
        print("\n💡 提示: 可以使用 'gh copilot suggest' 代替 'codex'")
        results['gh_copilot'] = check_command('gh', 'gh copilot', ['copilot', '--help'])

    return results

def check_claude_cli():
    """检查Claude CLI"""
    print_header("Claude CLI")

    results = {}
    results['claude'] = check_command('claude', 'Claude CLI')

    if results['claude']:
        # 检查API密钥配置
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print("✅ ANTHROPIC_API_KEY  已设置")
            print(f"   密钥: {api_key[:10]}...{api_key[-5:]}")
        else:
            print("⚠️  ANTHROPIC_API_KEY  未设置")
            print("   运行: claude configure")

    return results

def check_config_file():
    """检查配置文件"""
    print_header("配置文件")

    config_files = [
        'config.yaml',
        'config.cli.yaml',
        'config.example.yaml',
        '.env'
    ]

    found = False
    for config_file in config_files:
        if os.path.exists(config_file):
            size = os.path.getsize(config_file)
            print(f"✅ {config_file:25s} 存在 ({size} 字节)")
            found = True
        else:
            print(f"⚠️  {config_file:25s} 不存在")

    if not found:
        print("\n💡 提示: 运行以下命令创建配置:")
        print("   cp config.cli.yaml config.yaml")

    return found

def check_workspace():
    """检查工作区"""
    print_header("工作区")

    workspace_paths = [
        './workspace',
        './checkpoints_cli',
        './logs'
    ]

    for path in workspace_paths:
        if os.path.exists(path):
            print(f"✅ {path:25s} 存在")
        else:
            print(f"⚠️  {path:25s} 不存在")
            try:
                os.makedirs(path, exist_ok=True)
                print(f"   → 已创建 {path}")
            except Exception as e:
                print(f"   ❌ 创建失败: {e}")

def generate_recommendations(results):
    """生成推荐配置"""
    print_header("推荐配置")

    has_codex = results.get('codex') or results.get('gh_copilot')
    has_claude = results.get('claude')

    if has_codex or has_claude:
        print("\n✅ 您可以使用CLI客户端模式!")
        print("\n推荐的config.yaml配置:\n")

        print("```yaml")
        print("agents:")

        if has_codex:
            print("  codex:")
            print("    enabled: true")
            print("    cli_command: \"codex\"  # 或 \"gh copilot suggest\"")
            print("    workspace: \"./workspace\"")
            print("    max_concurrent: 5")

        if has_claude:
            print("  claude_cli:")
            print("    enabled: true")
            print("    cli_command: \"claude\"")
            print("    max_concurrent: 3")

        print("\n  mock:")
        print("    enabled: true  # 保留用于测试")
        print("\nscheduler:")
        print("  agent_selection_strategy:")

        if has_codex:
            print("    coding: \"codex\"")
            print("    testing: \"codex\"")
            print("    refactoring: \"codex\"")

        if has_claude:
            print("    analysis: \"claude_cli\"")
            print("    documentation: \"claude_cli\"")

        print("    simple: \"mock\"")
        print("```")

    else:
        print("\n❌ 没有检测到可用的CLI客户端")
        print("\n请安装以下之一:")
        print("\n1. GitHub Copilot (推荐):")
        print("   • 订阅: https://github.com/settings/copilot")
        print("   • 安装CLI: gh extension install github/gh-copilot")
        print("\n2. Claude CLI:")
        print("   • 安装: pip install claude-cli")
        print("   • 配置: claude configure")

def run_quick_test(results):
    """运行快速功能测试"""
    print_header("快速功能测试")

    has_codex = results.get('codex')
    has_claude = results.get('claude')

    if has_codex:
        print("\n测试Codex...")
        try:
            result = subprocess.run(
                ['codex', 'write a hello world function'],
                capture_output=True,
                timeout=30,
                text=True
            )
            if result.returncode == 0:
                print("✅ Codex测试通过")
                print(f"   响应: {result.stdout[:100]}...")
            else:
                print(f"❌ Codex测试失败: {result.stderr[:100]}")
        except Exception as e:
            print(f"❌ Codex测试错误: {e}")

    if has_claude:
        print("\n测试Claude CLI...")
        try:
            result = subprocess.run(
                ['claude', 'Hello, respond with just "OK"'],
                capture_output=True,
                timeout=30,
                text=True
            )
            if result.returncode == 0:
                print("✅ Claude CLI测试通过")
                print(f"   响应: {result.stdout[:100]}...")
            else:
                print(f"❌ Claude CLI测试失败: {result.stderr[:100]}")
        except Exception as e:
            print(f"❌ Claude CLI测试错误: {e}")

def main():
    """主函数"""
    print("\n" + "🔍" * 30)
    print("  CLI客户端设置验证工具")
    print("  Multi-Agent Scheduler")
    print("🔍" * 30)

    # 汇总结果
    all_results = {}

    # 检查各个组件
    gh_results = check_github_copilot()
    all_results.update(gh_results)

    claude_results = check_claude_cli()
    all_results.update(claude_results)

    config_ok = check_config_file()
    check_workspace()

    # 生成推荐
    generate_recommendations(all_results)

    # 快速测试（可选）
    print("\n" + "=" * 60)
    test_input = input("\n是否运行快速功能测试? (y/N): ").strip().lower()
    if test_input == 'y':
        run_quick_test(all_results)

    # 最终总结
    print_header("总结")

    has_any_cli = any([
        all_results.get('codex'),
        all_results.get('gh_copilot'),
        all_results.get('claude')
    ])

    if has_any_cli and config_ok:
        print("\n✅ 您的CLI客户端设置完成!")
        print("\n下一步:")
        print("1. 复制配置: cp config.cli.yaml config.yaml")
        print("2. 运行示例: python test_cli.py")
        print("3. 查看文档: docs/CLI_CLIENT_SETUP.md")
        return 0
    elif has_any_cli:
        print("\n⚠️  CLI客户端可用，但缺少配置文件")
        print("\n运行: cp config.cli.yaml config.yaml")
        return 1
    else:
        print("\n❌ 需要安装CLI客户端")
        print("\n请查看文档: docs/CLI_CLIENT_SETUP.md")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        sys.exit(130)
