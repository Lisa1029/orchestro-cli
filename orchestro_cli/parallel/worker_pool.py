"""Worker pool for parallel scenario execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .task_queue import Task, TaskQueue, TaskResult
from .worker import Worker


@dataclass
class WorkerPoolConfig:
    """Configuration for worker pool."""

    num_workers: int = 4
    max_queue_size: int = 0  # 0 = unlimited
    verbose: bool = False
    junit_xml_dir: Optional[Path] = None
    timeout_per_task: Optional[float] = None  # Global task timeout


class WorkerPool:
    """Pool of workers for parallel scenario execution.

    Features:
    - Configurable worker count
    - Priority-based task queue
    - Automatic task distribution
    - Progress tracking
    - Result aggregation
    - Graceful shutdown

    Usage:
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=4))

        # Add tasks
        for scenario in scenarios:
            task = TaskQueue.create_task(scenario, priority=1)
            await pool.submit(task)

        # Wait for completion
        results = await pool.wait_all()
    """

    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        """Initialize worker pool.

        Args:
            config: Pool configuration (uses defaults if None)
        """
        self.config = config or WorkerPoolConfig()

        self.task_queue = TaskQueue(max_size=self.config.max_queue_size)
        self.workers: List[Worker] = []
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False
        self._start_time: Optional[datetime] = None

        # Initialize workers
        for i in range(self.config.num_workers):
            worker = Worker(
                worker_id=i,
                verbose=self.config.verbose,
                junit_xml_dir=self.config.junit_xml_dir
            )
            self.workers.append(worker)

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.config.verbose:
            print(f"[WorkerPool] {message}")

    async def submit(self, task: Task) -> None:
        """Submit a task to the queue.

        Args:
            task: Task to execute

        Raises:
            asyncio.QueueFull: If queue is at capacity
        """
        await self.task_queue.put(task)
        self._log(f"Submitted task {task.task_id}: {task.scenario_path.name}")

    async def submit_many(self, tasks: List[Task]) -> None:
        """Submit multiple tasks.

        Args:
            tasks: List of tasks to execute
        """
        for task in tasks:
            await self.submit(task)

    async def _worker_loop(self, worker: Worker) -> None:
        """Main worker loop.

        Args:
            worker: Worker instance to run
        """
        self._log(f"Worker {worker.worker_id} started")

        while self._running:
            try:
                # Get next task (with timeout to allow checking _running flag)
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )

                # Execute task
                result = await worker.execute_task(task)

                # Store result
                self.task_queue.add_result(result)

                # Mark task done
                self.task_queue.task_done()

            except asyncio.TimeoutError:
                # No tasks available, continue loop
                continue

            except Exception as e:
                self._log(f"Worker {worker.worker_id} error: {e}")

        self._log(f"Worker {worker.worker_id} stopped")

    def start(self) -> None:
        """Start the worker pool.

        Workers will begin processing tasks from the queue.
        """
        if self._running:
            return

        self._running = True
        self._start_time = datetime.now()
        self._log(f"Starting pool with {self.config.num_workers} workers")

        # Start worker tasks
        for worker in self.workers:
            task = asyncio.create_task(self._worker_loop(worker))
            self._worker_tasks.append(task)

    async def stop(self, wait: bool = True) -> None:
        """Stop the worker pool.

        Args:
            wait: Wait for current tasks to complete before stopping
        """
        self._log("Stopping worker pool...")
        self._running = False

        if wait:
            # Wait for current tasks to complete
            await self.task_queue.join()

        # Stop all workers
        for worker in self.workers:
            worker.stop()

        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()

        # Wait for cancellation
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        self._log("Worker pool stopped")

    async def wait_all(self, timeout: Optional[float] = None) -> List[TaskResult]:
        """Wait for all tasks to complete.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            List of all task results

        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        # Ensure pool is started
        if not self._running:
            self.start()

        # Wait for all tasks
        if timeout:
            await asyncio.wait_for(self.task_queue.join(), timeout=timeout)
        else:
            await self.task_queue.join()

        # Stop pool
        await self.stop(wait=False)

        # Return results
        return self.task_queue.get_all_results()

    def get_progress(self) -> dict:
        """Get current execution progress.

        Returns:
            Dict with progress statistics
        """
        results = self.task_queue.get_all_results()
        completed = sum(1 for r in results if r.completed)
        failed = sum(1 for r in results if r.failed)

        return {
            "queue_size": self.task_queue.qsize(),
            "completed": completed,
            "failed": failed,
            "total_results": len(results),
            "workers": [w.get_stats() for w in self.workers],
            "running": self._running,
        }

    def get_stats(self) -> dict:
        """Get comprehensive pool statistics.

        Returns:
            Dict with all statistics
        """
        results = self.task_queue.get_all_results()
        completed = sum(1 for r in results if r.completed)
        failed = sum(1 for r in results if r.failed)

        total_duration = 0.0
        if results:
            total_duration = sum(r.duration for r in results)

        elapsed = 0.0
        if self._start_time:
            elapsed = (datetime.now() - self._start_time).total_seconds()

        return {
            "config": {
                "num_workers": self.config.num_workers,
                "max_queue_size": self.config.max_queue_size,
            },
            "execution": {
                "running": self._running,
                "elapsed_seconds": elapsed,
                "queue_size": self.task_queue.qsize(),
            },
            "results": {
                "total": len(results),
                "completed": completed,
                "failed": failed,
                "success_rate": (
                    completed / len(results) * 100 if results else 0
                ),
            },
            "performance": {
                "total_task_duration": total_duration,
                "average_task_duration": (
                    total_duration / len(results) if results else 0
                ),
                "speedup": (
                    total_duration / elapsed if elapsed > 0 else 0
                ),
            },
            "workers": [w.get_stats() for w in self.workers],
        }
