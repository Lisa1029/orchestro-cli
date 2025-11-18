"""Advanced scheduling strategies for parallel execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import heapq
from datetime import datetime

from .task_queue import Task, TaskResult


@dataclass
class SchedulingMetrics:
    """Metrics for scheduling decisions."""

    worker_id: int
    tasks_completed: int
    tasks_failed: int
    avg_duration: float
    current_load: int  # Number of tasks in queue
    success_rate: float


class SchedulingStrategy(ABC):
    """Base class for scheduling strategies."""

    @abstractmethod
    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select the best worker for a task.

        Args:
            task: Task to schedule
            worker_metrics: Metrics for each worker

        Returns:
            Worker ID to assign task to
        """
        pass

    @abstractmethod
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Reorder tasks based on strategy.

        Args:
            tasks: List of pending tasks

        Returns:
            Reordered list of tasks
        """
        pass


class FIFOScheduler(SchedulingStrategy):
    """First-In-First-Out scheduling (default)."""

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select least loaded worker."""
        return min(worker_metrics, key=lambda m: m.current_load).worker_id

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Keep original order."""
        return tasks


class PriorityScheduler(SchedulingStrategy):
    """Priority-based scheduling with fairness."""

    def __init__(self, fairness_factor: float = 0.5):
        """Initialize scheduler.

        Args:
            fairness_factor: Balance between priority and fairness (0-1)
                             0 = pure priority, 1 = pure fairness
        """
        self.fairness_factor = fairness_factor

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select worker balancing load and success rate."""
        def score(m: SchedulingMetrics) -> float:
            # Lower is better
            load_score = m.current_load
            success_penalty = (1.0 - m.success_rate) * 10
            return load_score + success_penalty

        return min(worker_metrics, key=score).worker_id

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort by priority with fairness adjustment."""
        # Use heap for efficient priority queue
        prioritized = sorted(
            tasks,
            key=lambda t: (-t.priority, t.task_id),  # Higher priority first
            reverse=False
        )
        return prioritized


class ShortestJobFirstScheduler(SchedulingStrategy):
    """Schedule shorter tasks first to maximize throughput."""

    def __init__(self):
        """Initialize scheduler."""
        self.task_estimates: dict[str, float] = {}

    def estimate_duration(self, task: Task) -> float:
        """Estimate task duration based on history.

        Args:
            task: Task to estimate

        Returns:
            Estimated duration in seconds
        """
        # Use scenario name as key for historical data
        key = task.scenario_path.name

        if key in self.task_estimates:
            return self.task_estimates[key]

        # Default estimate based on timeout or 30s
        return task.timeout or 30.0

    def update_estimate(self, result: TaskResult) -> None:
        """Update duration estimate from completed task.

        Args:
            result: Completed task result
        """
        key = result.scenario_path.name

        if key in self.task_estimates:
            # Exponential moving average
            old = self.task_estimates[key]
            self.task_estimates[key] = 0.7 * old + 0.3 * result.duration
        else:
            self.task_estimates[key] = result.duration

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select worker with shortest queue time."""
        def queue_time(m: SchedulingMetrics) -> float:
            return m.current_load * m.avg_duration

        return min(worker_metrics, key=queue_time).worker_id

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort by estimated duration (shortest first)."""
        return sorted(tasks, key=self.estimate_duration)


class LoadBalancingScheduler(SchedulingStrategy):
    """Advanced load balancing with worker affinity."""

    def __init__(self, affinity_factor: float = 0.3):
        """Initialize scheduler.

        Args:
            affinity_factor: Weight for worker affinity (0-1)
        """
        self.affinity_factor = affinity_factor
        self.task_worker_affinity: dict[str, dict[int, float]] = {}

    def record_affinity(self, task: Task, worker_id: int, success: bool) -> None:
        """Record task-worker affinity.

        Args:
            task: Completed task
            worker_id: Worker that executed task
            success: Whether task succeeded
        """
        key = task.scenario_path.stem  # Use filename without extension

        if key not in self.task_worker_affinity:
            self.task_worker_affinity[key] = {}

        if worker_id not in self.task_worker_affinity[key]:
            self.task_worker_affinity[key][worker_id] = 0.5  # Neutral

        # Update affinity score
        current = self.task_worker_affinity[key][worker_id]
        adjustment = 0.1 if success else -0.1
        self.task_worker_affinity[key][worker_id] = max(
            0.0, min(1.0, current + adjustment)
        )

    def get_affinity(self, task: Task, worker_id: int) -> float:
        """Get affinity score for task-worker pair.

        Args:
            task: Task to check
            worker_id: Worker ID

        Returns:
            Affinity score (0-1, higher is better)
        """
        key = task.scenario_path.stem

        if key in self.task_worker_affinity:
            return self.task_worker_affinity[key].get(worker_id, 0.5)

        return 0.5  # Neutral for unknown combinations

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select worker balancing load and affinity."""
        def score(m: SchedulingMetrics) -> float:
            # Normalize load to 0-1
            max_load = max(wm.current_load for wm in worker_metrics)
            load_norm = m.current_load / max_load if max_load > 0 else 0

            # Get affinity
            affinity = self.get_affinity(task, m.worker_id)

            # Combined score (lower is better)
            return (
                (1 - self.affinity_factor) * load_norm +
                self.affinity_factor * (1 - affinity)
            )

        return min(worker_metrics, key=score).worker_id

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Keep priority order with minor reordering for affinity."""
        return sorted(tasks, key=lambda t: -t.priority)


class DeadlineAwareScheduler(SchedulingStrategy):
    """Schedule tasks to meet deadlines (earliest deadline first)."""

    def __init__(self):
        """Initialize scheduler."""
        self.task_deadlines: dict[str, datetime] = {}

    def set_deadline(self, task: Task, deadline: datetime) -> None:
        """Set deadline for a task.

        Args:
            task: Task to set deadline for
            deadline: Deadline timestamp
        """
        self.task_deadlines[task.task_id] = deadline

    def get_deadline(self, task: Task) -> Optional[datetime]:
        """Get deadline for a task.

        Args:
            task: Task to check

        Returns:
            Deadline or None if not set
        """
        return self.task_deadlines.get(task.task_id)

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Select fastest available worker for deadline-critical tasks."""
        deadline = self.get_deadline(task)

        if deadline:
            # Prioritize fastest worker
            return min(worker_metrics, key=lambda m: m.avg_duration).worker_id
        else:
            # Use least loaded for non-deadline tasks
            return min(worker_metrics, key=lambda m: m.current_load).worker_id

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort by deadline (earliest first)."""
        def sort_key(task: Task) -> tuple:
            deadline = self.get_deadline(task)
            if deadline:
                return (0, deadline)  # Deadline tasks first
            else:
                return (1, task.priority)  # Then by priority

        return sorted(tasks, key=sort_key)


class AdaptiveScheduler(SchedulingStrategy):
    """Adaptive scheduler that switches strategies based on workload."""

    def __init__(self):
        """Initialize adaptive scheduler."""
        self.strategies = {
            "priority": PriorityScheduler(),
            "sjf": ShortestJobFirstScheduler(),
            "load_balance": LoadBalancingScheduler(),
            "deadline": DeadlineAwareScheduler(),
        }
        self.current_strategy = "priority"
        self.performance_history: List[float] = []

    def set_strategy(self, strategy_name: str) -> None:
        """Switch to a different strategy.

        Args:
            strategy_name: Name of strategy to use
        """
        if strategy_name in self.strategies:
            self.current_strategy = strategy_name

    def analyze_workload(self, tasks: List[Task]) -> str:
        """Analyze workload and select best strategy.

        Args:
            tasks: Current task queue

        Returns:
            Strategy name to use
        """
        if not tasks:
            return "priority"

        # Check for deadlines
        has_deadlines = any(
            isinstance(self.strategies["deadline"], DeadlineAwareScheduler) and
            self.strategies["deadline"].get_deadline(t)
            for t in tasks
        )
        if has_deadlines:
            return "deadline"

        # Check for large number of tasks
        if len(tasks) > 50:
            return "sjf"  # Optimize throughput

        # Check priority spread
        priorities = [t.priority for t in tasks]
        if max(priorities) - min(priorities) > 5:
            return "priority"  # Honor priorities

        # Default to load balancing
        return "load_balance"

    def select_worker(
        self,
        task: Task,
        worker_metrics: List[SchedulingMetrics]
    ) -> int:
        """Delegate to current strategy."""
        strategy = self.strategies[self.current_strategy]
        return strategy.select_worker(task, worker_metrics)

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Adapt strategy and prioritize tasks."""
        # Analyze and switch if needed
        best_strategy = self.analyze_workload(tasks)
        if best_strategy != self.current_strategy:
            self.set_strategy(best_strategy)

        # Use current strategy
        strategy = self.strategies[self.current_strategy]
        return strategy.prioritize_tasks(tasks)
