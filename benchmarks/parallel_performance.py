#!/usr/bin/env python
"""Performance benchmarks for parallel execution."""

import asyncio
import time
from pathlib import Path
from typing import List
import statistics

from orchestro_cli.parallel import WorkerPool, WorkerPoolConfig, TaskQueue


class ParallelBenchmark:
    """Benchmark suite for parallel execution performance."""

    def __init__(self, output_dir: Path):
        """Initialize benchmark.

        Args:
            output_dir: Directory for benchmark results
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def create_test_scenarios(self, count: int, complexity: str = "simple") -> List[Path]:
        """Create test scenarios.

        Args:
            count: Number of scenarios to create
            complexity: "simple", "medium", or "complex"

        Returns:
            List of scenario paths
        """
        scenarios = []

        for i in range(count):
            scenario_path = self.output_dir / f"bench_{complexity}_{i}.yaml"

            if complexity == "simple":
                content = f"""name: Simple Bench {i}
command: echo
timeout: 5
steps:
  - send: "Line 1"
  - expect: "Line 1"
validations: []
"""
            elif complexity == "medium":
                content = f"""name: Medium Bench {i}
command: cat
timeout: 10
steps:
  - send: "Line 1"
  - expect: "Line 1"
  - send: "Line 2"
  - expect: "Line 2"
  - send: "Line 3"
  - expect: "Line 3"
  - control: "d"
validations: []
"""
            else:  # complex
                content = f"""name: Complex Bench {i}
command: cat
timeout: 15
steps:
  - send: "Line 1"
  - expect: "Line 1"
  - send: "Line 2"
  - expect: "Line 2"
  - send: "Line 3"
  - expect: "Line 3"
  - send: "Line 4"
  - expect: "Line 4"
  - send: "Line 5"
  - expect: "Line 5"
  - control: "d"
validations: []
"""

            scenario_path.write_text(content)
            scenarios.append(scenario_path)

        return scenarios

    async def benchmark_worker_count(
        self,
        scenarios: List[Path],
        worker_counts: List[int]
    ) -> dict:
        """Benchmark different worker counts.

        Args:
            scenarios: Scenarios to execute
            worker_counts: List of worker counts to test

        Returns:
            Dict with benchmark results
        """
        results = {}

        for num_workers in worker_counts:
            config = WorkerPoolConfig(
                num_workers=num_workers,
                verbose=False
            )
            pool = WorkerPool(config=config)

            # Submit all scenarios
            for scenario in scenarios:
                task = TaskQueue.create_task(scenario, priority=1)
                await pool.submit(task)

            # Execute and measure
            start_time = time.time()
            task_results = await pool.wait_all(timeout=120)
            elapsed = time.time() - start_time

            # Calculate stats
            stats = pool.get_stats()

            results[num_workers] = {
                "elapsed_seconds": elapsed,
                "total_scenarios": len(scenarios),
                "completed": sum(1 for r in task_results if r.success),
                "failed": sum(1 for r in task_results if not r.success),
                "speedup": stats["performance"]["speedup"],
                "throughput": len(scenarios) / elapsed if elapsed > 0 else 0,
            }

            print(f"Workers={num_workers}: {elapsed:.2f}s, "
                  f"Speedup={results[num_workers]['speedup']:.2f}x")

        return results

    async def benchmark_scenario_complexity(self) -> dict:
        """Benchmark different scenario complexities.

        Returns:
            Dict with complexity benchmark results
        """
        complexities = ["simple", "medium", "complex"]
        results = {}

        for complexity in complexities:
            scenarios = self.create_test_scenarios(count=10, complexity=complexity)

            config = WorkerPoolConfig(num_workers=4, verbose=False)
            pool = WorkerPool(config=config)

            for scenario in scenarios:
                task = TaskQueue.create_task(scenario, priority=1)
                await pool.submit(task)

            start_time = time.time()
            task_results = await pool.wait_all(timeout=120)
            elapsed = time.time() - start_time

            # Calculate per-scenario timing
            durations = [r.duration for r in task_results]

            results[complexity] = {
                "total_time": elapsed,
                "avg_scenario_duration": statistics.mean(durations),
                "median_scenario_duration": statistics.median(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "scenarios_completed": len(task_results),
            }

            # Cleanup
            for scenario in scenarios:
                scenario.unlink()

            print(f"Complexity={complexity}: {elapsed:.2f}s, "
                  f"Avg={results[complexity]['avg_scenario_duration']:.2f}s")

        return results

    async def benchmark_priority_scheduling(self) -> dict:
        """Benchmark priority-based scheduling.

        Returns:
            Dict with priority benchmark results
        """
        # Create scenarios with different priorities
        scenarios_high = self.create_test_scenarios(count=5, complexity="simple")
        scenarios_low = self.create_test_scenarios(count=5, complexity="simple")

        config = WorkerPoolConfig(num_workers=2, verbose=False)
        pool = WorkerPool(config=config)

        # Submit high priority first, low priority second
        for scenario in scenarios_high:
            task = TaskQueue.create_task(scenario, priority=10)  # High
            await pool.submit(task)

        for scenario in scenarios_low:
            task = TaskQueue.create_task(scenario, priority=1)   # Low
            await pool.submit(task)

        # Track execution order
        start_time = time.time()
        results_list = await pool.wait_all(timeout=60)
        elapsed = time.time() - start_time

        # Analyze if high priority executed first
        high_priority_avg = statistics.mean([
            r.end_time.timestamp() for r in results_list[:5]
        ])
        low_priority_avg = statistics.mean([
            r.end_time.timestamp() for r in results_list[5:]
        ])

        # Cleanup - check if files still exist
        for scenario in scenarios_high + scenarios_low:
            if scenario.exists():
                scenario.unlink()

        return {
            "total_time": elapsed,
            "high_priority_first": high_priority_avg < low_priority_avg,
            "time_difference": abs(high_priority_avg - low_priority_avg),
        }

    async def benchmark_scalability(self) -> dict:
        """Test scalability with increasing load.

        Returns:
            Dict with scalability results
        """
        scenario_counts = [5, 10, 20, 40]
        results = {}

        for count in scenario_counts:
            scenarios = self.create_test_scenarios(count=count, complexity="simple")

            config = WorkerPoolConfig(num_workers=4, verbose=False)
            pool = WorkerPool(config=config)

            for scenario in scenarios:
                task = TaskQueue.create_task(scenario, priority=1)
                await pool.submit(task)

            start_time = time.time()
            await pool.wait_all(timeout=180)
            elapsed = time.time() - start_time

            results[count] = {
                "elapsed_seconds": elapsed,
                "throughput": count / elapsed if elapsed > 0 else 0,
                "time_per_scenario": elapsed / count if count > 0 else 0,
            }

            # Cleanup
            for scenario in scenarios:
                scenario.unlink()

            print(f"Scenarios={count}: {elapsed:.2f}s, "
                  f"Throughput={results[count]['throughput']:.2f} scenarios/s")

        return results

    def generate_report(self, results: dict) -> None:
        """Generate benchmark report.

        Args:
            results: Benchmark results dictionary
        """
        report_path = self.output_dir / "benchmark_report.md"

        report = f"""# Parallel Execution Performance Benchmark

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Worker Count Benchmark

