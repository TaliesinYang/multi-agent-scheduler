"""
Streaming Response Example

Demonstrates how to use streaming responses with the Multi-Agent Scheduler.
"""

import asyncio
import os
from src.agents import ClaudeAgent, OpenAIAgent
from src.scheduler import MultiAgentScheduler, Task


async def example_basic_streaming():
    """
    Example 1: Basic streaming with a single agent
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Agent Streaming")
    print("=" * 60)

    # Initialize agent (requires API key)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping example")
        return

    agent = ClaudeAgent(api_key=api_key)

    # Stream response
    print("\n🌊 Streaming response:")
    print("-" * 60)

    async for chunk in agent.call_stream("Explain async/await in Python in 3 sentences"):
        print(chunk, end='', flush=True)

    print("\n" + "-" * 60)
    print("✅ Streaming completed!\n")


async def example_scheduler_streaming():
    """
    Example 2: Streaming with scheduler
    """
    print("\n" + "=" * 60)
    print("Example 2: Scheduler Streaming")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping example")
        return

    # Setup
    agents = {
        'claude': ClaudeAgent(api_key=api_key)
    }
    scheduler = MultiAgentScheduler(agents=agents)

    task = Task(
        id="task1",
        prompt="Write a haiku about programming",
        task_type="creative"
    )

    # Stream task execution
    print("\n🌊 Streaming task execution:")
    print("-" * 60)

    async for chunk_data in scheduler.execute_task_stream(task, 'claude'):
        if not chunk_data['done']:
            # Print intermediate chunks
            print(chunk_data['chunk'], end='', flush=True)
        else:
            # Print final result info
            print("\n" + "-" * 60)
            print(f"✅ Task completed in {chunk_data['latency']:.2f}s")
            print(f"   Success: {chunk_data['success']}")
            print(f"   Full result length: {len(chunk_data['result'])} chars\n")


async def example_realtime_feedback():
    """
    Example 3: Real-time feedback with character counting
    """
    print("\n" + "=" * 60)
    print("Example 3: Real-time Feedback")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping example")
        return

    agent = ClaudeAgent(api_key=api_key)

    print("\n🌊 Streaming with real-time stats:")
    print("-" * 60)

    char_count = 0
    word_count = 0
    last_char = ""

    async for chunk in agent.call_stream("List 5 benefits of Python in bullet points"):
        print(chunk, end='', flush=True)

        # Track stats
        char_count += len(chunk)
        for char in chunk:
            if char == " " and last_char != " ":
                word_count += 1
            last_char = char

    print("\n" + "-" * 60)
    print(f"📊 Stats: {char_count} characters, ~{word_count} words")
    print(f"✅ Streaming completed!\n")


async def example_websocket_ready():
    """
    Example 4: WebSocket-ready streaming (simulated)
    """
    print("\n" + "=" * 60)
    print("Example 4: WebSocket-Ready Format")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping example")
        return

    agent = ClaudeAgent(api_key=api_key)

    print("\n🌊 Simulating WebSocket streaming:")
    print("-" * 60)

    async def simulate_websocket_send(message: dict):
        """Simulate sending to WebSocket"""
        print(f"WS → {message}")

    async for chunk in agent.call_stream("What is Docker in one sentence?"):
        # Send each chunk as JSON (WebSocket format)
        await simulate_websocket_send({
            "type": "chunk",
            "data": chunk,
            "timestamp": asyncio.get_event_loop().time()
        })

    # Send completion message
    await simulate_websocket_send({
        "type": "complete",
        "timestamp": asyncio.get_event_loop().time()
    })

    print("-" * 60)
    print("✅ WebSocket simulation completed!\n")


async def example_multiple_agents_comparison():
    """
    Example 5: Compare streaming from different agents
    """
    print("\n" + "=" * 60)
    print("Example 5: Multi-Agent Comparison")
    print("=" * 60)

    claude_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not (claude_key or openai_key):
        print("⚠️  No API keys set, skipping example")
        return

    agents = {}
    if claude_key:
        agents['claude'] = ClaudeAgent(api_key=claude_key)
    if openai_key:
        agents['openai'] = OpenAIAgent(api_key=openai_key)

    prompt = "Explain what is REST API in 2 sentences"

    for agent_name, agent in agents.items():
        print(f"\n🌊 {agent_name.upper()} streaming:")
        print("-" * 60)

        import time
        start = time.time()

        async for chunk in agent.call_stream(prompt):
            print(chunk, end='', flush=True)

        elapsed = time.time() - start
        print(f"\n⏱️  Completed in {elapsed:.2f}s")
        print("-" * 60)

    print("\n✅ All agents completed!\n")


async def example_error_handling():
    """
    Example 6: Error handling in streaming
    """
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    # Use invalid API key to trigger error
    agent = ClaudeAgent(api_key="invalid-key-12345")

    print("\n🌊 Attempting to stream with invalid API key:")
    print("-" * 60)

    error_occurred = False
    async for chunk in agent.call_stream("Test prompt"):
        print(chunk, end='', flush=True)
        if "[ERROR:" in chunk:
            error_occurred = True

    print("\n" + "-" * 60)
    if error_occurred:
        print("✅ Error handled gracefully in stream")
    else:
        print("⚠️  No error detected (unexpected)")

    print()


async def main():
    """
    Run all examples
    """
    print("\n" + "=" * 60)
    print("🌊 STREAMING RESPONSE EXAMPLES")
    print("=" * 60)
    print("\nThese examples demonstrate the streaming capabilities")
    print("of the Multi-Agent Scheduler framework.")
    print("\nNote: Requires API keys to be set in environment variables:")
    print("  - ANTHROPIC_API_KEY")
    print("  - OPENAI_API_KEY (optional)")
    print("=" * 60)

    # Run examples
    await example_basic_streaming()
    await example_scheduler_streaming()
    await example_realtime_feedback()
    await example_websocket_ready()
    await example_multiple_agents_comparison()
    await example_error_handling()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
