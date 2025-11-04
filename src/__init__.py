"""
Multi-Agent Intelligent Scheduler

A flexible scheduler that coordinates multiple AI agents (Claude, OpenAI, Codex, Gemini)
to execute complex tasks in parallel or serial mode with intelligent dependency resolution.
"""

__version__ = "1.0.0"
__author__ = "FDU OS Course Group"

# Lazy imports to avoid dependency errors when modules are imported individually
__all__ = [
    "MultiAgentScheduler",
    "Task",
    "ExecutionMode",
    "ClaudeAgent",
    "ClaudeCLIAgent",
    "CodexExecAgent",
    "GeminiAgent",
    "MetaAgent",
    "MetaAgentCLI",
    "ExecutionLogger",
    "TaskVisualizer",
    "WorkspaceManager",
]
