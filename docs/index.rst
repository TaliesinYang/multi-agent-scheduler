Multi-Agent Scheduler Documentation
===================================

Welcome to Multi-Agent Scheduler's documentation!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   quickstart
   installation
   configuration
   api/modules
   deployment
   monitoring
   best_practices
   troubleshooting
   changelog

Introduction
============

The Multi-Agent Scheduler is an intelligent system for scheduling multiple AI agents with support for parallel/serial execution, task dependency analysis, and cost optimization.

Key Features
-----------

* **Atomic Task Decomposition**: AI automatically breaks tasks into atomic subtasks
* **Real-time Topology Visualization**: Live dependency graph with progress tracking
* **Workspace Isolation**: File operations in dedicated workspaces
* **Smart Scheduling**: Automatic task dependency analysis
* **Cost Optimization**: Intelligent agent selection based on task complexity
* **Performance Improvement**: 40-60% latency reduction through parallel execution
* **Checkpoint & Recovery**: Automatic state persistence and recovery
* **Distributed Tracing**: OpenTelemetry-compatible tracing
* **Human-in-the-Loop**: Approval workflows and feedback collection

Quick Start
===========

Installation
-----------

.. code-block:: bash

   pip install multi-agent-scheduler

Basic Usage
-----------

.. code-block:: python

   from multi_agent_scheduler import Scheduler, Task

   # Initialize scheduler
   scheduler = Scheduler()

   # Create tasks
   tasks = [
       Task("design", "Design database schema"),
       Task("implement", "Implement API", dependencies=["design"]),
       Task("test", "Write tests", dependencies=["implement"])
   ]

   # Execute
   result = await scheduler.execute_tasks(tasks)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
