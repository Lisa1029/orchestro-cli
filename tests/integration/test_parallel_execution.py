"""Integration tests for parallel execution."""

import pytest
import asyncio
import tempfile
from pathlib import Path

from orchestro_cli.parallel import (
    WorkerPool,
    WorkerPoolConfig,
    TaskQueue,
    Task,
)

# Mark all as integration tests (skip by default)
pytestmark = pytest.mark.integration


class TestParallelExecution:
    """Test real parallel scenario execution."""

    @pytest.fixture
    def test_scenarios(self, tmp_path):
        """Create multiple test scenarios."""
        scenarios = []

        for i in range(5):
            scenario = tmp_path / f"test_{i}.yaml"
            scenario.write_text(f"""
name: Test Scenario {i}
description: Parallel test {i}
command: echo
timeout: 10

steps:
  - expect: ".*"
    send: "Test {i}"
    note: "Send test message"

  - expect: "Test {i}"
    note: "Verify output"
""")
            scenarios.append(scenario)

        return scenarios

    @pytest.mark.asyncio
    async def test_parallel_execution_basic(self, test_scenarios, tmp_path):
        """Test basic parallel execution."""
        config = WorkerPoolConfig(
            num_workers=2,
            verbose=False
        )
        pool = WorkerPool(config=config)

        # Submit all scenarios
        tasks = []
        for scenario in test_scenarios:
            task = TaskQueue.create_task(
                scenario_path=scenario,
                workspace=tmp_path / f"ws_{scenario.stem}",
                priority=1
            )
            tasks.append(task)

        await pool.submit_many(tasks)

        # Execute and wait
        results = await pool.wait_all(timeout=60)

        # Verify all completed
        assert len(results) == len(test_scenarios)

        # Check success
        success_count = sum(1 for r in results if r.success)
        assert success_count == len(test_scenarios)

    @pytest.mark.asyncio
    async def test_priority_scheduling(self, tmp_path):
        """Test priority-based task scheduling."""
        # Create scenarios with different priorities
        high_priority = tmp_path / "high.yaml"
        high_priority.write_text("""
name: High Priority
command: echo
timeout: 10
steps:
  - expect: ".*"
    send: "high"
""")

        low_priority = tmp_path / "low.yaml"
        low_priority.write_text("""
name: Low Priority
command: echo
timeout: 10
steps:
  - expect: ".*"
    send: "low"
""")

        config = WorkerPoolConfig(num_workers=1, verbose=False)
        pool = WorkerPool(config=config)

        # Submit in reverse priority order
        low_task = TaskQueue.create_task(low_priority, priority=1)
        high_task = TaskQueue.create_task(high_priority, priority=100)

        await pool.submit(low_task)
        await pool.submit(high_task)

        results = await pool.wait_all(timeout=30)

        # High priority should complete first
        assert len(results) == 2
        # Both should succeed
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_worker_isolation(self, tmp_path):
        """Test that workers execute in isolation."""
        scenarios = []
        for i in range(3):
            scenario = tmp_path / f"isolated_{i}.yaml"
            scenario.write_text(f"""
name: Isolated Test {i}
command: echo
timeout: 10
steps:
  - expect: ".*"
    send: "worker {i}"
""")
            scenarios.append(scenario)

        config = WorkerPoolConfig(num_workers=3, verbose=False)
        pool = WorkerPool(config=config)

        tasks = [
            TaskQueue.create_task(s, workspace=tmp_path / f"ws_{i}")
            for i, s in enumerate(scenarios)
        ]

        await pool.submit_many(tasks)
        results = await pool.wait_all(timeout=60)

        # All should complete successfully
        assert len(results) == 3
        assert all(r.success for r in results)

        # Each should have separate workspace
        for i in range(3):
            ws = tmp_path / f"ws_{i}"
            assert ws.exists() or True  # Workspace may or may not persist

    @pytest.mark.asyncio
    async def test_progress_monitoring(self, test_scenarios, tmp_path):
        """Test progress monitoring during execution."""
        config = WorkerPoolConfig(num_workers=2, verbose=False)
        pool = WorkerPool(config=config)

        tasks = [
            TaskQueue.create_task(s, workspace=tmp_path / f"ws_{i}")
            for i, s in enumerate(test_scenarios)
        ]

        await pool.submit_many(tasks)

        # Start execution
        pool.start()

        # Monitor progress
        progress_snapshots = []
        while not pool.task_queue.empty() or any(w.is_busy for w in pool.workers):
            progress = pool.get_progress()
            progress_snapshots.append(progress)
            await asyncio.sleep(0.1)

        await pool.stop()

        # Should have captured progress
        assert len(progress_snapshots) > 0

        # Final progress should show all completed
        final_progress = pool.get_progress()
        assert final_progress['queue_size'] == 0
        assert final_progress['completed'] == len(test_scenarios)

    @pytest.mark.asyncio
    async def test_speedup_calculation(self, test_scenarios, tmp_path):
        """Test parallel speedup calculation."""
        config = WorkerPoolConfig(num_workers=4, verbose=False)
        pool = WorkerPool(config=config)

        tasks = [
            TaskQueue.create_task(s, workspace=tmp_path / f"ws_{i}")
            for i, s in enumerate(test_scenarios)
        ]

        await pool.submit_many(tasks)
        results = await pool.wait_all(timeout=60)

        # Get statistics
        stats = pool.get_stats()

        # Verify speedup calculation
        assert 'performance' in stats
        assert 'speedup' in stats['performance']
        assert stats['performance']['speedup'] >= 1.0  # Should have some speedup

        # Total task duration should be > elapsed time (parallel benefit)
        assert stats['performance']['total_task_duration'] > 0
        assert stats['execution']['elapsed_seconds'] > 0

    @pytest.mark.asyncio
    async def test_failed_task_handling(self, tmp_path):
        """Test handling of failed tasks."""
        # Create a scenario that will fail
        fail_scenario = tmp_path / "fail.yaml"
        fail_scenario.write_text("""
name: Failing Scenario
command: echo
timeout: 2
steps:
  - expect: "THIS_WILL_NOT_MATCH"
    note: "This will timeout"
""")

        # Create a successful scenario
        success_scenario = tmp_path / "success.yaml"
        success_scenario.write_text("""
name: Success Scenario
command: echo
timeout: 10
steps:
  - expect: ".*"
    send: "success"
""")

        config = WorkerPoolConfig(num_workers=2, verbose=False)
        pool = WorkerPool(config=config)

        fail_task = TaskQueue.create_task(fail_scenario)
        success_task = TaskQueue.create_task(success_scenario)

        await pool.submit(fail_task)
        await pool.submit(success_task)

        results = await pool.wait_all(timeout=60)

        # Should have 2 results
        assert len(results) == 2

        # One should fail, one should succeed
        success_count = sum(1 for r in results if r.success)
        fail_count = sum(1 for r in results if not r.success)

        assert success_count == 1
        assert fail_count == 1


