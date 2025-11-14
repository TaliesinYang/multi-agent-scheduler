#!/usr/bin/env python3
"""
最简单的 Multi-Agent Scheduler 示例
无需任何 API 密钥，立即运行
"""

import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import MockAgent


async def main():
    print("🚀 Multi-Agent Scheduler - 最简示例\n")

    # 1. 创建 Mock Agent（模拟模式，无需 API 密钥）
    print("📦 初始化调度器...")
    scheduler = MultiAgentScheduler(agents={"mock": MockAgent()})

    # 2. 定义3个简单任务（无依赖，可并行执行）
    print("📝 定义任务...\n")
    tasks = [
        Task(id="task1", prompt="总结量子计算的基本原理", task_type="general"),
        Task(id="task2", prompt="写一个快速排序算法的Python实现", task_type="general"),
        Task(id="task3", prompt="分析云计算相比传统架构的3个主要优势", task_type="general")
    ]

    print("任务列表:")
    for task in tasks:
        print(f"  • {task.id}: {task.prompt}")

    # 3. 执行调度（系统会自动检测任务可以并行执行）
    print("\n⚡ 开始执行（自动并行）...\n")
    result = await scheduler.schedule(tasks)

    # 4. 查看执行结果
    print("\n" + "="*60)
    print("📊 执行结果摘要")
    print("="*60)
    scheduler.print_summary(result)

    print("\n" + "="*60)
    print("📄 详细结果")
    print("="*60)
    scheduler.print_detailed_results(result)

    print("\n✅ 示例执行完成!")
    print("\n💡 提示:")
    print("   - Mock 模式返回模拟数据，无需 API 密钥")
    print("   - 要使用真实 AI，请配置 API 密钥并使用 ClaudeAgent 等")
    print("   - 运行 'python demo.py' 查看更多示例")


if __name__ == "__main__":
    asyncio.run(main())
