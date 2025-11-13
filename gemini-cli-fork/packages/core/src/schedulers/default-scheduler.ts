/**
 * @license
 * Copyright 2025 Multi-Agent Integration
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Default Scheduler
 *
 * This scheduler preserves the original Gemini CLI behavior.
 * It's used as a fallback when multi-agent mode is disabled,
 * and serves as a baseline for performance comparison.
 *
 * Behavior:
 * - No task decomposition (treats entire input as single task)
 * - Uses Gemini as the only agent
 * - Sequential execution (no parallelization)
 * - Wraps existing GeminiChat functionality
 */

import type { Config } from '../config/config.js';
import type { Content } from '@google/genai';
import type {
  TaskSchedulerPort,
  Task,
  TaskPlan,
  TaskResult,
  ExecutionResults,
} from './port.js';
import { GeminiChat } from '../core/geminiChat.js';
import { debugLogger } from '../utils/debugLogger.js';

export class DefaultScheduler implements TaskSchedulerPort {
  readonly type = 'default' as const;
  readonly name = 'Default Gemini Scheduler';

  private geminiChat: GeminiChat;

  constructor(private config: Config) {
    this.geminiChat = new GeminiChat(config);
    debugLogger.log('[DefaultScheduler] Initialized');
  }

  /**
   * Decompose task - No actual decomposition, just wrap as single task
   */
  async decompose(task: string, context?: Content[]): Promise<TaskPlan> {
    debugLogger.log('[DefaultScheduler] decompose() called (no-op)');

    // No decomposition - entire task goes to Gemini as single unit
    const singleTask: Task = {
      id: 'task-1',
      description: task,
      agent: 'gemini',
      prompt: task,
      context: context ? { history: context } : undefined,
    };

    return {
      tasks: [singleTask],
      dependencies: {},
      originalTask: task,
      estimatedTime: undefined, // Unknown
      estimatedCost: undefined, // Unknown
    };
  }

  /**
   * Execute task plan - Use original Gemini chat
   */
  async execute(plan: TaskPlan): Promise<ExecutionResults> {
    debugLogger.log('[DefaultScheduler] execute() called');

    if (plan.tasks.length !== 1) {
      throw new Error(
        'DefaultScheduler can only handle single-task plans',
      );
    }

    const task = plan.tasks[0];
    const startTime = Date.now();

    try {
      // Use original Gemini chat logic
      const response = await this.geminiChat.send({
        message: task.prompt,
        context: task.context?.history,
      });

      const endTime = Date.now();
      const latency = endTime - startTime;

      const result: TaskResult = {
        taskId: task.id,
        agent: 'gemini',
        result: this.extractTextFromResponse(response),
        success: true,
        latency: latency,
        cost: this.estimateCost(response),
        rawResponse: response,
      };

      return {
        results: [result],
        totalTime: latency,
        totalCost: result.cost || 0,
        successRate: 1.0,
        successfulTasks: 1,
        failedTasks: 0,
        plan: plan,
      };
    } catch (error) {
      const endTime = Date.now();
      const latency = endTime - startTime;

      const result: TaskResult = {
        taskId: task.id,
        agent: 'gemini',
        result: '',
        success: false,
        latency: latency,
        error: error instanceof Error ? error.message : String(error),
      };

      return {
        results: [result],
        totalTime: latency,
        totalCost: 0,
        successRate: 0.0,
        successfulTasks: 0,
        failedTasks: 1,
        plan: plan,
      };
    }
  }

  /**
   * Run: Decompose and execute in one call
   */
  async run(task: string, context?: Content[]): Promise<ExecutionResults> {
    debugLogger.log('[DefaultScheduler] run() called');

    const plan = await this.decompose(task, context);
    return await this.execute(plan);
  }

  /**
   * Extract text from Gemini response
   */
  private extractTextFromResponse(response: any): string {
    // Handle different response formats
    if (typeof response === 'string') {
      return response;
    }

    if (response.text) {
      return response.text;
    }

    if (response.candidates?.[0]?.content?.parts?.[0]?.text) {
      return response.candidates[0].content.parts[0].text;
    }

    // Fallback: stringify the response
    return JSON.stringify(response);
  }

  /**
   * Estimate cost based on response
   *
   * This is a rough estimation based on typical Gemini pricing.
   * Actual cost tracking would require usage metadata from the API.
   */
  private estimateCost(response: any): number {
    // Rough estimation: $0.0001 per 1K input tokens, $0.0003 per 1K output tokens
    // This is very approximate without actual token counts

    const outputText = this.extractTextFromResponse(response);
    const estimatedOutputTokens = outputText.length / 4; // Rough approximation

    // Assume similar input size
    const estimatedInputTokens = estimatedOutputTokens;

    const inputCost = (estimatedInputTokens / 1000) * 0.0001;
    const outputCost = (estimatedOutputTokens / 1000) * 0.0003;

    return inputCost + outputCost;
  }
}
