#!/usr/bin/env python3
"""
真实 API 环境性能测试

⚠️ 警告: 此测试会调用真实 API，产生实际费用
建议从小规模测试开始（5-10个任务）

使用方法:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python tests/real_world/test_real_api_performance.py --tasks 5
"""

import asyncio
import time
import os
import argparse
from typing import List, Dict, Any
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.scheduler import MultiAgentScheduler, Task, ExecutionMode
from src.agents import MockAgent


async def test_real_api_small_scale(api_key: str, num_tasks: int = 5):
    """小规模真实 API 测试"""

    print("\n" + "="*60)
    print("🔍 真实 API 性能测试")
    print("="*60)
    print(f"任务数量: {num_tasks}")
    print(f"API: Claude Sonnet 3.5")
    print(f"模式: 并行执行")
    print("="*60 + "\n")

    # 导入真实 Agent（可能失败，所以在函数内部）
    try:
        from src.agents import ClaudeAgent
    except ImportError:
        print("❌ 无法导入 ClaudeAgent")
        print("   请确保已安装: pip install anthropic")
        return None

    # 创建调度器
    try:
        scheduler = MultiAgentScheduler(agents={
            "claude": ClaudeAgent(api_key=api_key)
        })
    except Exception as e:
        print(f"❌ 创建调度器失败: {e}")
        return None

    # 定义简单任务（避免消耗太多 token）
    tasks = [
        Task(
            id=f"task_{i}",
            prompt=f"请用一句话总结数字 {i} 的数学特性",  # 简单任务
            task_type="general",
            depends_on=[]
        )
        for i in range(num_tasks)
    ]

    print("📝 任务列表:")
    for task in tasks[:3]:  # 只显示前3个
        print(f"   • {task.id}: {task.prompt}")
    if num_tasks > 3:
        print(f"   • ... (还有 {num_tasks-3} 个任务)")

    print("\n⏳ 开始执行...\n")

    # 执行并计时
    start_time = time.time()

    try:
        result = await scheduler.schedule(tasks, mode=ExecutionMode.PARALLEL)
        duration = time.time() - start_time

        # 显示结果
        print("\n" + "="*60)
        print("✅ 执行完成")
        print("="*60)
        print(f"总耗时: {duration:.2f}秒")
        print(f"平均每任务: {duration/num_tasks:.2f}秒")
        print(f"吞吐量: {num_tasks/duration:.3f} tasks/sec")
        print(f"成功任务: {result.task_count}/{num_tasks}")
        print("="*60)

        # 详细摘要
        scheduler.print_summary(result)

        # 性能分析
        print("\n📊 性能分析:")
        print(f"   理论串行时间: ~{duration * num_tasks / max(result.task_count, 1):.1f}秒")
        print(f"   实际并行时间: {duration:.1f}秒")
        print(f"   加速比: ~{(duration * num_tasks / max(duration, 1)):.1f}x")

        # 成本估算（粗略）
        estimated_tokens = num_tasks * 100  # 假设每任务100 tokens
        estimated_cost = estimated_tokens * 3 / 1_000_000  # Claude Sonnet 定价
        print(f"\n💰 成本估算:")
        print(f"   估算 tokens: ~{estimated_tokens}")
        print(f"   估算成本: ~${estimated_cost:.4f}")

        return {
            "duration": duration,
            "throughput": num_tasks / duration,
            "success_rate": result.task_count / num_tasks * 100,
            "avg_time_per_task": duration / num_tasks
        }

    except Exception as e:
        duration = time.time() - start_time
        print("\n" + "="*60)
        print(f"❌ 测试失败 (耗时 {duration:.2f}秒)")
        print("="*60)
        print(f"错误: {e}")
        print("\n可能原因:")
        print("  • API 密钥无效或过期")
        print("  • 网络连接问题")
        print("  • API 限流（请求太频繁）")
        print("  • 余额不足")

        print("\n💡 建议:")
        print("  1. 检查 API 密钥是否正确")
        print("  2. 验证网络连接")
        print("  3. 减少任务数量（使用 --tasks 3）")
        print("  4. 检查 Anthropic 账户状态")

        return None


async def compare_mock_vs_real(api_key: str, num_tasks: int = 5):
    """对比 Mock 和真实 API 性能"""

    print("\n" + "="*60)
    print("🔬 Mock vs. 真实 API 性能对比")
    print("="*60)

    # 1. Mock 测试
    print("\n[1/2] Mock 环境测试...")
    mock_scheduler = MultiAgentScheduler(agents={"mock": MockAgent()})

    mock_tasks = [
        Task(id=f"task_{i}", prompt=f"任务 {i}", task_type="general", depends_on=[])
        for i in range(num_tasks)
    ]

    mock_start = time.time()
    mock_result = await mock_scheduler.schedule(mock_tasks)
    mock_duration = time.time() - mock_start

    print(f"   Mock 耗时: {mock_duration:.2f}秒")
    print(f"   Mock 吞吐量: {num_tasks/mock_duration:.1f} tasks/sec")

    # 2. 真实 API 测试
    print(f"\n[2/2] 真实 API 测试...")
    real_result = await test_real_api_small_scale(api_key, num_tasks)

    # 3. 对比
    if real_result:
        print("\n" + "="*60)
        print("📊 性能对比总结")
        print("="*60)

        print(f"\n{'指标':<20} {'Mock':<15} {'真实 API':<15} {'差异':<15}")
        print("-"*65)

        mock_throughput = num_tasks / mock_duration
        real_throughput = real_result['throughput']
        throughput_diff = (mock_throughput / real_throughput) if real_throughput > 0 else 0

        mock_avg = mock_duration / num_tasks
        real_avg = real_result['avg_time_per_task']
        time_diff = real_avg / mock_avg if mock_avg > 0 else 0

        print(f"{'执行时间':<20} {mock_duration:>6.2f}秒      {real_result['duration']:>6.2f}秒      {real_result['duration']/mock_duration:>6.1f}x 慢")
        print(f"{'吞吐量':<20} {mock_throughput:>6.1f} t/s     {real_throughput:>6.3f} t/s     {throughput_diff:>6.1f}x 快(Mock)")
        print(f"{'平均每任务':<20} {mock_avg:>6.2f}秒      {real_avg:>6.2f}秒      {time_diff:>6.1f}x 慢")
        print(f"{'成功率':<20} {'100%':<15} {real_result['success_rate']:>6.1f}%")

        print("\n💡 关键发现:")
        print(f"   • 真实 API 比 Mock 慢 {real_result['duration']/mock_duration:.0f}x")
        print(f"   • 主要开销来自网络延迟和模型推理")
        print(f"   • Mock 测试适合验证算法，真实测试评估实际性能")


