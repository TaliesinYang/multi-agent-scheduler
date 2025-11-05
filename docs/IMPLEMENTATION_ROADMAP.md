# Implementation Roadmap: Multi-Agent Code CLI

## Overview

Transform the existing multi-agent scheduler into an interactive CLI tool similar to Claude Code, with multi-agent orchestration capabilities.

---

## Current State Analysis

### What We Have ✅

1. **Core Scheduler** (`src/scheduler.py`)
   - Dependency resolution
   - Parallel execution
   - Task management

2. **Meta-Agent** (`src/meta_agent.py`)
   - Task decomposition
   - Claude API integration
   - CLI version available

3. **Multiple Agents** (`src/agents.py`)
   - ClaudeAgent (API)
   - OpenAIAgent (API)
   - ClaudeCLIAgent
   - CodexCLIAgent
   - GeminiAgent

4. **Demo Scripts** (`demos/`)
   - Basic workflows
   - Mock mode for testing

### What We Need to Build 🔨

1. **Interactive REPL**
   - Command-line interface with prompt
   - Session management
   - Command history

2. **Streaming Output**
   - Real-time agent responses
   - Progress indicators
   - Formatted output

3. **Context Management**
   - Conversation history
   - File/project context
   - Workspace management

4. **Configuration System**
   - User preferences
   - Agent configuration
   - API key management

5. **Tool Integration**
   - File operations
   - Git commands
   - Code execution

---

## Phase 1: MVP (4-6 weeks)

### Week 1: Interactive REPL Foundation

**Goal**: Basic interactive CLI that can accept commands and maintain session

**Tasks**:

1. **Create REPL Core** (`src/cli/repl.py`)
   ```python
   - [ ] Command input loop with prompt
   - [ ] Basic command parsing
   - [ ] Session initialization
   - [ ] Exit handling
   ```

2. **Session Management** (`src/cli/session.py`)
   ```python
   - [ ] Conversation history storage
   - [ ] Context accumulation
   - [ ] Session persistence (optional)
   ```

3. **Command System** (`src/cli/commands.py`)
   ```python
   - [ ] /help - Show available commands
   - [ ] /config - Show configuration
   - [ ] /agents - List available agents
   - [ ] /history - Show conversation history
   - [ ] /clear - Clear session
   - [ ] /exit - Exit CLI
   ```

**Deliverable**: Basic CLI that can start, accept input, and handle commands

**Test**:
```bash
$ python -m src.cli.main

Multi-Agent Code v0.1.0
Type '/help' for commands

macode> /help
Available commands:
  /help     - Show this help
  /config   - Show configuration
  /agents   - List agents
  /exit     - Exit

macode> /agents
Available agents:
  ✓ claude  - Claude Sonnet 4.5 (API)
  ✓ openai  - GPT-4 Turbo (API)
  ✗ gemini  - Disabled in config

macode> /exit
Goodbye!
```

---

### Week 2: Task Processing Integration

**Goal**: Connect REPL to existing Meta-Agent and Scheduler

**Tasks**:

1. **Task Processor** (`src/cli/processor.py`)
   ```python
   - [ ] Integration with MetaAgent
   - [ ] Task plan display
   - [ ] User confirmation prompt
   - [ ] Execute with Scheduler
   ```

2. **Output Formatting** (`src/cli/display.py`)
   ```python
   - [ ] Task plan pretty-print
   - [ ] Progress indicators
   - [ ] Success/error formatting
   - [ ] Agent output display
   ```

3. **Error Handling**
   ```python
   - [ ] Graceful failure handling
   - [ ] User-friendly error messages
   - [ ] Retry options
   ```

**Deliverable**: Can execute simple tasks through Meta-Agent

**Test**:
```bash
macode> Write a Python function to calculate fibonacci

🧠 Meta-Agent: Decomposing task...

📋 Plan:
  1. [claude] Write fibonacci function with memoization
  2. [claude] Add docstring and type hints
  3. [gemini] Write unit tests

Execute plan? [Y/n]: y

⚡ Executing tasks...
  ✓ [claude] Write fibonacci function (2.3s)
  ✓ [claude] Add docstring (1.1s)
  ✓ [gemini] Write unit tests (1.8s)

✅ Completed in 5.2s

📄 Results:
  - fibonacci.py (created)
  - test_fibonacci.py (created)
```

