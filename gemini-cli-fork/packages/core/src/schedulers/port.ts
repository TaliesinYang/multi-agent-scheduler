/**
 * @license
 * Copyright 2025 Multi-Agent Integration
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Task Scheduler Port Interface
 *
 * This is the abstraction layer that allows different scheduling implementations
 * to be plugged into Gemini CLI without modifying core logic.
 *
 * Implementations:
 * - DefaultScheduler: Wraps original Gemini CLI behavior
 * - MultiAgentScheduler: Uses Meta Agent + parallel execution
 */

import type { Config } from '../config/config.js';
import type { Content } from '@google/genai';

/**
 * Represents a single subtask in a decomposed task plan
 */
export interface Task {
  /** Unique identifier for this task */
  id: string;

  /** Human-readable description of what this task does */
  description: string;

  /** The agent assigned to execute this task */
  agent: 'claude' | 'openai' | 'gemini' | 'codex';

  /** The actual prompt to send to the agent */
  prompt: string;

  /** Optional context or additional data */
  context?: Record<string, any>;
}

/**
 * A complete task plan with dependencies
 */
export interface TaskPlan {
  /** List of all subtasks */
  tasks: Task[];

  /** Dependency graph: { taskId: [dependsOnTaskIds] } */
  dependencies: Record<string, string[]>;

  /** Estimated execution time in seconds */
  estimatedTime?: number;

  /** Estimated cost in USD */
  estimatedCost?: number;

  /** Original user task */
  originalTask: string;
}

/**
 * Result from executing a single task
 */
export interface TaskResult {
  /** The task that was executed */
  taskId: string;

  /** The agent that executed it */
  agent: string;

  /** The result/output from the agent */
  result: string;

  /** Whether execution was successful */
  success: boolean;

  /** Execution time in milliseconds */
  latency: number;

  /** Optional cost information */
  cost?: number;

  /** Optional error if failed */
  error?: string;

  /** Raw agent response (for debugging) */
  rawResponse?: any;
}

/**
 * Execution results for the entire task plan
 */
export interface ExecutionResults {
  /** Individual task results */
  results: TaskResult[];

  /** Total execution time */
  totalTime: number;

  /** Total cost */
  totalCost: number;

  /** Success rate */
  successRate: number;

  /** Number of successful tasks */
  successfulTasks: number;

  /** Number of failed tasks */
  failedTasks: number;

  /** Original task plan */
  plan: TaskPlan;
}

/**
 * Port interface for task scheduling implementations
 *
 * This interface defines the contract that all schedulers must implement.
 * It follows the Port-Adapter pattern to allow clean separation between
 * Gemini CLI's core logic and our multi-agent scheduling logic.
 */
export interface TaskSchedulerPort {
  /**
   * Decompose a high-level task into subtasks
   *
   * @param task - The user's task description
   * @param context - Optional context (conversation history, files, etc.)
   * @returns A complete task plan with subtasks and dependencies
   */
  decompose(task: string, context?: Content[]): Promise<TaskPlan>;

  /**
   * Execute a task plan
   *
   * @param plan - The task plan to execute
   * @returns Execution results for all tasks
   */
  execute(plan: TaskPlan): Promise<ExecutionResults>;

  /**
   * One-shot: Decompose and execute in one call
   *
   * This is a convenience method that combines decompose() and execute().
   * Most users will call this instead of the individual methods.
   *
   * @param task - The user's task description
   * @param context - Optional context
   * @returns Complete execution results
   */
  run(task: string, context?: Content[]): Promise<ExecutionResults>;

  /**
   * Get the type of this scheduler
   *
   * Used for conditional logic in AgentExecutor to determine
   * which code path to take.
   */
  readonly type: 'default' | 'multi-agent';

  /**
   * Get human-readable name for logging
   */
  readonly name: string;
}

/**
 * Factory function to get the appropriate scheduler based on configuration
 *
 * This is the main entry point used by AgentExecutor.
 *
 * @param config - Runtime configuration
 * @returns The configured scheduler instance
 */
export function getScheduler(config: Config): TaskSchedulerPort {
  const schedulerType = config.getSchedulerType();

  if (schedulerType === 'multi-agent') {
    // Lazy import to avoid circular dependencies
    const { MultiAgentScheduler } = await import('./multi-agent-scheduler.js');
    return new MultiAgentScheduler(config);
  } else {
    // Default to original Gemini behavior
    const { DefaultScheduler } = await import('./default-scheduler.js');
    return new DefaultScheduler(config);
  }
}

/**
 * Helper: Check if a scheduler is multi-agent
 */
export function isMultiAgentScheduler(
  scheduler: TaskSchedulerPort,
): scheduler is TaskSchedulerPort & { type: 'multi-agent' } {
  return scheduler.type === 'multi-agent';
}

/**
 * Helper: Format execution results for display
 */
export function formatExecutionSummary(results: ExecutionResults): string {
  const { successfulTasks, failedTasks, totalTime, totalCost } = results;
  const totalTasks = successfulTasks + failedTasks;

  return `
📊 Execution Summary:
  ✅ Successful: ${successfulTasks}/${totalTasks}
  ❌ Failed: ${failedTasks}/${totalTasks}
  ⏱️  Total Time: ${(totalTime / 1000).toFixed(2)}s
  💰 Total Cost: $${totalCost.toFixed(4)}
`;
}

/**
 * Helper: Format task plan for display
 */
export function formatTaskPlan(plan: TaskPlan): string {
  const lines = ['📋 Task Plan:', ''];

  plan.tasks.forEach((task, index) => {
    const deps = plan.dependencies[task.id] || [];
    const depsStr = deps.length > 0 ? ` (depends on: ${deps.join(', ')})` : '';

    lines.push(
      `  ${index + 1}. [${task.agent}] ${task.description}${depsStr}`,
    );
  });

  if (plan.estimatedTime) {
    lines.push('');
    lines.push(`  ⏱️  Estimated time: ${plan.estimatedTime.toFixed(1)}s`);
  }

  if (plan.estimatedCost) {
    lines.push(`  💰 Estimated cost: $${plan.estimatedCost.toFixed(4)}`);
  }

  return lines.join('\n');
}
