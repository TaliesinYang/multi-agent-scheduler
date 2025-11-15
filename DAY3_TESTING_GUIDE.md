# Day 3 Testing Guide

## 🎯 Day 3 Checkpoint: Multi-Round Dialogue Execution

**Status**: Implementation Complete ✓
**Next Step**: Run validation tests to verify >80% success rate

---

## What Was Implemented

### 1. MultiRoundExecutor (`src/orchestration/multi_round_executor.py`)
- Agent-tool interaction loop (up to 20 rounds)
- Anthropic message format compliance
- FINAL_ANSWER detection for task completion
- Batch execution and statistics calculation

### 2. Test Infrastructure
- Full test suite with 5 tasks (3 OS + 2 DB)
- SQLite support for easy testing (no MySQL required)
- Quick test for rapid validation
- Detailed performance reporting

---

## Prerequisites

### Required
- **Docker**: Must be running (for OS task execution)
  ```bash
  # Check Docker is running
  docker ps

  # If not, start Docker daemon
  # macOS/Windows: Start Docker Desktop
  # Linux: sudo systemctl start docker
  ```

- **Anthropic API Key**: Set in environment
  ```bash
  export ANTHROPIC_API_KEY="your-api-key-here"
  ```

### Optional
- **MySQL**: Only if testing with `--db mysql` (SQLite is default)

---

## Running Tests

### Option 1: Quick Test (Recommended First)
**Time**: ~30 seconds
**Purpose**: Verify basic functionality

```bash
python3 quick_test_multi_round.py
```

**What it tests**:
- Single OS task: List files in /root
- Agent-tool interaction
- FINAL_ANSWER detection

**Expected output**:
```
✅ Test PASSED
   - Completed in 2 rounds
   - Made 2 tool calls
   - Final answer: .bashrc .profile ...
```

---

### Option 2: Simple Mode (1 Task)
**Time**: ~30 seconds
**Purpose**: Test with simple mode flag

```bash
python3 test_multi_round.py --mode simple
```

---

### Option 3: Full Validation (5 Tasks) 🎯
**Time**: ~2-3 minutes
**Purpose**: Day 3 checkpoint validation

```bash
python3 test_multi_round.py --mode full
```

**What it tests**:
- 3 OS tasks: ls, file existence check, whoami
- 2 DB tasks: list tables, count users
- Uses SQLite by default (auto-creates test database)

**Success criteria**:
- ✅ Success rate > 80% (at least 4/5 tasks)
- ✅ Average rounds < 5
- ✅ No tasks hitting max rounds

**Expected output**:
```
================================================================================
VALIDATION CRITERIA
================================================================================
  ✓ Success rate > 80%: 100.0%
  ✓ Avg rounds < 5: 2.4
  ✓ No tasks hit max rounds: 0 tasks

================================================================================
✅ DAY 3 VALIDATION: PASSED
Multi-round dialogue execution is working correctly!
================================================================================
```

---

### Option 4: Full Validation with MySQL
If you have MySQL running:

```bash
python3 test_multi_round.py --mode full --db mysql
```

**Note**: Update MySQL credentials in test_multi_round.py line 137-139 first.

---

## Troubleshooting

### Error: "Failed to connect to Docker"
```bash
# Start Docker daemon
# macOS/Windows: Open Docker Desktop
# Linux:
sudo systemctl start docker

# Verify Docker is running
docker ps
```

### Error: "ANTHROPIC_API_KEY not found"
```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### Error: "Container failed to start"
```bash
# Pull Ubuntu image manually
docker pull ubuntu:22.04

# Check disk space
docker system df
```

### Error: "Module not found: anthropic"
```bash
# Install dependencies
pip install anthropic
# or
pip install -r requirements.txt
```

### SQLite database locked
```bash
# Remove old database file
rm test_agentbench.db

# Run test again
python3 test_multi_round.py --mode full
```

---

## Understanding Test Output

### Per-Task Results
```
✓ os_1: 2 rounds, 2 tool calls     # Success
✗ os_2: 5 rounds, 6 tool calls     # Failed
  Answer: Task incomplete - ...
```

### Statistics
```
Overall Performance:
  Total tasks: 5
  Successful: 4
  Failed: 1
  Success rate: 80.0%        # Must be > 80%
  Avg rounds: 2.8            # Must be < 5
  Avg tool calls: 3.4
```

### OS vs DB Performance
```
OS Tasks Performance:
  Success rate: 100.0% (3/3)

DB Tasks Performance:
  Success rate: 50.0% (1/2)  # One DB task failed
```

---

## Next Steps

### If Tests Pass (Success Rate > 80%)
✅ Day 3 checkpoint complete!

**Proceed to Day 4**:
- Implement DAG scheduler (topological sort, parallel execution)
- See `HYBRID_ARCHITECTURE_PLAN.md` Day 4 section

### If Tests Fail (Success Rate < 80%)
⚠️ Debug before continuing

**Common issues**:
1. **Tool not called**: Agent didn't use tools
   - Check tool definitions in `AGENTBENCH_TOOLS`
   - Verify prompt clarity

2. **Timeout**: Task exceeded max rounds
   - Check Docker/DB connectivity
   - Increase max_rounds if needed

3. **Wrong answer**: Agent gave incorrect result
   - Review conversation history in output
   - Check tool execution results

**How to debug**:
```bash
# Run with verbose output (already enabled by default)
python3 quick_test_multi_round.py

# Check conversation history in failed tasks
# Look for the "message_history" field in results
```

---

## Files Created in Day 3

```
src/orchestration/
├── __init__.py                    # Package init
└── multi_round_executor.py        # Multi-round executor (260 lines)

tests/
├── test_multi_round.py            # Full validation (5 tasks)
└── quick_test_multi_round.py      # Quick test (1 task)

docs/
└── DAY3_TESTING_GUIDE.md          # This file
```

---

## Test Database Schema (SQLite)

Auto-created by test script:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT
);

-- Sample data (5 records)
INSERT INTO users VALUES
    (1, 'Alice', 25, 'alice@example.com'),
    (2, 'Bob', 30, 'bob@example.com'),
    (3, 'Charlie', 22, 'charlie@example.com'),
    (4, 'David', 35, 'david@example.com'),
    (5, 'Eve', 28, 'eve@example.com');
```

---

## Questions?

- Check `HYBRID_ARCHITECTURE_PLAN.md` for overall roadmap
- Review `src/orchestration/multi_round_executor.py` for implementation details
- See commit history for changes: `git log --oneline`

---

**Last Updated**: Day 3 Implementation (Commits: 2f5f13b, 94b446d, ef61a75)