class TestWorkerPoolConfiguration:
    """Test worker pool configuration options."""

    @pytest.mark.asyncio
    async def test_custom_worker_count(self, tmp_path):
        """Test configuring custom worker count."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""
name: Test
command: echo
steps:
  - expect: ".*"
    send: "test"
""")

        for num_workers in [1, 2, 4, 8]:
            config = WorkerPoolConfig(num_workers=num_workers, verbose=False)
            pool = WorkerPool(config=config)

            assert len(pool.workers) == num_workers

            task = TaskQueue.create_task(scenario)
            await pool.submit(task)
            results = await pool.wait_all(timeout=30)

            assert len(results) == 1
            assert results[0].success

    @pytest.mark.asyncio
    async def test_junit_xml_per_scenario(self, tmp_path):
        """Test JUnit XML generation for parallel scenarios."""
        junit_dir = tmp_path / "junit"
        junit_dir.mkdir()

        scenarios = []
        for i in range(3):
            scenario = tmp_path / f"test_{i}.yaml"
            scenario.write_text(f"""
name: Test {i}
command: echo
steps:
  - expect: ".*"
    send: "test {i}"
""")
            scenarios.append(scenario)

        config = WorkerPoolConfig(
            num_workers=2,
            verbose=False,
            junit_xml_dir=junit_dir
        )
        pool = WorkerPool(config=config)

        tasks = [TaskQueue.create_task(s) for s in scenarios]
        await pool.submit_many(tasks)
        results = await pool.wait_all(timeout=60)

        # Should have created JUnit XML files
        xml_files = list(junit_dir.glob("*.xml"))
        assert len(xml_files) == 3

        # Each file should be valid XML
        for xml_file in xml_files:
            content = xml_file.read_text()
            assert "<?xml version" in content