async def test_parallel_speedup(api_key: str, num_tasks: int = 10):
    """测试真实环境的并行加速比"""

    print("\n" + "="*60)
    print("🚀 并行加速比测试")
    print("="*60)

    try:
        from src.agents import ClaudeAgent
        scheduler = MultiAgentScheduler(agents={
            "claude": ClaudeAgent(api_key=api_key)
        })
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    tasks = [
        Task(id=f"task_{i}", prompt=f"总结数字 {i}", task_type="general", depends_on=[])
        for i in range(num_tasks)
    ]

    # 测试串行执行
    print(f"\n[1/2] 串行执行 {num_tasks} 个任务...")
    serial_start = time.time()
    try:
        serial_result = await scheduler.schedule(tasks, mode=ExecutionMode.SERIAL)
        serial_duration = time.time() - serial_start
        print(f"   串行耗时: {serial_duration:.2f}秒")
    except Exception as e:
        print(f"   ❌ 串行执行失败: {e}")
        return

    # 等待避免限流
    print("\n   ⏳ 等待30秒避免 API 限流...")
    await asyncio.sleep(30)

    # 测试并行执行
    print(f"\n[2/2] 并行执行 {num_tasks} 个任务...")
    parallel_start = time.time()
    try:
        parallel_result = await scheduler.schedule(tasks, mode=ExecutionMode.PARALLEL)
        parallel_duration = time.time() - parallel_start
        print(f"   并行耗时: {parallel_duration:.2f}秒")
    except Exception as e:
        print(f"   ❌ 并行执行失败: {e}")
        return

    # 计算加速比
    speedup = serial_duration / parallel_duration if parallel_duration > 0 else 0

    print("\n" + "="*60)
    print("📊 加速比分析")
    print("="*60)
    print(f"串行时间: {serial_duration:.2f}秒")
    print(f"并行时间: {parallel_duration:.2f}秒")
    print(f"加速比: {speedup:.2f}x")
    print(f"理论最优: {num_tasks:.0f}x")
    print(f"效率: {speedup/num_tasks*100:.1f}%")

    print("\n💡 分析:")
    if speedup >= 2.5:
        print("   ✅ 并行加速效果显著")
    elif speedup >= 1.5:
        print("   ⚠️  并行有改善，但受 API 限流影响")
    else:
        print("   ❌ 并行效果不明显，可能受限于 API 限流")


def main():
    parser = argparse.ArgumentParser(
        description="真实 API 环境性能测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 小规模测试（5个任务）
  export ANTHROPIC_API_KEY="sk-ant-..."
  python %(prog)s --tasks 5

  # 对比 Mock vs 真实
  python %(prog)s --compare --tasks 5

  # 测试并行加速比（会消耗更多 API 调用）
  python %(prog)s --speedup --tasks 10

注意:
  - 此测试会产生实际 API 费用
  - 建议从小任务数开始
  - 注意 API 限流（Claude: 50 req/min）
        """
    )

    parser.add_argument(
        "--tasks",
        type=int,
        default=5,
        help="任务数量（默认: 5）"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="对比 Mock 和真实 API 性能"
    )

    parser.add_argument(
        "--speedup",
        action="store_true",
        help="测试并行加速比（需要更多 API 调用）"
    )

    args = parser.parse_args()

    # 检查 API 密钥
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        print("\n请先设置 API 密钥:")
        print("  export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'")
        print("\n或者运行 Mock 模式测试:")
        print("  python tests/benchmark/test_benchmark_scheduler.py")
        sys.exit(1)

    # 确认测试
    print("\n⚠️  警告: 此测试将调用真实 API")
    print(f"   任务数量: {args.tasks}")
    print(f"   估算 API 调用: {args.tasks * 2 if args.speedup else args.tasks}")
    print(f"   估算成本: ~${args.tasks * 0.001:.4f}")

    response = input("\n确认继续? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("已取消")
        sys.exit(0)

    # 运行测试
    if args.compare:
        asyncio.run(compare_mock_vs_real(api_key, args.tasks))
    elif args.speedup:
        asyncio.run(test_parallel_speedup(api_key, args.tasks))
    else:
        asyncio.run(test_real_api_small_scale(api_key, args.tasks))


if __name__ == "__main__":
    main()