---

### Week 3: Streaming & Real-time Updates

**Goal**: Show agent output in real-time, not just final results

**Tasks**:

1. **Streaming Support** (`src/cli/streaming.py`)
   ```python
   - [ ] Async streaming from agents
   - [ ] Real-time output display
   - [ ] Interleaved multi-agent output
   ```

2. **Progress Indicators**
   ```python
   - [ ] Spinner for thinking state
   - [ ] Progress bars for long tasks
   - [ ] Status updates
   ```

3. **Formatted Output**
   ```python
   - [ ] Syntax highlighting for code
   - [ ] Markdown rendering
   - [ ] Color coding by agent
   ```

**Deliverable**: Real-time streaming output from agents

**Test**:
```bash
macode> Explain the Repository pattern

🧠 Meta-Agent: Analyzing task...

[claude] The Repository pattern is a design pattern that...

[claude] Key benefits:
[claude]   1. Separation of concerns...
[claude]   2. Testability...
[claude]   3. Flexibility...

[claude] Example implementation:
```python
class UserRepository:
    def __init__(self, db):
        self.db = db
...
```

✅ Explanation complete (4.2s)
```

---

### Week 4: Configuration & Workspace

**Goal**: Persistent configuration and workspace management

**Tasks**:

1. **Configuration System** (`src/cli/config.py`)
   ```python
   - [ ] Load from ~/.macode/config.yaml
   - [ ] Environment variable support
   - [ ] Agent enable/disable
   - [ ] API key management
   ```

2. **Workspace Manager** (`src/cli/workspace.py`)
   ```python
   - [ ] Project detection (git repo)
   - [ ] File operations
   - [ ] Code context loading
   ```

3. **Context Building**
   ```python
   - [ ] Load relevant files
   - [ ] Recent file changes
   - [ ] Project structure
   ```

**Deliverable**: Persistent configuration and workspace awareness

**Config Example** (`~/.macode/config.yaml`):
```yaml
agents:
  claude:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-5-20250929
    max_concurrent: 5

  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
    max_concurrent: 3

  gemini:
    enabled: false

preferences:
  auto_execute: false  # Ask before running
  parallel: true
  verbose: true
  color: true

workspace:
  auto_detect: true  # Auto-detect git repos
  max_context_files: 50
  exclude_patterns:
    - "node_modules/"
    - "*.pyc"
    - ".git/"
```

---

### Week 5: Polish & User Experience

**Goal**: Smooth user experience, helpful features

**Tasks**:

1. **Input Enhancement**
   ```python
   - [ ] Command history (up/down arrows)
   - [ ] Tab completion
   - [ ] Multi-line input
   ```

2. **Help System**
   ```python
   - [ ] Contextual help
   - [ ] Examples
   - [ ] Quick start guide
   ```

3. **Error Messages**
   ```python
   - [ ] Clear error descriptions
   - [ ] Suggested fixes
   - [ ] Links to docs
   ```

4. **Installation**
   ```python
   - [ ] Setup script
   - [ ] Package for pip
   - [ ] Dependencies management
   ```

**Deliverable**: Polished MVP ready for beta testing

---

### Week 6: Testing & Beta Release

**Goal**: Validate with real users, fix bugs

**Tasks**:

1. **Testing**
   ```python
   - [ ] Unit tests for core components
   - [ ] Integration tests
   - [ ] User acceptance testing
   ```

2. **Documentation**
   ```python
   - [ ] README update
   - [ ] User guide
   - [ ] API documentation
   - [ ] Example workflows
   ```

3. **Beta Release**
   ```python
   - [ ] Package on PyPI (test)
   - [ ] Recruit 10-20 beta users
   - [ ] Collect feedback
   - [ ] Bug fixes
   ```

