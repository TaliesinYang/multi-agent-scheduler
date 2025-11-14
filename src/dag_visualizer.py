"""
优雅的DAG任务流可视化模块

支持多种可视化格式:
- JSON (用于Web前端)
- Mermaid (用于Markdown文档)
- Graphviz DOT (用于专业图形)
- HTML (内嵌SVG，可独立查看)

灵感来源: Apache Airflow, LangGraph
"""

import json
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisualizationFormat(Enum):
    """可视化格式"""
    JSON = "json"
    MERMAID = "mermaid"
    GRAPHVIZ = "graphviz"
    HTML = "html"
    SVG = "svg"


@dataclass
class VisualNode:
    """可视化节点"""
    id: str
    label: str
    status: NodeStatus
    node_type: str = "task"  # task, start, end, condition
    metadata: Dict[str, Any] = None

    # 执行信息
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None

    # Agent信息
    agent: Optional[str] = None

    # 样式
    color: Optional[str] = None
    shape: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # 自动设置颜色
        if self.color is None:
            self.color = self._get_status_color()

    def _get_status_color(self) -> str:
        """根据状态获取颜色"""
        color_map = {
            NodeStatus.PENDING: "#gray",
            NodeStatus.RUNNING: "#3498db",  # 蓝色
            NodeStatus.COMPLETED: "#2ecc71",  # 绿色
            NodeStatus.FAILED: "#e74c3c",  # 红色
            NodeStatus.SKIPPED: "#95a5a6"  # 灰色
        }
        return color_map.get(self.status, "#bdc3c7")


