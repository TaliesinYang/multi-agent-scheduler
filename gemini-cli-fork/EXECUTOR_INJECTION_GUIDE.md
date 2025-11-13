# AgentExecutor Injection Guide

**File to Modify**: `packages/core/src/agents/executor.ts`

This is the **only existing file** we need to modify to integrate our multi-agent scheduler.

---

## Step 1: Add Import at Top of File

**Location**: After existing imports (around line 54)

```typescript
// ============================================================
// MULTI-AGENT INTEGRATION: Add this import
// ============================================================
import { getScheduler, isMultiAgentScheduler } from '../schedulers/port.js';
// ============================================================
```

---

## Step 2: Modify the `execute()` Method

**Location**: Inside `AgentExecutor` class, find the `execute()` method (around line 250)

**Original code** looks like this:
```typescript
async execute(inputs: AgentInputs): Promise<OutputObject<TOutput>> {
  const history: Content[] = [];
  // ... rest of implementation
}
```

**Replace with**:

```typescript
async execute(inputs: AgentInputs): Promise<OutputObject<TOutput>> {
  // ============================================================
  // MULTI-AGENT INTEGRATION: Injection point
  // ============================================================

  // Get the configured scheduler
  const scheduler = await getScheduler(this.runtimeContext);

  // Log which scheduler is being used
  debugLogger.log(`[AgentExecutor] Using scheduler: ${scheduler.type}`);

  // Route to appropriate execution path
  if (isMultiAgentScheduler(scheduler)) {
    // ========== MULTI-AGENT PATH ==========
    debugLogger.log('[AgentExecutor] Taking multi-agent path');
    return await this.executeWithMultiAgent(scheduler, inputs);
  } else {
    // ========== DEFAULT PATH (Original Gemini logic) ==========
    debugLogger.log('[AgentExecutor] Taking default Gemini path');
    return await this.executeWithGemini(inputs);
  }
  // ============================================================
}
```

---

## Step 3: Add New Method: `executeWithMultiAgent()`

**Location**: After the `execute()` method (around line 350)

```typescript
/**
 * Execute using multi-agent scheduler
 *
 * This method handles the multi-agent execution flow:
 * 1. Decompose task using Meta Agent
 * 2. Show plan to user (via activity callback)
 * 3. Execute plan in parallel
 * 4. Format results
 *
 * ADDED FOR MULTI-AGENT INTEGRATION
 */
private async executeWithMultiAgent(
  scheduler: TaskSchedulerPort,
  inputs: AgentInputs,
): Promise<OutputObject<TOutput>> {
  const startTime = Date.now();

  try {
    // 1. Decompose task
    debugLogger.log('[AgentExecutor] Decomposing task with Meta Agent...');

    const taskDescription = this.buildTaskDescription(inputs);
    const plan = await scheduler.decompose(taskDescription, inputs.context);

    // 2. Notify UI about the plan (if callback provided)
    if (this.onActivity) {
      this.onActivity({
        type: 'plan_generated',
        agentId: this.agentId,
        data: {
          plan,
          taskCount: plan.tasks.length,
          estimatedTime: plan.estimatedTime,
          estimatedCost: plan.estimatedCost,
        },
      });
    }

    // 3. Execute the plan
    debugLogger.log('[AgentExecutor] Executing plan in parallel...');
    const results = await scheduler.execute(plan);

    // 4. Notify UI about completion
    if (this.onActivity) {
      this.onActivity({
        type: 'execution_complete',
        agentId: this.agentId,
        data: {
          results,
          successRate: results.successRate,
          totalTime: results.totalTime,
          totalCost: results.totalCost,
        },
      });
    }

    // 5. Format results into expected output format
    return this.formatMultiAgentResults(results, inputs);
  } catch (error) {
    debugLogger.error('[AgentExecutor] Multi-agent execution failed:', error);

    // Fallback to default Gemini on error
    debugLogger.log('[AgentExecutor] Falling back to default Gemini');
    return await this.executeWithGemini(inputs);
  }
}
```

---

## Step 4: Add New Method: `executeWithGemini()`

**Location**: After `executeWithMultiAgent()` (around line 400)

```typescript
/**
 * Execute using original Gemini logic
 *
 * This preserves the original behavior when multi-agent is disabled
 * or as a fallback when multi-agent fails.
 *
 * REFACTORED FOR MULTI-AGENT INTEGRATION
 * (This is the original execute() code)
 */
private async executeWithGemini(
  inputs: AgentInputs,
): Promise<OutputObject<TOutput>> {
  // ============================================================
  // ORIGINAL CODE (moved from execute() method)
  // ============================================================

  const history: Content[] = [];

  // ... (paste the ENTIRE original execute() method body here)
  // ... (this is 100+ lines of existing code)
  // ... (no changes needed, just moved into this method)

  // ============================================================
}
```

