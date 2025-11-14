#!/usr/bin/env python3
"""
DAG可视化示例

展示如何使用新的 dag_visualizer 模块生成优雅的任务流可视化
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import MockAgent
from src.dag_visualizer import (
    DAGVisualizer,
    visualize_tasks,
    visualize_workflow
)
from src.workflow_graph import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    NodeType,
    EdgeType,
    WorkflowState
)


async def demo_task_visualization():
    """演示任务DAG可视化"""
    print("=" * 60)
    print("📊 任务DAG可视化演示")
    print("=" * 60)

    # 创建一个真实的软件开发项目任务流
    tasks = [
        # 第一批: 需求分析 (并行)
        Task(
            id="req_analysis",
            prompt="分析用户需求，提取核心功能点",
            task_type="analysis"
        ),
        Task(
            id="market_research",
            prompt="研究竞品特性，识别差异化优势",
            task_type="analysis"
        ),

        # 第二批: 设计阶段 (依赖需求分析)
        Task(
            id="system_design",
            prompt="设计系统架构，选择技术栈",
            task_type="design",
            depends_on=["req_analysis"]
        ),
        Task(
            id="ui_design",
            prompt="设计用户界面，制定交互规范",
            task_type="design",
            depends_on=["req_analysis", "market_research"]
        ),

        # 第三批: 实现阶段 (并行开发)
        Task(
            id="backend_api",
            prompt="实现后端REST API和数据库",
            task_type="coding",
            depends_on=["system_design"]
        ),
        Task(
            id="frontend_ui",
            prompt="实现前端页面和组件",
            task_type="coding",
            depends_on=["ui_design"]
        ),
        Task(
            id="auth_module",
            prompt="实现用户认证与授权模块",
            task_type="coding",
            depends_on=["system_design"]
        ),

        # 第四批: 测试阶段
        Task(
            id="unit_tests",
            prompt="编写单元测试，确保代码质量",
            task_type="testing",
            depends_on=["backend_api", "frontend_ui", "auth_module"]
        ),
        Task(
            id="integration_test",
            prompt="执行集成测试，验证模块协作",
            task_type="testing",
            depends_on=["backend_api", "frontend_ui"]
        ),

        # 第五批: 部署
        Task(
            id="deployment",
            prompt="部署到生产环境，配置监控",
            task_type="deployment",
            depends_on=["unit_tests", "integration_test"]
        )
    ]

    print(f"\n✅ 创建了 {len(tasks)} 个任务")
    print("\n任务依赖关系:")
    for task in tasks:
        deps = task.depends_on if task.depends_on else ["无依赖"]
        print(f"  • {task.id:20s} → {', '.join(deps)}")

    # 1. 生成静态HTML可视化
    print("\n🎨 生成HTML可视化...")
    html_file = "task_dag_visualization.html"
    visualize_tasks(tasks, "html", html_file)
    print(f"✅ 已生成: {html_file}")
    print("   在浏览器中打开即可查看交互式DAG图")

    # 2. 生成Mermaid图 (用于文档)
    print("\n📊 生成Mermaid图表...")
    mermaid_code = visualize_tasks(tasks, "mermaid")
    print("\n" + "─" * 60)
    print(mermaid_code)
    print("─" * 60)

    # 3. 生成Graphviz DOT格式
    print("\n🔧 生成Graphviz DOT格式...")
    dot_file = "task_dag.dot"
    visualize_tasks(tasks, "graphviz", dot_file)
    print(f"✅ 已生成: {dot_file}")
    print("   使用命令生成图片: dot -Tpng task_dag.dot -o task_dag.png")

    # 4. 执行任务并更新可视化
    print("\n🚀 执行任务调度...")
    scheduler = MultiAgentScheduler(agents={"mock": MockAgent()})
    result = await scheduler.schedule(tasks)

    # 生成带执行结果的可视化
    html_file_with_result = "task_dag_with_results.html"
    visualize_tasks(tasks, "html", html_file_with_result, execution_result=result)
    print(f"✅ 已生成执行结果可视化: {html_file_with_result}")

    # 5. 获取统计信息
    viz = DAGVisualizer.from_tasks(tasks, result)
    stats = viz.get_statistics()
    print("\n📈 统计信息:")
    print(f"  总节点数: {stats['total_nodes']}")
    print(f"  总边数: {stats['total_edges']}")
    print(f"  完成率: {stats['completion_rate']:.1f}%")
    print(f"  失败率: {stats['failure_rate']:.1f}%")

    return result


async def demo_workflow_visualization():
    """演示工作流可视化"""
    print("\n" + "=" * 60)
    print("🔄 工作流图可视化演示")
    print("=" * 60)

    # 创建一个条件工作流
    graph = WorkflowGraph("code_review_workflow")

    # 定义节点处理函数
    async def analyze_code(state: WorkflowState):
        print("  [分析代码质量...]")
        # 模拟代码质量评分
        state.set("code_quality", 85)
        return state

    async def run_tests(state: WorkflowState):
        print("  [运行测试套件...]")
        state.set("tests_passed", True)
        return state

    async def code_review(state: WorkflowState):
        print("  [人工代码审查...]")
        state.set("review_approved", True)
        return state

    async def deploy_to_staging(state: WorkflowState):
        print("  [部署到staging环境...]")
        state.set("staging_deployed", True)
        return state

    async def deploy_to_production(state: WorkflowState):
        print("  [部署到生产环境...]")
        state.set("production_deployed", True)
        return state

    async def rollback(state: WorkflowState):
        print("  [回滚更改...]")
        state.set("rolled_back", True)
        return state

    # 构建工作流图
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("analyze", NodeType.TASK, handler=analyze_code))
    graph.add_node(WorkflowNode("test", NodeType.TASK, handler=run_tests))
    graph.add_node(WorkflowNode("review", NodeType.TASK, handler=code_review))
    graph.add_node(WorkflowNode("quality_check", NodeType.CONDITION))
    graph.add_node(WorkflowNode("staging", NodeType.TASK, handler=deploy_to_staging))
    graph.add_node(WorkflowNode("production", NodeType.TASK, handler=deploy_to_production))
    graph.add_node(WorkflowNode("rollback", NodeType.TASK, handler=rollback))
    graph.add_node(WorkflowNode("end", NodeType.END))

    # 添加边
    graph.add_edge(WorkflowEdge("start", "analyze"))
    graph.add_edge(WorkflowEdge("analyze", "test"))
    graph.add_edge(WorkflowEdge("test", "review"))
    graph.add_edge(WorkflowEdge("review", "quality_check"))

    # 条件边: 质量检查通过 → staging
    graph.add_edge(WorkflowEdge(
        "quality_check",
        "staging",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("code_quality", 0) > 80 and s.get("tests_passed", False),
        label="质量合格"
    ))

    # 条件边: 质量检查不通过 → rollback
    graph.add_edge(WorkflowEdge(
        "quality_check",
        "rollback",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("code_quality", 0) <= 80,
        label="质量不合格"
    ))

    graph.add_edge(WorkflowEdge("staging", "production"))
    graph.add_edge(WorkflowEdge("production", "end"))
    graph.add_edge(WorkflowEdge("rollback", "end"))

    print("\n🔍 工作流验证:")
    issues = graph.validate()
    if issues:
        print("  ⚠️  发现问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ 工作流结构正确")

    # 生成可视化
    print("\n🎨 生成工作流可视化...")
    html_file = "workflow_visualization.html"
    visualize_workflow(graph, "html", html_file)
    print(f"✅ 已生成: {html_file}")

    # 生成Mermaid图
    mermaid_code = visualize_workflow(graph, "mermaid")
    print("\n📊 Mermaid图表:")
    print("─" * 60)
    print(mermaid_code)
    print("─" * 60)

    # 执行工作流
    print("\n🚀 执行工作流...")
    state = await graph.execute(WorkflowState())

    print("\n✅ 工作流执行完成")
    print(f"  执行路径: {' → '.join(state.history)}")
    print(f"  最终状态: {dict(state.data)}")

    # 生成带执行结果的可视化
    html_file_with_result = "workflow_with_results.html"
    visualize_workflow(graph, "html", html_file_with_result, workflow_state=state)
    print(f"✅ 已生成执行结果可视化: {html_file_with_result}")


async def main():
    """主函数"""
    print("\n" + "🎯" * 30)
    print("  DAG任务流优雅可视化演示")
    print("🎯" * 30)

    # Demo 1: 任务DAG可视化
    await demo_task_visualization()

    # Demo 2: 工作流可视化
    await demo_workflow_visualization()

    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print("\n📁 生成的文件:")
    print("  • task_dag_visualization.html - 任务DAG (无执行结果)")
    print("  • task_dag_with_results.html  - 任务DAG (含执行结果)")
    print("  • task_dag.dot                - Graphviz DOT格式")
    print("  • workflow_visualization.html - 工作流图 (无执行结果)")
    print("  • workflow_with_results.html  - 工作流图 (含执行结果)")
    print("\n💡 提示:")
    print("  1. 在浏览器中打开 .html 文件查看交互式可视化")
    print("  2. 将 Mermaid 代码复制到 Markdown 文档中")
    print("  3. 使用 Graphviz 生成高质量图片:")
    print("     dot -Tpng task_dag.dot -o task_dag.png")
    print("     dot -Tsvg task_dag.dot -o task_dag.svg")
    print()


if __name__ == "__main__":
    asyncio.run(main())