@dataclass
class VisualEdge:
    """可视化边"""
    source: str
    target: str
    label: Optional[str] = None
    edge_type: str = "normal"  # normal, conditional, dependency
    metadata: Dict[str, Any] = None

    # 样式
    color: Optional[str] = None
    style: Optional[str] = None  # solid, dashed, dotted

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DAGVisualizer:
    """
    DAG可视化器

    功能:
    - 多格式导出 (JSON, Mermaid, Graphviz, HTML)
    - 自动布局优化
    - 实时状态更新
    - 交互式Web视图

    Example:
        >>> from src.scheduler import Task, MultiAgentScheduler
        >>> tasks = [Task(...), Task(...)]
        >>> viz = DAGVisualizer.from_tasks(tasks)
        >>> viz.export_json("dag.json")
        >>> viz.export_html("dag.html")
    """

    def __init__(self):
        self.nodes: Dict[str, VisualNode] = {}
        self.edges: List[VisualEdge] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "title": "Task DAG",
            "description": ""
        }

    def add_node(self, node: VisualNode):
        """添加节点"""
        self.nodes[node.id] = node

    def add_edge(self, edge: VisualEdge):
        """添加边"""
        self.edges.append(edge)

    def update_node_status(self, node_id: str, status: NodeStatus,
                          duration: Optional[float] = None,
                          agent: Optional[str] = None):
        """更新节点状态"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = status
            node.color = node._get_status_color()

            if duration is not None:
                node.duration = duration

            if agent is not None:
                node.agent = agent

            # 更新时间戳
            if status == NodeStatus.RUNNING and node.start_time is None:
                node.start_time = datetime.now().isoformat()
            elif status in [NodeStatus.COMPLETED, NodeStatus.FAILED]:
                node.end_time = datetime.now().isoformat()

    @classmethod
    def from_tasks(cls, tasks: List, execution_result: Optional[Any] = None) -> 'DAGVisualizer':
        """
        从任务列表创建可视化器

        Args:
            tasks: Task对象列表
            execution_result: 执行结果 (可选)

        Returns:
            DAGVisualizer实例
        """
        viz = cls()

        # 添加所有任务节点
        for task in tasks:
            status = NodeStatus.PENDING
            duration = None
            agent = None

            # 如果有执行结果，获取状态
            if execution_result and hasattr(execution_result, 'task_results'):
                task_result = execution_result.task_results.get(task.id)
                if task_result:
                    if task_result.success:
                        status = NodeStatus.COMPLETED
                    else:
                        status = NodeStatus.FAILED

                    duration = getattr(task_result, 'duration', None)
                    agent = getattr(task_result, 'agent_type', None)

            node = VisualNode(
                id=task.id,
                label=task.prompt[:50] + "..." if len(task.prompt) > 50 else task.prompt,
                status=status,
                node_type="task",
                metadata={
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "full_prompt": task.prompt
                },
                duration=duration,
                agent=agent
            )
            viz.add_node(node)

        # 添加依赖边
        for task in tasks:
            for dep_id in task.depends_on:
                edge = VisualEdge(
                    source=dep_id,
                    target=task.id,
                    edge_type="dependency",
                    style="solid"
                )
                viz.add_edge(edge)

        viz.metadata["title"] = f"Task DAG ({len(tasks)} tasks)"
        viz.metadata["total_tasks"] = len(tasks)

        return viz

    @classmethod
    def from_workflow(cls, workflow_graph, workflow_state: Optional[Any] = None) -> 'DAGVisualizer':
        """
        从WorkflowGraph创建可视化器

        Args:
            workflow_graph: WorkflowGraph实例
            workflow_state: WorkflowState (可选)

        Returns:
            DAGVisualizer实例
        """
        viz = cls()

        # 添加所有节点
        for node_id, node in workflow_graph.nodes.items():
            # 确定状态
            status = NodeStatus.PENDING
            if workflow_state and node_id in workflow_state.history:
                status = NodeStatus.COMPLETED

            visual_node = VisualNode(
                id=node_id,
                label=node_id,
                status=status,
                node_type=node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                metadata=node.config if hasattr(node, 'config') else {}
            )
            viz.add_node(visual_node)

        # 添加所有边
        for edge in workflow_graph.edges:
            visual_edge = VisualEdge(
                source=edge.from_node,
                target=edge.to_node,
                label=edge.label,
                edge_type=edge.edge_type.value if hasattr(edge.edge_type, 'value') else str(edge.edge_type),
                style="dashed" if "conditional" in str(edge.edge_type).lower() else "solid"
            )
            viz.add_edge(visual_edge)

        viz.metadata["title"] = f"Workflow Graph ({len(viz.nodes)} nodes)"
        viz.metadata["graph_id"] = workflow_graph.graph_id

        return viz

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "metadata": self.metadata,
            "nodes": [
                {
                    **asdict(node),
                    "status": node.status.value
                }
                for node in self.nodes.values()
            ],
            "edges": [asdict(edge) for edge in self.edges]
        }

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        导出为JSON格式

        Args:
            filepath: 保存路径 (可选)

        Returns:
            JSON字符串
        """
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def export_mermaid(self, filepath: Optional[str] = None) -> str:
        """
        导出为Mermaid格式 (适合Markdown文档)

        Returns:
            Mermaid diagram字符串
        """
        lines = ["```mermaid", "graph TD"]

        # 添加节点
        for node in self.nodes.values():
            # 样式映射
            shape_start = "["
            shape_end = "]"

            if node.node_type == "start":
                shape_start = "(("
                shape_end = "))"
            elif node.node_type == "end":
                shape_start = "(["
                shape_end = "])"
            elif node.node_type == "condition":
                shape_start = "{"
                shape_end = "}"

            # 节点定义
            label = node.label.replace('"', "'")
            lines.append(f'    {node.id}{shape_start}"{label}"{shape_end}')

            # 节点样式
            if node.status == NodeStatus.COMPLETED:
                lines.append(f'    style {node.id} fill:#2ecc71,stroke:#27ae60,stroke-width:2px')
            elif node.status == NodeStatus.FAILED:
                lines.append(f'    style {node.id} fill:#e74c3c,stroke:#c0392b,stroke-width:2px')
            elif node.status == NodeStatus.RUNNING:
                lines.append(f'    style {node.id} fill:#3498db,stroke:#2980b9,stroke-width:3px')

        # 添加边
        for edge in self.edges:
            arrow = "-->"
            label_str = ""

            if edge.style == "dashed":
                arrow = "-.->"
            elif edge.style == "dotted":
                arrow = "-..->"

            if edge.label:
                label_str = f'|{edge.label}|'

            lines.append(f'    {edge.source} {arrow}{label_str} {edge.target}')

        lines.append("```")

        mermaid_str = "\n".join(lines)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(mermaid_str)

        return mermaid_str

    def export_graphviz(self, filepath: Optional[str] = None) -> str:
        """
        导出为Graphviz DOT格式

        Returns:
            DOT格式字符串
        """
        lines = ['digraph TaskDAG {']
        lines.append('    rankdir=TB;')
        lines.append('    node [style=filled, fontname="Arial"];')
        lines.append('    edge [fontname="Arial"];')
        lines.append('')

        # 添加节点
        for node in self.nodes.values():
            # 形状
            shape = "box"
            if node.node_type == "start":
                shape = "ellipse"
            elif node.node_type == "end":
                shape = "doublecircle"
            elif node.node_type == "condition":
                shape = "diamond"

            # 标签
            label = node.label.replace('"', '\\"')
            if node.agent:
                label += f"\\n[{node.agent}]"
            if node.duration:
                label += f"\\n{node.duration:.2f}s"

            # 颜色
            fillcolor = node.color.lstrip('#')

            lines.append(
                f'    "{node.id}" [label="{label}", shape={shape}, '
                f'fillcolor="#{fillcolor}"];'
            )

        lines.append('')

        # 添加边
        for edge in self.edges:
            style = edge.style or "solid"
            label = f'label="{edge.label}"' if edge.label else ''

            lines.append(
                f'    "{edge.source}" -> "{edge.target}" '
                f'[style={style}, {label}];'
            )

        lines.append('}')

        dot_str = '\n'.join(lines)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(dot_str)

        return dot_str

    def export_html(self, filepath: Optional[str] = None,
                   include_d3: bool = True) -> str:
        """
        导出为独立HTML文件 (使用D3.js或Cytoscape.js)

        Args:
            filepath: 保存路径
            include_d3: 使用D3.js (True) 或 Cytoscape.js (False)

        Returns:
            HTML字符串
        """
        if include_d3:
            html = self._generate_d3_html()
        else:
            html = self._generate_cytoscape_html()

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

        return html

    def _generate_d3_html(self) -> str:
        """生成基于D3.js的HTML"""
        json_data = self.to_dict()
        json_data_str = json.dumps(json_data, ensure_ascii=False)
        title = self.metadata.get("title", "Task DAG")
        description = self.metadata.get("description", "可视化任务调度流程与依赖关系")

        # 使用字符串拼接避免f-string语法冲突
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>""" + title + """</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { margin: 20px; font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 1400px; margin: 20px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { color: #333; margin: 0 0 10px 0; font-size: 28px; }
        .desc { color: #666; margin-bottom: 20px; }
        #graph { width: 100%; height: 600px; border: 1px solid #ddd; background: #fafafa; border-radius: 8px; }
        .node { cursor: pointer; }
        .node circle { stroke: #fff; stroke-width: 3px; transition: all 0.3s; }
        .node:hover circle { filter: brightness(1.1); }
        .node text { font-size: 12px; fill: white; text-anchor: middle; pointer-events: none; font-weight: 600; }
        .link { fill: none; stroke: #999; stroke-width: 2px; marker-end: url(#arrowhead); }
        .legend { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0; }
        .legend-item { display: inline-block; margin-right: 20px; font-size: 14px; }
        .legend-color { display: inline-block; width: 16px; height: 16px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
    </style>
</head>
<body>
    <div class="container">
        <h1>""" + title + """</h1>
        <div class="desc">""" + description + """</div>
        <svg id="graph"></svg>
        <div class="legend">
            <div class="legend-item"><span class="legend-color" style="background: #2ecc71;"></span>已完成</div>
            <div class="legend-item"><span class="legend-color" style="background: #3498db;"></span>执行中</div>
            <div class="legend-item"><span class="legend-color" style="background: gray;"></span>待执行</div>
            <div class="legend-item"><span class="legend-color" style="background: #e74c3c;"></span>失败</div>
        </div>
    </div>
    <script>
        var data = """ + json_data_str + """;
        
        var width = document.getElementById('graph').clientWidth;
        var height = 600;
        
        var svg = d3.select("#graph").attr("viewBox", [0, 0, width, height]);
        
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");
        
        var simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.edges).id(function(d) { return d.id; }).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));
        
        var link = svg.append("g")
            .selectAll("path")
            .data(data.edges)
            .join("path")
            .attr("class", "link");
        
        var node = svg.append("g")
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        node.append("circle")
            .attr("r", 30)
            .attr("fill", function(d) { return d.color || "#bdc3c7"; });
        
        node.append("text")
            .attr("dy", ".35em")
            .text(function(d) { return d.id; });
        
        node.append("title")
            .text(function(d) { 
                var text = d.label + " - Status: " + d.status;
                if (d.agent) text += " - Agent: " + d.agent;
                if (d.duration) text += " - Duration: " + d.duration.toFixed(2) + "s";
                return text;
            });
        
        simulation.on("tick", function() {
            link.attr("d", function(d) {
                var dx = d.target.x - d.source.x;
                var dy = d.target.y - d.source.y;
                var dr = Math.sqrt(dx * dx + dy * dy);
                return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
            });
            
            node.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        });
        
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    </script>
</body>
</html>"""
        
        return html


    def _generate_cytoscape_html(self) -> str:
        """生成基于Cytoscape.js的HTML (更适合复杂图)"""
        # 简化版本，可以进一步扩展
        return self._generate_d3_html()  # 暂时使用D3版本

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.nodes)
        status_counts = {}

        for node in self.nodes.values():
            status = node.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_nodes": total,
            "total_edges": len(self.edges),
            "status_breakdown": status_counts,
            "completion_rate": (status_counts.get("completed", 0) / total * 100) if total > 0 else 0,
            "failure_rate": (status_counts.get("failed", 0) / total * 100) if total > 0 else 0
        }


# 便捷函数

def visualize_tasks(tasks: List, output_format: str = "html",
                   filepath: Optional[str] = None,
                   execution_result: Optional[Any] = None) -> str:
    """
    快速可视化任务列表

    Args:
        tasks: Task列表
        output_format: 输出格式 (json, mermaid, graphviz, html)
        filepath: 保存路径 (可选)
        execution_result: 执行结果 (可选)

    Returns:
        可视化字符串

    Example:
        >>> from src.scheduler import Task
        >>> tasks = [Task(...), Task(...)]
        >>> html = visualize_tasks(tasks, "html", "dag.html")
    """
    viz = DAGVisualizer.from_tasks(tasks, execution_result)

    if output_format == "json":
        return viz.export_json(filepath)
    elif output_format == "mermaid":
        return viz.export_mermaid(filepath)
    elif output_format == "graphviz":
        return viz.export_graphviz(filepath)
    elif output_format == "html":
        return viz.export_html(filepath)
    else:
        raise ValueError(f"Unknown format: {output_format}")


def visualize_workflow(workflow_graph, output_format: str = "html",
                      filepath: Optional[str] = None,
                      workflow_state: Optional[Any] = None) -> str:
    """
    快速可视化工作流

    Args:
        workflow_graph: WorkflowGraph实例
        output_format: 输出格式
        filepath: 保存路径 (可选)
        workflow_state: WorkflowState (可选)

    Returns:
        可视化字符串
    """
    viz = DAGVisualizer.from_workflow(workflow_graph, workflow_state)

    if output_format == "json":
        return viz.export_json(filepath)
    elif output_format == "mermaid":
        return viz.export_mermaid(filepath)
    elif output_format == "graphviz":
        return viz.export_graphviz(filepath)
    elif output_format == "html":
        return viz.export_html(filepath)
    else:
        raise ValueError(f"Unknown format: {output_format}")


# 示例使用
if __name__ == "__main__":
    from src.scheduler import Task

    # 创建示例任务
    tasks = [
        Task(id="task1", prompt="分析需求", task_type="analysis"),
        Task(id="task2", prompt="设计架构", task_type="design", depends_on=["task1"]),
        Task(id="task3", prompt="实现功能A", task_type="coding", depends_on=["task2"]),
        Task(id="task4", prompt="实现功能B", task_type="coding", depends_on=["task2"]),
        Task(id="task5", prompt="集成测试", task_type="testing", depends_on=["task3", "task4"]),
    ]

    # 生成HTML可视化
    html = visualize_tasks(tasks, "html", "task_dag_demo.html")
    print("✅ 已生成 task_dag_demo.html")

    # 生成Mermaid图 (用于文档)
    mermaid = visualize_tasks(tasks, "mermaid")
    print("\n📊 Mermaid图表:")
    print(mermaid)