**Deliverable**: Beta version with real user feedback

---

## Phase 2: Advanced Features (2-3 months)

### Month 2: Batch & Workflows

**Features**:
1. **Batch Processing**
   - Execute multiple tasks from file
   - Parallel batch execution
   - Progress tracking

2. **Workflow Definitions**
   - YAML workflow files
   - Reusable workflows
   - Workflow library

3. **Cost Tracking**
   - API usage tracking
   - Cost estimation
   - Budget limits

**Example**:
```bash
$ macode batch refactor-tasks.txt
Processing 15 tasks...
⚡ Running 3 tasks in parallel...
[1/15] ✓ Refactor auth.py
[2/15] ✓ Update tests
[3/15] ⚡ Optimize queries...
```

---

### Month 3: Advanced Orchestration

**Features**:
1. **Smart Agent Selection**
   - Automatic agent selection based on task
   - Cost optimization
   - Performance optimization

2. **Tool Integration**
   - Git operations
   - Testing frameworks
   - Build systems
   - Deployment tools

3. **Plugin System**
   - Custom agent plugins
   - Custom tools
   - Community plugins

**Example**:
```bash
macode> Run tests and fix any failures

[gemini] Running pytest...
[gemini] ❌ 3 tests failed in test_auth.py

🧠 Auto-fix enabled
[claude] Analyzing failures...
[claude] Identified issue: Missing mock setup
[claude] Applying fix...

[gemini] Re-running tests...
[gemini] ✅ All 45 tests passing

✅ Auto-fixed and verified
```

---

## Technical Architecture

### Project Structure

```
multi-agent-scheduler/
├── src/
│   ├── cli/                    # NEW: CLI interface
│   │   ├── __init__.py
│   │   ├── main.py            # Entry point
│   │   ├── repl.py            # Interactive loop
│   │   ├── session.py         # Session management
│   │   ├── commands.py        # Command handlers
│   │   ├── processor.py       # Task processing
│   │   ├── display.py         # Output formatting
│   │   ├── streaming.py       # Real-time output
│   │   ├── config.py          # Configuration
│   │   └── workspace.py       # Workspace management
│   │
│   ├── agents.py              # EXISTING: Agent implementations
│   ├── scheduler.py           # EXISTING: Task scheduler
│   ├── meta_agent.py          # EXISTING: Meta-agent
│   └── task.py                # EXISTING: Task definitions
│
├── config/
│   └── default_config.yaml    # NEW: Default configuration
│
├── docs/
│   ├── PRODUCT_VISION.md      # Product vision
│   ├── IMPLEMENTATION_ROADMAP.md  # This file
│   └── USER_GUIDE.md          # NEW: User documentation
│
├── tests/
│   └── cli/                   # NEW: CLI tests
│
└── setup.py                   # NEW: Package configuration
```

---

## Key Design Decisions

### 1. Use Existing Components

**Decision**: Build on top of existing scheduler, don't rebuild

**Rationale**:
- Scheduler is proven and working
- Saves development time
- Maintains backward compatibility

**Implementation**:
```python
# CLI just wraps existing components
class TaskProcessor:
    def __init__(self):
        self.meta_agent = MetaAgent(...)  # Existing
        self.scheduler = Scheduler(...)    # Existing
```

---

### 2. Streaming by Default

**Decision**: Always stream output, don't wait for completion

**Rationale**:
- Better UX (feels responsive)
- Users see progress
- Can cancel if going wrong direction

**Implementation**:
```python
async def execute_with_streaming(task):
    async for event in agent.stream(task):
        display.show(event)  # Immediate feedback
```

---

### 3. Configuration over Code

**Decision**: Use YAML config files, not command-line flags

**Rationale**:
- Easier for non-technical users
- Persistent preferences
- Shareable configurations

**Example**:
```yaml
# Good: ~/.macode/config.yaml
agents:
  claude:
    enabled: true
    model: claude-sonnet-4-5

# Not: python cli.py --claude-enabled --claude-model=sonnet
```

---

### 4. Async-First Architecture

**Decision**: Use async/await throughout

