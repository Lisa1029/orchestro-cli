#!/usr/bin/env python
"""Example: Parallel scenario execution.

Demonstrates running multiple scenarios in parallel using the worker pool.
"""

import asyncio
from pathlib import Path

from orchestro_cli.parallel import WorkerPool, WorkerPoolConfig, TaskQueue


async def main():
    """Run multiple scenarios in parallel."""
    # Configuration
    scenarios_dir = Path("examples/scenarios")
    num_workers = 4

    # Find all scenario files
    scenario_files = list(scenarios_dir.glob("*.yaml"))
    print(f"Found {len(scenario_files)} scenarios to execute")

    # Create worker pool
    config = WorkerPoolConfig(
        num_workers=num_workers,
        verbose=True,
        junit_xml_dir=Path("test-results")
    )
    pool = WorkerPool(config=config)

    # Submit all scenarios as tasks
    tasks = []
    for i, scenario_path in enumerate(scenario_files):
        # Higher priority for critical scenarios
        priority = 10 if "critical" in scenario_path.name else 5

        task = TaskQueue.create_task(
            scenario_path=scenario_path,
            priority=priority,
            workspace=Path(f"workspace_{i}"),  # Isolated workspaces
            test_suite="parallel_suite",
            run_id=i
        )
        tasks.append(task)

    await pool.submit_many(tasks)

    # Execute and wait for all tasks
    print(f"\nExecuting {len(tasks)} scenarios with {num_workers} workers...\n")
    results = await pool.wait_all(timeout=300)  # 5 minute timeout

    # Print results
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results if r.success)
    failure_count = len(results) - success_count

    print(f"Total Scenarios: {len(results)}")
    print(f"✅ Passed: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"Success Rate: {success_count / len(results) * 100:.1f}%")

    # Get pool statistics
    stats = pool.get_stats()
    print(f"\nExecution Time: {stats['execution']['elapsed_seconds']:.2f}s")
    print(f"Total Task Duration: {stats['performance']['total_task_duration']:.2f}s")
    print(f"Speedup: {stats['performance']['speedup']:.1f}x")

    # Print failed scenarios
    if failure_count > 0:
        print("\nFailed Scenarios:")
        for result in results:
            if not result.success:
                print(f"  - {result.scenario_path.name}: {result.error}")

    # Print per-worker statistics
    print("\nWorker Statistics:")
    for worker_stats in stats['workers']:
        print(f"  Worker {worker_stats['worker_id']}: "
              f"{worker_stats['tasks_completed']} completed, "
              f"{worker_stats['tasks_failed']} failed")

    return success_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
