# Multi-Agent Scheduler - Usage Guide

Complete guide for using the Multi-Agent Scheduler with all optimization features.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Core Features](#core-features)
4. [Optimization Features](#optimization-features)
5. [Plugin Development](#plugin-development)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-agent-scheduler.git
cd multi-agent-scheduler

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```python
import asyncio
from src.agents import ClaudeAgent
from src.scheduler import MultiAgentScheduler, Task

async def main():
    # Initialize agents
    agents = {
        'claude': ClaudeAgent(api_key="your-api-key")
    }

    # Create scheduler
    scheduler = MultiAgentScheduler(agents=agents)

    # Define tasks
    tasks = [
        Task(id="task1", prompt="Explain async/await in Python", task_type="analysis"),
        Task(id="task2", prompt="Write a bubble sort function", task_type="coding"),
    ]

    # Execute tasks
    result = await scheduler.execute(tasks)
    print(f"Completed {result.task_count} tasks in {result.total_time:.2f}s")

asyncio.run(main())
```

---

## Configuration

### Configuration File

Create `config.yaml` from the example:

```bash
cp config.example.yaml config.yaml
```

Edit configuration sections as needed:

```yaml
scheduler:
  max_concurrent: 10
  max_tasks: 50
  use_dynamic_complexity: true

agents:
  claude:
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 1024

cache:
  enabled: true
  max_size: 1000
  ttl: 3600
```

### Environment Variables

Environment variables override config file settings:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SCHEDULER_MAX_CONCURRENT=20
export CACHE_ENABLED=true
```

---

## Core Features

### 1. Task Decomposition with Meta-Agent

Automatically break down complex tasks into subtasks:

```python
from src.meta_agent import MetaAgent

# Using API-based meta-agent
meta = MetaAgent(api_key="your-api-key")
tasks = await meta.decompose_task("Build a todo list web app")

# Using CLI-based meta-agent (no API key needed)
from src.meta_agent import MetaAgentCLI
meta_cli = MetaAgentCLI(agent_type='claude')
tasks = await meta_cli.decompose_task("Build a todo list web app")
```

### 2. Dynamic Complexity Analysis

Tasks are automatically analyzed for complexity:

```python
from src.complexity_analyzer import get_analyzer

analyzer = get_analyzer()
score = analyzer.analyze("Build a microservices architecture")

print(f"Complexity: {score.level}")
print(f"Recommended subtasks: {score.recommended_subtasks}")
print(f"Reasoning: {score.reasoning}")
```

### 3. Dependency Management

Define task dependencies:

```python
tasks = [
    Task(id="task1", prompt="Create database schema", depends_on=[]),
    Task(id="task2", prompt="Build API endpoints", depends_on=["task1"]),
    Task(id="task3", prompt="Create frontend", depends_on=["task2"]),
]

# Scheduler automatically handles execution order
result = await scheduler.execute_auto(tasks)
```

---

## Optimization Features

### 1. Result Caching

Avoid redundant API calls with automatic caching:

```python
from src.cache import get_global_cache

# Cache is automatically used by agents when enabled in config
cache = get_global_cache(max_size=1000, ttl=3600)

# Manual usage
cached_result = cache.get(prompt)
if cached_result is None:
    result = await agent.call(prompt)
    cache.set(prompt, result)
else:
    result = cached_result

# Check cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

### 2. Connection Pooling

Reuse API client connections automatically:

```python
from src.connection_pool import get_pooled_claude_client

# Connections are automatically pooled
client = get_pooled_claude_client(api_key)

# Check pool statistics
from src.connection_pool import get_connection_pool
pool = get_connection_pool()
stats = pool.get_stats()
print(f"Claude reuses: {stats['claude_reuses']}")
```

### 3. Secure API Key Management

Encrypt API keys at rest:

```python
from src.security import get_key_manager

manager = get_key_manager(master_password='your-secure-password')

# Store encrypted key
manager.set_key('ANTHROPIC_API_KEY', 'sk-ant-...')

# Retrieve decrypted key
api_key = manager.get_key('ANTHROPIC_API_KEY')

# Keys are encrypted on disk
manager.save()
```

### 4. Input Validation

Automatically validate and sanitize inputs:

```python
from src.validation import get_validator

validator = get_validator()

# Validate prompt
is_valid, error = validator.validate_prompt(user_input)
if not is_valid:
    print(f"Invalid input: {error}")
    return

# Sanitize prompt
clean_prompt = validator.sanitize_prompt(user_input)
```

### 5. Event System

Subscribe to system events:

```python
from src.events import get_event_bus, Events

bus = get_event_bus()

# Register event listener
async def on_task_complete(event):
    print(f"Task {event.data['task_id']} completed!")
    print(f"Success: {event.data['success']}")

bus.on(Events.TASK_COMPLETED, on_task_complete)

# Events are automatically emitted by scheduler
```

### 6. Metrics Collection

Track performance metrics:

```python
from src.metrics import get_metrics

metrics = get_metrics()

# Metrics are automatically collected when enabled
# View statistics
metrics.print_stats()

# Sample output:
# === Metrics Summary ===
# Counters:
#   tasks.completed: 42
#   tasks.failed: 3
#
# Timers:
#   task.execution:
#     count: 45
#     mean: 2.34s
#     p50: 2.10s
#     p95: 4.20s
#     p99: 5.80s
```

### 7. Workspace Sandboxing

Secure file operations with sandboxing:

```python
from src.workspace_lock import SandboxedWorkspaceManager

manager = SandboxedWorkspaceManager(base_dir='workspaces')

# Create workspace
workspace = await manager.create_workspace('my_project')

# Write file (with automatic locking and validation)
await manager.write_file(workspace / 'output.txt', 'Hello, world!')

# Read file
content = await manager.read_file(workspace / 'output.txt')

# Get workspace info
info = manager.get_workspace_info(workspace)
print(f"Files: {info['file_count']}, Size: {info['total_size']} bytes")
```

### 8. Dependency Injection

Use dependency injection for testability:

```python
from src.dependency_injection import SchedulerDependencies

# Bundle dependencies
deps = SchedulerDependencies(
    agents=agents,
    logger=logger,
    config=config,
    metrics=metrics,
    event_bus=event_bus,
    cache=cache
)

# Create scheduler with DI
scheduler = MultiAgentScheduler(dependencies=deps)

# Or use legacy way (still supported)
scheduler = MultiAgentScheduler(agents=agents, logger=logger)
```

---

## Plugin Development

### Creating a Plugin

```python
from src.plugin_system import Plugin, PluginMetadata, PluginHook

class MyPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="My custom plugin",
            hooks=[
                PluginHook.BEFORE_TASK,
                PluginHook.AFTER_TASK,
            ]
        )

    async def initialize(self, config: dict) -> None:
        """Initialize plugin with configuration"""
        self.config = config
        print(f"Plugin initialized with config: {config}")

    async def on_hook(self, hook: PluginHook, context: dict):
        """Handle hook events"""
        if hook == PluginHook.BEFORE_TASK:
            task_id = context.get('task_id')
            print(f"[MyPlugin] Task {task_id} starting...")

            # Modify context (optional)
            return {'custom_field': 'value'}

        elif hook == PluginHook.AFTER_TASK:
            task_id = context.get('task_id')
            success = context.get('success')
            print(f"[MyPlugin] Task {task_id} completed: {success}")

    async def cleanup(self) -> None:
        """Cleanup resources"""
        print("[MyPlugin] Cleaning up...")
```

### Using Plugins

```python
from src.plugin_system import get_plugin_manager

manager = get_plugin_manager()

# Register plugin
manager.register(MyPlugin())

# Initialize plugins with config
await manager.initialize_plugins({
    'plugins': {
        'my_plugin': {
            'setting1': 'value1'
        }
    }
})

# Plugins automatically execute on hooks

# List registered plugins
for plugin_info in manager.list_plugins():
    print(f"{plugin_info['name']} v{plugin_info['version']} - {plugin_info['enabled']}")
```

### Plugin Hooks

Available hook points:

- `BEFORE_EXECUTION` - Before task batch execution
- `AFTER_EXECUTION` - After task batch completion
- `BEFORE_TASK` - Before individual task execution
- `AFTER_TASK` - After individual task completion
- `BEFORE_AGENT_CALL` - Before agent API call
- `AFTER_AGENT_CALL` - After agent API call
- `BEFORE_DECOMPOSITION` - Before meta-agent decomposition
- `AFTER_DECOMPOSITION` - After meta-agent decomposition
- `ON_STARTUP` - System startup
- `ON_SHUTDOWN` - System shutdown

---

## Best Practices

### 1. API Key Management

**DO:**
- Use environment variables for API keys
- Encrypt keys at rest with SecureKeyManager
- Rotate keys regularly

**DON'T:**
- Commit API keys to version control
- Share keys in plain text
- Use production keys for testing

### 2. Task Design

**DO:**
- Keep tasks atomic (< 5 minutes)
- Specify clear dependencies
- Use appropriate task types

**DON'T:**
- Create overly broad tasks
- Create circular dependencies
- Mix multiple concerns in one task

### 3. Performance Optimization

**DO:**
- Enable caching for repeated operations
- Use connection pooling
- Monitor metrics regularly
- Use dynamic complexity analysis

**DON'T:**
- Disable all optimizations without testing
- Ignore cache hit rates
- Skip performance monitoring

### 4. Error Handling

**DO:**
- Enable input validation
- Handle agent failures gracefully
- Log errors with context

**DON'T:**
- Ignore validation warnings
- Assume all API calls succeed
- Swallow exceptions silently

---

## Troubleshooting

### Common Issues

#### 1. "API Key Not Found"

**Solution:**
```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# Or set it
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### 2. "Circular Dependency Detected"

**Solution:**
```python
# Review task dependencies
for task in tasks:
    print(f"{task.id} depends on: {task.depends_on}")

# Ensure no cycles in dependency graph
```

#### 3. "Cache Hit Rate Too Low"

**Solution:**
```python
# Increase cache size
cache = ResultCache(max_size=5000, ttl=7200)

# Check cache configuration
config.set('cache.max_size', 5000)
config.set('cache.ttl', 7200)
```

#### 4. "Plugin Not Loading"

**Solution:**
```python
# Check plugin directory
manager.load_from_directory('plugins')

# Verify plugin class inherits from Plugin
# Check plugin metadata is correct
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set in config:
```yaml
logging:
  log_level: "DEBUG"
```

### Performance Profiling

```python
from src.metrics import get_metrics

metrics = get_metrics()

# Run your tasks
await scheduler.execute(tasks)

# Print detailed statistics
metrics.print_stats()
```

---

## Advanced Topics

### Custom Agent Implementation

```python
from src.agents import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="custom", **kwargs)
        # Initialize your client

    async def call(self, prompt: str, **kwargs) -> dict:
        # Implement your agent logic
        try:
            # Make API call
            result = await your_api_call(prompt)

            return {
                'agent': self.name,
                'result': result,
                'success': True,
                'latency': 0.5
            }
        except Exception as e:
            return {
                'agent': self.name,
                'error': str(e),
                'success': False
            }
```

### Custom Complexity Analyzer

```python
from src.complexity_analyzer import ComplexityAnalyzer, ComplexityScore

class CustomComplexityAnalyzer(ComplexityAnalyzer):
    def analyze(self, task_description: str) -> ComplexityScore:
        # Your custom logic
        score = super().analyze(task_description)

        # Add custom rules
        if 'blockchain' in task_description.lower():
            score.score += 20

        return score
```

---

## Additional Resources

- [API Reference](API_REFERENCE.md)
- [Optimization Details](OPTIMIZATIONS.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## Support

For issues and questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Search [GitHub Issues](https://github.com/yourusername/multi-agent-scheduler/issues)
3. Create a new issue with:
   - Clear description
   - Code sample
   - Error messages
   - Environment details

---

**Last Updated:** 2025-01-13
**Version:** 2.0.0
