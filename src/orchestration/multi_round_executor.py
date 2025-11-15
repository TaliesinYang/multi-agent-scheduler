"""
Multi-Round Dialogue Executor

Implements agent-tool interaction loop for complex tasks requiring multiple steps.
"""

from typing import Dict, Any, List, Optional
from agents import BaseAgent
from adapters import ToolRegistry, AGENTBENCH_TOOLS


class MultiRoundExecutor:
    """
    Multi-round dialogue executor for agent-tool interaction

    Manages the iterative loop:
    1. Agent receives task prompt
    2. Agent requests tool calls
    3. Tools execute and return results
    4. Agent receives results and continues
    5. Repeat until task complete or max rounds reached

    Features:
    - Anthropic message format compliance
    - FINAL_ANSWER detection for task completion
    - Round limit enforcement
    - Complete conversation history tracking

    Example:
        executor = MultiRoundExecutor(agent=claude_agent, tool_registry=registry)
        result = await executor.execute_task(
            "Find all users with age > 18 in the database",
            max_rounds=20
        )
        print(result["final_answer"])
        print(f"Completed in {result['rounds']} rounds")
    """

    def __init__(
        self,
        agent: BaseAgent,
        tool_registry: ToolRegistry
    ):
        """
        Initialize multi-round executor

        Args:
            agent: Agent instance (e.g., ClaudeAgent)
            tool_registry: Tool registry for executing tool calls
        """
        self.agent = agent
        self.tool_registry = tool_registry

    async def execute_task(
        self,
        task_prompt: str,
        max_rounds: int = 20,
        verbose: bool = False,
        **agent_kwargs
    ) -> Dict[str, Any]:
        """
        Execute task with multi-round agent-tool interaction

        Args:
            task_prompt: Task description for the agent
            max_rounds: Maximum number of agent-tool rounds (default: 20)
            verbose: Print round-by-round progress (default: False)
            **agent_kwargs: Additional arguments passed to agent.call()

        Returns:
            Dict with:
                - final_answer: Final answer from agent or tool
                - rounds: Number of rounds executed
                - success: Whether task completed successfully
                - message_history: Complete conversation history
                - tool_calls_count: Total number of tool calls made

        Raises:
            RuntimeError: If tool registry not initialized
        """
        if not self.tool_registry.initialized:
            raise RuntimeError("ToolRegistry not initialized. Call initialize() first.")

        # Initialize conversation with task prompt
        messages = [{"role": "user", "content": task_prompt}]
        round_count = 0
        final_answer = None
        total_tool_calls = 0

        if verbose:
            print(f"\n{'='*60}")
            print(f"TASK: {task_prompt[:100]}...")
            print(f"{'='*60}\n")

        # Multi-round loop
        for round_num in range(1, max_rounds + 1):
            round_count = round_num

            if verbose:
                print(f"[Round {round_num}/{max_rounds}] Calling agent...")

            # Call agent with tools
            response = await self.agent.call(
                prompt=messages,
                tools=AGENTBENCH_TOOLS,
                **agent_kwargs
            )

            # Extract response components
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if verbose and content:
                print(f"[Round {round_num}] Agent response: {content[:100]}...")

            # Build assistant message (Anthropic format)
            assistant_content = []

            # Add text content if present
            if content:
                assistant_content.append({
                    "type": "text",
                    "text": content
                })

            # Add tool_use blocks
            for tool_call in tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "input": tool_call.arguments
                })

            # Append assistant message to history
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })

            # If no tool calls, agent is done
            if not tool_calls:
                final_answer = content
                if verbose:
                    print(f"[Round {round_num}] Task complete (no tool calls)")
                break

            # Execute tool calls
            total_tool_calls += len(tool_calls)
            tool_results = []
            task_complete = False

            for tool_call in tool_calls:
                if verbose:
                    print(f"[Round {round_num}] Executing tool: {tool_call.name}")
                    print(f"  Arguments: {tool_call.arguments}")

                try:
                    # Execute tool
                    result = await self.tool_registry.execute_tool(
                        tool_call.name,
                        tool_call.arguments
                    )

                    if verbose:
                        print(f"  Result: {result[:100]}...")

                    # Check for FINAL_ANSWER marker
                    if result.startswith("FINAL_ANSWER:"):
                        final_answer = result.replace("FINAL_ANSWER:", "").strip()
                        task_complete = True
                        if verbose:
                            print(f"[Round {round_num}] Final answer received: {final_answer[:100]}...")

                    # Add tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })

                    # Break if final answer found
                    if task_complete:
                        break

                except Exception as e:
                    # Add error as tool result
                    error_msg = f"Error executing {tool_call.name}: {str(e)}"
                    if verbose:
                        print(f"  ERROR: {error_msg}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": error_msg,
                        "is_error": True
                    })

            # Add tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # If final answer found, break
            if task_complete:
                break

        # Build result
        result = {
            "final_answer": final_answer or "Task incomplete - max rounds reached",
            "rounds": round_count,
            "success": final_answer is not None,
            "message_history": messages,
            "tool_calls_count": total_tool_calls,
            "max_rounds_reached": round_count >= max_rounds and final_answer is None
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"RESULT: {result['final_answer'][:200]}")
            print(f"Rounds: {result['rounds']}, Tool calls: {result['tool_calls_count']}")
            print(f"Success: {result['success']}")
            print(f"{'='*60}\n")

        return result

    async def execute_batch(
        self,
        tasks: List[str],
        max_rounds: int = 20,
        verbose: bool = False,
        **agent_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks sequentially

        Args:
            tasks: List of task prompts
            max_rounds: Maximum rounds per task
            verbose: Print progress
            **agent_kwargs: Arguments for agent.call()

        Returns:
            List of result dicts (one per task)
        """
        results = []

        for i, task in enumerate(tasks, 1):
            if verbose:
                print(f"\n{'#'*60}")
                print(f"TASK {i}/{len(tasks)}")
                print(f"{'#'*60}")

            result = await self.execute_task(
                task,
                max_rounds=max_rounds,
                verbose=verbose,
                **agent_kwargs
            )

            results.append(result)

        return results

    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from batch results

        Args:
            results: List of result dicts from execute_batch()

        Returns:
            Dict with success_rate, avg_rounds, avg_tool_calls, etc.
        """
        total = len(results)
        if total == 0:
            return {}

        successes = sum(1 for r in results if r["success"])
        total_rounds = sum(r["rounds"] for r in results)
        total_tool_calls = sum(r["tool_calls_count"] for r in results)
        max_rounds_hit = sum(1 for r in results if r.get("max_rounds_reached", False))

        return {
            "total_tasks": total,
            "successful_tasks": successes,
            "failed_tasks": total - successes,
            "success_rate": successes / total,
            "avg_rounds": total_rounds / total,
            "avg_tool_calls": total_tool_calls / total,
            "max_rounds_hit": max_rounds_hit,
            "max_rounds_hit_rate": max_rounds_hit / total
        }
