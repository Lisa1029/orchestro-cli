"""Task queue for parallel scenario execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a scenario execution task."""

    scenario_path: Path
    task_id: str
    workspace: Optional[Path] = None
    env: Optional[Dict[str, str]] = None
    priority: int = 0  # Higher = more important
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate task configuration."""
        if not self.scenario_path.exists():
            raise FileNotFoundError(
                f"Scenario file not found: {self.scenario_path}"
            )


@dataclass
class TaskResult:
    """Result of task execution."""

    task_id: str
    scenario_path: Path
    status: TaskStatus
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    error: Optional[Exception] = None
    output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def failed(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED

    @property
    def completed(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED and self.success


class TaskQueue:
    """Priority queue for scenario execution tasks.

    Features:
    - Priority-based ordering (higher priority first)
    - FIFO within same priority
    - Async task management
    - Task cancellation support
    """

    def __init__(self, max_size: int = 0):
        """Initialize task queue.

        Args:
            max_size: Maximum queue size (0 = unlimited)
        """
        self.max_size = max_size
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=max_size
        )
        self._tasks: Dict[str, Task] = {}
        self._results: Dict[str, TaskResult] = {}
        self._counter = 0  # For FIFO ordering within same priority

    async def put(self, task: Task) -> None:
        """Add task to queue.

        Args:
            task: Task to add

        Raises:
            asyncio.QueueFull: If queue is at max capacity
        """
        # Priority queue uses (priority, counter, item) tuples
        # Negative priority for max-heap behavior (higher number = higher priority)
        # Counter ensures FIFO for same priority
        priority_tuple = (-task.priority, self._counter, task)
        self._counter += 1

        await self._queue.put(priority_tuple)
        self._tasks[task.task_id] = task

    async def get(self) -> Task:
        """Get next task from queue.

        Returns:
            Highest priority task

        Raises:
            asyncio.QueueEmpty: If queue is empty
        """
        _, _, task = await self._queue.get()
        return task

    def task_done(self) -> None:
        """Mark current task as complete."""
        self._queue.task_done()

    async def join(self) -> None:
        """Wait for all tasks to complete."""
        await self._queue.join()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()

    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def add_result(self, result: TaskResult) -> None:
        """Store task result.

        Args:
            result: Task execution result
        """
        self._results[result.task_id] = result

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskResult if found, None otherwise
        """
        return self._results.get(task_id)

    def get_all_results(self) -> list[TaskResult]:
        """Get all task results.

        Returns:
            List of all results
        """
        return list(self._results.values())

    def clear_results(self) -> None:
        """Clear all stored results."""
        self._results.clear()

    @staticmethod
    def create_task(
        scenario_path: Path,
        workspace: Optional[Path] = None,
        priority: int = 0,
        timeout: Optional[float] = None,
        **metadata
    ) -> Task:
        """Create a new task with auto-generated ID.

        Args:
            scenario_path: Path to scenario file
            workspace: Optional workspace directory
            priority: Task priority (higher = more important)
            timeout: Optional timeout in seconds
            **metadata: Additional metadata

        Returns:
            New Task instance
        """
        return Task(
            scenario_path=scenario_path,
            task_id=str(uuid4()),
            workspace=workspace,
            priority=priority,
            timeout=timeout,
            metadata=metadata or None,
        )