Tests parallel speedup with different worker counts.

| Workers | Time (s) | Speedup | Throughput (scenarios/s) |
|---------|----------|---------|--------------------------|
"""

        if "worker_count" in results:
            for workers, data in results["worker_count"].items():
                report += f"| {workers} | {data['elapsed_seconds']:.2f} | "
                report += f"{data['speedup']:.2f}x | {data['throughput']:.2f} |\n"

        report += "\n## Scenario Complexity Benchmark\n\n"
        report += "Tests execution time for different scenario complexities.\n\n"
        report += "| Complexity | Total Time (s) | Avg Duration (s) | Median (s) |\n"
        report += "|------------|----------------|------------------|------------|\n"

        if "complexity" in results:
            for complexity, data in results["complexity"].items():
                report += f"| {complexity} | {data['total_time']:.2f} | "
                report += f"{data['avg_scenario_duration']:.2f} | "
                report += f"{data['median_scenario_duration']:.2f} |\n"

        report += "\n## Scalability Benchmark\n\n"
        report += "Tests performance with increasing scenario count.\n\n"
        report += "| Scenarios | Time (s) | Throughput | Time/Scenario (s) |\n"
        report += "|-----------|----------|------------|-------------------|\n"

        if "scalability" in results:
            for count, data in results["scalability"].items():
                report += f"| {count} | {data['elapsed_seconds']:.2f} | "
                report += f"{data['throughput']:.2f}/s | "
                report += f"{data['time_per_scenario']:.2f} |\n"

        report += "\n## Priority Scheduling Benchmark\n\n"

        if "priority" in results:
            data = results["priority"]
            report += f"- **Total Time**: {data['total_time']:.2f}s\n"
            report += f"- **High Priority First**: {data['high_priority_first']}\n"
            report += f"- **Time Difference**: {data['time_difference']:.2f}s\n"

        report += "\n---\n\n*Benchmark complete*\n"

        report_path.write_text(report)
        print(f"\n📊 Benchmark report written to: {report_path}")


async def main():
    """Run all benchmarks."""
    print("🚀 Orchestro CLI - Parallel Execution Benchmarks\n")
    print("=" * 60)

    bench = ParallelBenchmark(output_dir=Path("benchmark_results"))
    all_results = {}

    # 1. Worker count benchmark
    print("\n1️⃣  Benchmarking worker counts...")
    scenarios = bench.create_test_scenarios(count=20, complexity="medium")
    all_results["worker_count"] = await bench.benchmark_worker_count(
        scenarios=scenarios,
        worker_counts=[1, 2, 4, 8]
    )
    for scenario in scenarios:
        scenario.unlink()

    # 2. Complexity benchmark
    print("\n2️⃣  Benchmarking scenario complexity...")
    all_results["complexity"] = await bench.benchmark_scenario_complexity()

    # 3. Priority benchmark
    print("\n3️⃣  Benchmarking priority scheduling...")
    all_results["priority"] = await bench.benchmark_priority_scheduling()

    # 4. Scalability benchmark
    print("\n4️⃣  Benchmarking scalability...")
    all_results["scalability"] = await bench.benchmark_scalability()

    # Generate report
    print("\n5️⃣  Generating report...")
    bench.generate_report(all_results)

    print("\n" + "=" * 60)
    print("✅ All benchmarks complete!")


if __name__ == "__main__":
    asyncio.run(main())
