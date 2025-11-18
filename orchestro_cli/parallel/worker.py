"""Worker process for parallel scenario execution."""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from ..core import Orchestrator
from .task_queue import Task, TaskResult, TaskStatus


class WorkerStatus(Enum):
    """Worker state."""

    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"


class Worker:
    """Worker that executes scenarios from a task queue.

    Each worker runs in its own async context and can execute
    scenarios independently with process isolation.
    """

    def __init__(
        self,
        worker_id: int,
        verbose: bool = False,
        junit_xml_dir: Optional[Path] = None
    ):
        """Initialize worker.

        Args:
            worker_id: Unique worker identifier
            verbose: Enable verbose logging
            junit_xml_dir: Optional directory for JUnit XML reports
        """
        self.worker_id = worker_id
        self.verbose = verbose
        self.junit_xml_dir = junit_xml_dir

        self.status = WorkerStatus.IDLE
        self.current_task: Optional[Task] = None
        self.tasks_completed = 0
        self.tasks_failed = 0

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[Worker-{self.worker_id}] {message}")

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task.

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution details
        """
        self.status = WorkerStatus.BUSY
        self.current_task = task
        self._log(f"Starting task {task.task_id}: {task.scenario_path.name}")

        start_time = datetime.now()
        success = False
        error: Optional[Exception] = None
        output: Optional[str] = None

        try:
            # Create isolated orchestrator for this task
            junit_xml_path = None
            if self.junit_xml_dir:
                junit_xml_path = (
                    self.junit_xml_dir /
                    f"{task.scenario_path.stem}_{task.task_id}.xml"
                )

            orchestrator = Orchestrator(
                workspace=task.workspace,
                verbose=self.verbose,
                junit_xml_path=junit_xml_path
            )

            # Execute scenario using async method (we're already in async context)
            await orchestrator.run_async(task.scenario_path)
            success = True
            self.tasks_completed += 1
            self._log(f"Completed task {task.task_id}")

        except Exception as e:
            error = e
            self.tasks_failed += 1
            self._log(f"Failed task {task.task_id}: {e}")

        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Create result
            result = TaskResult(
                task_id=task.task_id,
                scenario_path=task.scenario_path,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                error=error,
                output=output,
                metadata=task.metadata
            )

            # Reset worker state
            self.status = WorkerStatus.IDLE
            self.current_task = None

            return result

    def stop(self) -> None:
        """Stop the worker."""
        self.status = WorkerStatus.STOPPED
        self._log("Worker stopped")

    @property
    def is_idle(self) -> bool:
        """Check if worker is idle."""
        return self.status == WorkerStatus.IDLE

    @property
    def is_busy(self) -> bool:
        """Check if worker is busy."""
        return self.status == WorkerStatus.BUSY

    @property
    def is_stopped(self) -> bool:
        """Check if worker is stopped."""
        return self.status == WorkerStatus.STOPPED

    def get_stats(self) -> dict:
        """Get worker statistics.

        Returns:
            Dict with worker stats
        """
        return {
            "worker_id": self.worker_id,
            "status": self.status.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "current_task": (
                self.current_task.task_id if self.current_task else None
            ),
        }
