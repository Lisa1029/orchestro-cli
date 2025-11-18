"""Tests for parallel execution system."""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from orchestro_cli.parallel import (
    WorkerPool,
    WorkerPoolConfig,
    TaskQueue,
    Task,
    TaskResult,
    Worker,
    WorkerStatus,
    TaskStatus,
)


class TestTaskQueue:
    """Test task queue functionality."""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test queue initialization."""
        queue = TaskQueue()
        assert queue.empty()
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_create_task(self, tmp_path):
        """Test task creation."""
        scenario = tmp_path / "test.yaml"
        scenario.write_text("name: test\ncommand: echo\nsteps: []")

        task = TaskQueue.create_task(
            scenario_path=scenario,
            priority=5,
            test_key="test_value"
        )

        assert task.scenario_path == scenario
        assert task.priority == 5
        assert task.task_id is not None
        assert task.metadata == {"test_key": "test_value"}

    @pytest.mark.asyncio
    async def test_task_validation(self):
        """Test task validation."""
        with pytest.raises(FileNotFoundError):
            Task(
                scenario_path=Path("/nonexistent/file.yaml"),
                task_id="test"
            )

    @pytest.mark.asyncio
    async def test_put_get(self, tmp_path):
        """Test putting and getting tasks."""
        queue = TaskQueue()
        scenario = tmp_path / "test.yaml"
        scenario.write_text("name: test")

        task = Task(scenario_path=scenario, task_id="test1", priority=1)
        await queue.put(task)

        assert queue.qsize() == 1
        retrieved = await queue.get()
        assert retrieved.task_id == "test1"

    @pytest.mark.asyncio
    async def test_priority_ordering(self, tmp_path):
        """Test priority-based ordering."""
        queue = TaskQueue()
        scenario = tmp_path / "test.yaml"
        scenario.write_text("name: test")

        # Add tasks with different priorities
        low = Task(scenario_path=scenario, task_id="low", priority=1)
        high = Task(scenario_path=scenario, task_id="high", priority=10)
        medium = Task(scenario_path=scenario, task_id="medium", priority=5)

        await queue.put(low)
        await queue.put(high)
        await queue.put(medium)

        # Should get in priority order: high, medium, low
        assert (await queue.get()).task_id == "high"
        assert (await queue.get()).task_id == "medium"
        assert (await queue.get()).task_id == "low"

    @pytest.mark.asyncio
    async def test_results(self):
        """Test result storage."""
        queue = TaskQueue()

        result = TaskResult(
            task_id="test1",
            scenario_path=Path("test.yaml"),
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            success=True
        )

        queue.add_result(result)
        assert queue.get_result("test1") == result
        assert len(queue.get_all_results()) == 1

        queue.clear_results()
        assert len(queue.get_all_results()) == 0


class TestWorker:
    """Test worker functionality."""

    def test_init(self):
        """Test worker initialization."""
        worker = Worker(worker_id=1, verbose=True)
        assert worker.worker_id == 1
        assert worker.status == WorkerStatus.IDLE
        assert worker.tasks_completed == 0
        assert worker.tasks_failed == 0

    def test_is_idle(self):
        """Test idle status check."""
        worker = Worker(worker_id=1)
        assert worker.is_idle
        assert not worker.is_busy
        assert not worker.is_stopped

    def test_stop(self):
        """Test worker stop."""
        worker = Worker(worker_id=1)
        worker.stop()
        assert worker.is_stopped

    def test_get_stats(self):
        """Test worker statistics."""
        worker = Worker(worker_id=1)
        stats = worker.get_stats()

        assert stats["worker_id"] == 1
        assert stats["status"] == "idle"
        assert stats["tasks_completed"] == 0
        assert stats["tasks_failed"] == 0
        assert stats["current_task"] is None


class TestWorkerPool:
    """Test worker pool functionality."""

    def test_init(self):
        """Test pool initialization."""
        config = WorkerPoolConfig(num_workers=2)
        pool = WorkerPool(config=config)

        assert len(pool.workers) == 2
        assert not pool._running

    def test_default_config(self):
        """Test default configuration."""
        pool = WorkerPool()
        assert pool.config.num_workers == 4

    @pytest.mark.asyncio
    async def test_submit(self, tmp_path):
        """Test task submission."""
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=1))
        scenario = tmp_path / "test.yaml"
        scenario.write_text("name: test")

        task = Task(scenario_path=scenario, task_id="test1")
        await pool.submit(task)

        assert pool.task_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_submit_many(self, tmp_path):
        """Test submitting multiple tasks."""
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=1))
        scenario = tmp_path / "test.yaml"
        scenario.write_text("name: test")

        tasks = [
            Task(scenario_path=scenario, task_id=f"test{i}")
            for i in range(3)
        ]

        await pool.submit_many(tasks)
        assert pool.task_queue.qsize() == 3

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping pool."""
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=2))

        pool.start()
        assert pool._running
        assert len(pool._worker_tasks) == 2

        await pool.stop()
        assert not pool._running
        assert len(pool._worker_tasks) == 0

    @pytest.mark.asyncio
    async def test_get_progress(self, tmp_path):
        """Test progress tracking."""
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=1))
        progress = pool.get_progress()

        assert "queue_size" in progress
        assert "completed" in progress
        assert "failed" in progress
        assert "workers" in progress
        assert progress["running"] == False

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test comprehensive statistics."""
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=2))
        stats = pool.get_stats()

        assert "config" in stats
        assert "execution" in stats
        assert "results" in stats
        assert "performance" in stats
        assert "workers" in stats
        assert stats["config"]["num_workers"] == 2


class TestTaskResult:
    """Test task result functionality."""

    def test_completed_property(self):
        """Test completed property."""
        result = TaskResult(
            task_id="test",
            scenario_path=Path("test.yaml"),
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            success=True
        )

        assert result.completed
        assert not result.failed

    def test_failed_property(self):
        """Test failed property."""
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

        assert result.failed
        assert not result.completed
