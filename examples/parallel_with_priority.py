#!/usr/bin/env python
"""Example: Priority-based parallel execution.

Demonstrates priority-based task scheduling in the worker pool.
"""

import asyncio
from pathlib import Path

from orchestro_cli.parallel import WorkerPool, WorkerPoolConfig, TaskQueue


async def main():
    """Run scenarios with priority-based scheduling."""
    scenarios_dir = Path("examples/scenarios")

    # Create worker pool
    config = WorkerPoolConfig(num_workers=2, verbose=True)
    pool = WorkerPool(config=config)

    # Define scenario priorities
    priority_map = {
        "critical": 100,   # Run first
        "high": 50,        # Run second
        "medium": 10,      # Run third
        "low": 1,          # Run last
    }

    # Submit scenarios with priorities
    tasks = []
    for scenario_file in scenarios_dir.glob("*.yaml"):
        # Determine priority from filename
        priority = 5  # default
        for key, value in priority_map.items():
            if key in scenario_file.name:
                priority = value
                break

        task = TaskQueue.create_task(
            scenario_path=scenario_file,
            priority=priority,
            priority_level=key if key in scenario_file.name else "default"
        )
        tasks.append(task)

    await pool.submit_many(tasks)

    # Monitor progress
    pool.start()

    while not pool.task_queue.empty() or any(w.is_busy for w in pool.workers):
        progress = pool.get_progress()
        print(f"\r[Queue: {progress['queue_size']}, "
              f"Completed: {progress['completed']}, "
              f"Failed: {progress['failed']}]", end="", flush=True)
        await asyncio.sleep(0.5)

    await pool.stop()
    print("\n\nAll scenarios completed!")

    # Print execution order (by result order)
    results = pool.task_queue.get_all_results()
    print("\nExecution Order (by completion):")
    for i, result in enumerate(results, 1):
        priority_level = result.metadata.get("priority_level", "default")
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{i}. [{priority_level.upper():8}] "
              f"{result.scenario_path.name:30} {status}")


if __name__ == "__main__":
    asyncio.run(main())