**Rationale**:
- Enables streaming
- Better for parallel execution
- Modern Python best practice

**Implementation**:
```python
# All core functions are async
async def process_task(task: str):
    plan = await meta_agent.decompose(task)
    results = await scheduler.execute(plan)
    return results
```

---

### 5. Graceful Degradation

**Decision**: Continue with available agents if some fail

**Rationale**:
- Better user experience
- More reliable
- No single point of failure

**Example**:
```
If OpenAI API is down:
  → Fall back to Claude for all tasks
  → Show warning to user
  → Continue execution
```

---

## Dependencies

### New Dependencies

```txt
# requirements.txt additions

# CLI Interface
prompt-toolkit>=3.0.0    # Advanced CLI features
rich>=13.0.0             # Beautiful terminal output
click>=8.0.0             # Command parsing

# Configuration
pyyaml>=6.0              # YAML config files
python-dotenv>=1.0.0     # .env support

# Streaming
aiostream>=0.5.0         # Async stream utilities

# Optional
colorama>=0.4.0          # Windows color support
pygments>=2.0.0          # Syntax highlighting
```

---

## Success Criteria

### MVP Success (Week 6)
- [ ] Can start CLI and get prompt
- [ ] Can execute simple tasks through Meta-Agent
- [ ] Real-time streaming output
- [ ] Configuration works
- [ ] 10 beta users give positive feedback

### Phase 2 Success (Month 2)
- [ ] Batch execution works reliably
- [ ] Workflows can be defined and run
- [ ] Cost tracking is accurate
- [ ] 100+ active users

### Phase 3 Success (Month 3)
- [ ] Smart agent selection works
- [ ] Tool integration is seamless
- [ ] Plugin system is functional
- [ ] 1000+ active users
- [ ] Community contributions

---

## Risks & Mitigation

### Risk 1: Complexity
**Risk**: Too many features, becomes hard to use
**Mitigation**:
- Start simple (MVP only)
- Progressive disclosure of features
- Excellent defaults

### Risk 2: Performance
**Risk**: Streaming adds latency
**Mitigation**:
- Optimize streaming code
- Buffer appropriately
- Allow users to disable streaming

### Risk 3: API Costs
**Risk**: Users complain about costs
**Mitigation**:
- Clear cost estimation upfront
- Budget limits
- Use cheaper models by default

### Risk 4: Reliability
**Risk**: Multi-agent system is less reliable
**Mitigation**:
- Robust error handling
- Automatic retries
- Fallback to single agent

---

## Metrics to Track

### Usage Metrics
- Daily/weekly active users
- Tasks executed per user
- Session length
- Command usage patterns

### Performance Metrics
- Task completion time
- Speed improvement vs single-agent
- Error rate
- Retry rate

### Business Metrics
- User retention (7-day, 30-day)
- API cost per user
- Cost savings vs single-agent tools
- User satisfaction (NPS)

---

## Next Immediate Steps

### This Week
1. [ ] Set up project structure
2. [ ] Create basic REPL prototype
3. [ ] Test with simple task
4. [ ] Get feedback from 2-3 developers

### Next Week
1. [ ] Integrate with Meta-Agent
2. [ ] Add streaming output
3. [ ] Create configuration system
4. [ ] Write user guide

### Month 1
1. [ ] Complete MVP features
2. [ ] Internal testing
3. [ ] Fix critical bugs
4. [ ] Prepare for beta release

---

## Conclusion

**This is achievable!**

- You have 80% of the core tech already built
- Main work is the CLI interface layer
- 6 weeks to MVP is realistic
- Can validate market fit quickly with beta users

**Start small, iterate fast:**
1. Week 1: Basic REPL that works
2. Week 2: Can execute one simple task
3. Week 3: Streaming looks good
4. Week 4: Configuration works
5. Week 5: Polish UX
6. Week 6: Beta test

**Focus on the core value prop:**
- Faster than single-agent tools (show speed metrics)
- Easier than writing code (show before/after)
- Cheaper than always using premium models (show cost savings)

Good luck! 🚀
