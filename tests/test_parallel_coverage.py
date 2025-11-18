"""Additional tests to increase parallel execution coverage."""

import asyncio
from pathlib import Path
from datetime import datetime
import pytest

from orchestro_cli.parallel import (
    WorkerPool,
    WorkerPoolConfig,
    TaskQueue,
    Task,
    TaskResult,
    TaskStatus,
    Worker,
    WorkerStatus,
)


class TestWorkerPoolCoverage:
    """Increase coverage for WorkerPool."""

    @pytest.mark.asyncio
    async def test_worker_pool_progress(self, tmp_path):
        """Test progress tracking during execution."""
        # Create test scenario
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: echo
timeout: 5
steps:
  - send: "test"
validations: []
""")

        config = WorkerPoolConfig(num_workers=2, verbose=False)
        pool = WorkerPool(config=config)

        # Submit task
        task = TaskQueue.create_task(scenario, priority=1)
        await pool.submit(task)

        # Start pool
        pool.start()

        # Check progress while running
        progress = pool.get_progress()
        assert progress["running"] is True
        assert progress["queue_size"] >= 0

        # Wait for completion
        await pool.wait_all()

        # Check final progress
        final_progress = pool.get_progress()
        assert final_progress["running"] is False
        assert final_progress["total_results"] == 1

    @pytest.mark.asyncio
    async def test_worker_pool_stats(self, tmp_path):
        """Test comprehensive statistics."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: echo
timeout: 5
steps:
  - send: "test"
validations: []
""")

        config = WorkerPoolConfig(num_workers=1, verbose=True)
        pool = WorkerPool(config=config)

        task = TaskQueue.create_task(scenario, priority=1)
        await pool.submit(task)

        # Execute
        results = await pool.wait_all()

        # Get stats
        stats = pool.get_stats()

        assert stats["config"]["num_workers"] == 1
        assert stats["results"]["total"] == 1
        assert "speedup" in stats["performance"]
        assert "workers" in stats
        assert len(stats["workers"]) == 1

    @pytest.mark.asyncio
    async def test_submit_many(self, tmp_path):
        """Test submitting multiple tasks at once."""
        tasks = []
        for i in range(3):
            scenario = tmp_path / f"test_{i}.yaml"
            scenario.write_text(f"""name: Test {i}
command: echo
timeout: 5
steps:
  - send: "test{i}"
validations: []
""")
            task = TaskQueue.create_task(scenario, priority=i)
            tasks.append(task)

        config = WorkerPoolConfig(num_workers=2, verbose=False)
        pool = WorkerPool(config=config)

        # Submit all at once
        await pool.submit_many(tasks)

        results = await pool.wait_all()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_double_start(self, tmp_path):
        """Test calling start() multiple times (should be idempotent)."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: echo
timeout: 5
steps:
  - send: "test"
validations: []
""")

        config = WorkerPoolConfig(num_workers=1, verbose=False)
        pool = WorkerPool(config=config)

        # Start twice
        pool.start()
        pool.start()  # Should not create duplicate workers

        # Verify only one set of workers
        assert len(pool._worker_tasks) == 1

        # Cleanup
        await pool.stop()

    @pytest.mark.asyncio
    async def test_stop_without_wait(self, tmp_path):
        """Test stopping without waiting for tasks."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: sleep
timeout: 30
steps:
  - send: "10"
validations: []
""")

        config = WorkerPoolConfig(num_workers=1, verbose=False)
        pool = WorkerPool(config=config)

        task = TaskQueue.create_task(scenario, priority=1)
        await pool.submit(task)

        pool.start()

        # Stop immediately without waiting
        await pool.stop(wait=False)

        assert pool._running is False

    @pytest.mark.asyncio
    async def test_verbose_logging(self, tmp_path, capsys):
        """Test verbose logging output."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: echo
timeout: 5
steps:
  - send: "test"
validations: []
""")

        config = WorkerPoolConfig(num_workers=1, verbose=True)
        pool = WorkerPool(config=config)

        task = TaskQueue.create_task(scenario, priority=1)
        await pool.submit(task)

        await pool.wait_all()

        captured = capsys.readouterr()
        assert "[WorkerPool]" in captured.out
        assert "Submitted task" in captured.out


class TestWorkerCoverage:
    """Increase coverage for Worker."""

    def test_worker_status_properties(self):
        """Test worker status property accessors."""
        worker = Worker(worker_id=0, verbose=False)

        # Test idle
        assert worker.is_idle is True
        assert worker.is_busy is False
        assert worker.is_stopped is False

        # Test stopped
        worker.stop()
        assert worker.is_stopped is True


    @pytest.mark.asyncio
    async def test_worker_logging_verbose(self, tmp_path, capsys):
        """Test worker verbose logging."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("""name: Test
command: echo
timeout: 5
steps:
  - send: "test"
validations: []
""")

        worker = Worker(worker_id=99, verbose=True)
        task = TaskQueue.create_task(scenario, workspace=tmp_path)

        await worker.execute_task(task)

        captured = capsys.readouterr()
        assert "[Worker-99]" in captured.out
        assert "Starting task" in captured.out


class TestTaskQueueCoverage:
    """Increase coverage for TaskQueue."""

    @pytest.mark.asyncio
    async def test_queue_empty_results(self):
        """Test getting results from empty queue."""
        queue = TaskQueue()
        results = queue.get_all_results()
        assert results == []

    @pytest.mark.asyncio
    async def test_queue_with_max_size(self, tmp_path):
        """Test queue with maximum size limit."""
        queue = TaskQueue(max_size=2)

        # Create actual test files
        file1 = tmp_path / "test1.yaml"
        file1.write_text("name: Test1\ncommand: echo\nsteps: []\nvalidations: []")
        file2 = tmp_path / "test2.yaml"
        file2.write_text("name: Test2\ncommand: echo\nsteps: []\nvalidations: []")

        # Create tasks
        task1 = Task(
            task_id="1",
            scenario_path=file1,
            priority=1
        )
        task2 = Task(
            task_id="2",
            scenario_path=file2,
            priority=2
        )

        # Add to queue
        await queue.put(task1)
        await queue.put(task2)

        # Queue should be at capacity
        assert queue.qsize() == 2


class TestTaskResultCoverage:
    """Test TaskResult properties."""

    def test_task_result_completed(self):
        """Test completed task result."""
        result = TaskResult(
            task_id="test",
            scenario_path=Path("test.yaml"),
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            success=True
        )

        assert result.completed is True
        assert result.failed is False

    def test_task_result_failed(self):
        """Test failed task result."""
        result = TaskResult(
            task_id="test",
            scenario_path=Path("test.yaml"),
            status=TaskStatus.FAILED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            success=False,
            error=Exception("Test error")
        )

        assert result.completed is False
        assert result.failed is True
        assert result.error is not None


class TestTaskValidation:
    """Test task validation."""

    def test_task_creation_validation(self, tmp_path):
        """Test task validation during creation."""
        # Test file not found validation
        missing_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError, match="Scenario file not found"):
            Task(
                task_id="test",
                scenario_path=missing_file,
                priority=1
            )

    def test_task_with_metadata(self, tmp_path):
        """Test task with custom metadata."""
        # Create actual file
        file_path = tmp_path / "test.yaml"
        file_path.write_text("name: Test\ncommand: echo\nsteps: []\nvalidations: []")

        metadata = {"custom": "value", "number": 42}
        task = Task(
            task_id="test",
            scenario_path=file_path,
            priority=1,
            metadata=metadata
        )

        assert task.metadata == metadata
        assert task.metadata["custom"] == "value"
