"""
Orchestration Layer for Multi-Round Dialogue

Manages agent-tool interaction loops and task execution.
"""

# Make docker dependency optional for CLI-only mode
try:
    from .multi_round_executor import MultiRoundExecutor
    __all__ = ['MultiRoundExecutor']
except ImportError as e:
    # Docker not available - skip MultiRoundExecutor
    # This is expected in CLI-only testing mode
    __all__ = []