---

## Step 5: Add Helper Methods

**Location**: After `executeWithGemini()` (around line 550)

```typescript
/**
 * Build task description from inputs
 * ADDED FOR MULTI-AGENT INTEGRATION
 */
private buildTaskDescription(inputs: AgentInputs): string {
  // Extract the main task from inputs
  if (typeof inputs.task === 'string') {
    return inputs.task;
  }

  if (inputs.task?.description) {
    return inputs.task.description;
  }

  // Fallback: stringify inputs
  return JSON.stringify(inputs);
}

/**
 * Format multi-agent results into expected OutputObject format
 * ADDED FOR MULTI-AGENT INTEGRATION
 */
private formatMultiAgentResults(
  results: ExecutionResults,
  inputs: AgentInputs,
): OutputObject<TOutput> {
  // Combine all task results into single output
  const combinedOutput = results.results
    .map((r, i) => {
      const header = `\n${'='.repeat(60)}\nTask ${i + 1} [${r.agent.toUpperCase()}]: ${results.plan.tasks[i].description}\n${'='.repeat(60)}\n`;
      return header + r.result;
    })
    .join('\n\n');

  // Format into expected output structure
  const output: any = {
    output: combinedOutput,
    metadata: {
      scheduler: 'multi-agent',
      totalTasks: results.results.length,
      successfulTasks: results.successfulTasks,
      failedTasks: results.failedTasks,
      totalTime: results.totalTime,
      totalCost: results.totalCost,
      successRate: results.successRate,
      agentBreakdown: this.buildAgentBreakdown(results),
    },
  };

  return output;
}

/**
 * Build agent breakdown for metadata
 * ADDED FOR MULTI-AGENT INTEGRATION
 */
private buildAgentBreakdown(results: ExecutionResults): Record<string, any> {
  const breakdown: Record<string, any> = {};

  results.results.forEach((result) => {
    if (!breakdown[result.agent]) {
      breakdown[result.agent] = {
        count: 0,
        successful: 0,
        failed: 0,
        totalTime: 0,
        totalCost: 0,
      };
    }

    const stats = breakdown[result.agent];
    stats.count++;
    if (result.success) {
      stats.successful++;
    } else {
      stats.failed++;
    }
    stats.totalTime += result.latency;
    stats.totalCost += result.cost || 0;
  });

  return breakdown;
}
```

---

## Summary of Changes

### Lines Added
- **Imports**: ~2 lines
- **execute() modification**: ~15 lines
- **executeWithMultiAgent()**: ~50 lines
- **executeWithGemini()**: 0 new lines (refactored existing code)
- **Helper methods**: ~60 lines

**Total new code**: ~127 lines
**Total modified code**: ~15 lines (in existing execute() method)

### Files Modified
- `packages/core/src/agents/executor.ts` - **ONLY FILE MODIFIED**

### Architecture Impact
- ✅ Original code still works (in executeWithGemini)
- ✅ Multi-agent path is optional (controlled by config)
- ✅ Fallback mechanism (if multi-agent fails)
- ✅ Activity callbacks preserved (UI integration)

---

## Testing the Integration

After making these changes:

```bash
# 1. Build
npm run build

# 2. Test with default scheduler (should work exactly as before)
SCHEDULER_TYPE=default npm run start

# 3. Test with multi-agent scheduler (stub mode)
SCHEDULER_TYPE=multi-agent npm run start
```

---

## Generating the Patch

After confirming the changes work:

```bash
# Generate patch file
npx patch-package @google/gemini-cli-core

# This creates: patches/@google+gemini-cli-core+0.13.0.patch
# Future npm install will auto-apply this patch
```

---

## Upstream Sync Strategy

When Google updates Gemini CLI:

1. **Fetch upstream**:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

2. **If executor.ts has conflicts**:
   ```bash
   # Option A: Manually re-apply our changes
   # (use this guide as reference)

   # Option B: Use patch-package
   npm install  # Will attempt to apply patch
   # If patch fails, manually adjust and regenerate
   ```

3. **Verify tests pass**:
   ```bash
   npm run test
   npm run build
   ```

---

## Next Steps

After modifying executor.ts:

1. ✅ Verify the code compiles
2. ✅ Test default scheduler (should work as before)
3. ✅ Test multi-agent scheduler (stub mode)
4. 📝 Proceed to Phase 2: Implement Meta Agent and Scheduler
