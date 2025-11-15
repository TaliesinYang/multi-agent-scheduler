# Multi-Agent Scheduler - Gemini CLI Project Configuration

This configuration file overrides global Gemini CLI settings for this project.

## Project Context

This is an academic research project for **CSCI6650 - Advanced Topics in Operating Systems**. The Multi-Agent Scheduler is a Python-based system that decomposes complex tasks and distributes them across multiple AI agents (Claude, Codex, Gemini) for parallel execution.

## Response Language and Format

**IMPORTANT**: When working in this project:
- **Language**: Always respond in **English** (not Chinese)
- **Format**: Use standard markdown format, NOT three-stage workflow format
- **DO NOT** use Chinese section headers like `【分析问题】`, `【细化方案】`, `【执行方案】`

## MetaAgent Task Decomposition

When called by `MetaAgentCLI` for task decomposition:

### Critical Requirements
1. **ALWAYS return valid JSON format** - The system expects a JSON array of tasks
2. **DO NOT return explanatory text** - Only return the JSON structure
3. **DO NOT use conversational responses** - This breaks the parser

### Expected JSON Structure
```json
[
  {
    "task_id": "task1",
    "prompt": "Task description here",
    "depends_on": [],
    "priority": 1,
    "type": "coding|analysis|simple|general"
  },
  ...15-20 more tasks
]
```

### Task Decomposition Guidelines
- Break down the user task into **15-20 atomic subtasks**
- Each subtask should be independent and executable by a single agent
- Identify dependencies between tasks (use `depends_on` field)
- Assign appropriate priority (1=highest, higher numbers=lower priority)
- Classify task type for optimal agent selection

### Task Types
- `coding`: Code implementation tasks (best for Codex)
- `analysis`: System design and analysis (best for Claude)
- `simple`: Documentation, simple operations (best for Gemini)
- `general`: General-purpose tasks

## Code Generation

When generating code for this project:
- Follow Python asyncio patterns (the project is async-first)
- Use type hints for all function signatures
- Follow PEP 8 style guidelines
- Add docstrings for classes and functions
- Prefer pathlib over os.path for file operations

## Project File Structure

```
multi-agent-scheduler/
├── src/
│   ├── agents.py          # CLI agent implementations
│   ├── meta_agent.py      # Task decomposition (calls Gemini/Claude/Codex)
│   ├── scheduler.py       # Dependency-based task scheduler
│   ├── agent_selector.py  # Smart agent selection
│   └── agent_config.yaml  # Agent capabilities configuration
├── demos/                 # Example usage scripts
├── tests/                 # Test suite
└── workspaces/           # Agent execution workspaces
```

## Common Tasks

### Running the Scheduler
```bash
cd /mnt/e/BaiduNetdiskDownload/obsidian/VPL\ Leaning/FDUClasses/25VF_CSCI_6650_V1AdvTopicsOperatingSystems/Assignments/Group/multi-agent-scheduler
python3 demos/demo_cli_full.py
```

### Testing
```bash
pytest tests/ -v
```

## Notes

- This project uses CLI tools (`claude`, `codex`, `gemini`) as subprocess execution
- All agents run in isolated workspace directories
- Configuration is managed via `src/agent_config.yaml`
- Logs are stored in `logs/` directory with execution metrics
