#!/usr/bin/env python
"""Demonstration of parallel scenario execution."""

import asyncio
from pathlib import Path

from orchestro_cli.parallel import WorkerPool, WorkerPoolConfig, TaskQueue


async def main():
    """Run multiple scenarios in parallel."""
    print("🚀 Orchestro CLI - Parallel Execution Demo\n")
    print("="*60)

    # Create 3 simple scenarios
    scenarios = []
    for i in range(3):
        scenario_path = Path(f"demo_test_{i}.yaml")
        scenario_path.write_text(f"""name: Parallel Test {i}
command: cat
timeout: 10

steps:
  - send: "Test {i} - Line 1"
  - expect: "Test {i} - Line 1"
  - send: "Test {i} - Line 2"
  - expect: "Test {i} - Line 2"
  - control: "d"

validations: []
""")
        scenarios.append(scenario_path)

    # Create worker pool with 2 workers
    config = WorkerPoolConfig(
        num_workers=2,
        verbose=True
    )
    pool = WorkerPool(config=config)

    # Submit all scenarios
    print(f"\n📋 Submitting {len(scenarios)} scenarios to worker pool...\n")
    for scenario in scenarios:
        task = TaskQueue.create_task(scenario, priority=1)
        await pool.submit(task)

    # Execute and wait
    print("⚙️  Executing scenarios in parallel...\n")
    results = await pool.wait_all(timeout=60)

    # Print results
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)

    success_count = sum(1 for r in results if r.success)
    print(f"Total Scenarios: {len(results)}")
    print(f"✅ Passed: {success_count}")
    print(f"❌ Failed: {len(results) - success_count}")
    print(f"Success Rate: {success_count / len(results) * 100:.0f}%")

    # Get statistics
    stats = pool.get_stats()
    print(f"\n⏱️  Execution Time: {stats['execution']['elapsed_seconds']:.2f}s")
    print(f"📈 Total Task Duration: {stats['performance']['total_task_duration']:.2f}s")
    print(f"🚀 Speedup: {stats['performance']['speedup']:.1f}x")

    # Worker statistics
    print(f"\n👷 Worker Statistics:")
    for worker_stats in stats['workers']:
        print(f"  Worker {worker_stats['worker_id']}: "
              f"{worker_stats['tasks_completed']} completed")

    # Cleanup
    for scenario in scenarios:
        scenario.unlink()

    return success_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
