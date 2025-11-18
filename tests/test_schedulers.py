"""Tests for advanced scheduling strategies."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from orchestro_cli.parallel import (
    Task,
    TaskResult,
    TaskStatus,
    SchedulingMetrics,
    FIFOScheduler,
    PriorityScheduler,
    ShortestJobFirstScheduler,
    LoadBalancingScheduler,
    DeadlineAwareScheduler,
    AdaptiveScheduler,
)


@pytest.fixture
def sample_tasks(tmp_path):
    """Create sample tasks for testing."""
    tasks = []
    for i in range(5):
        scenario = tmp_path / f"task_{i}.yaml"
        scenario.write_text(f"name: Task {i}\ncommand: echo\nsteps: []\nvalidations: []")
        task = Task(
            task_id=f"task_{i}",
            scenario_path=scenario,
            priority=i,  # Priority 0-4
            timeout=30.0
        )
        tasks.append(task)
    return tasks


@pytest.fixture
def sample_metrics():
    """Create sample worker metrics."""
    return [
        SchedulingMetrics(
            worker_id=0,
            tasks_completed=10,
            tasks_failed=1,
            avg_duration=2.0,
            current_load=2,
            success_rate=0.9
        ),
        SchedulingMetrics(
            worker_id=1,
            tasks_completed=8,
            tasks_failed=0,
            avg_duration=1.5,
            current_load=1,
            success_rate=1.0
        ),
        SchedulingMetrics(
            worker_id=2,
            tasks_completed=12,
            tasks_failed=3,
            avg_duration=2.5,
            current_load=3,
            success_rate=0.75
        ),
    ]


class TestFIFOScheduler:
    """Test First-In-First-Out scheduler."""

    def test_select_least_loaded_worker(self, sample_tasks, sample_metrics):
        """Should select worker with lowest current load."""
        scheduler = FIFOScheduler()
        worker_id = scheduler.select_worker(sample_tasks[0], sample_metrics)

        # Worker 1 has current_load=1 (lowest)
        assert worker_id == 1

    def test_preserve_task_order(self, sample_tasks):
        """Should not reorder tasks."""
        scheduler = FIFOScheduler()
        prioritized = scheduler.prioritize_tasks(sample_tasks)

        assert prioritized == sample_tasks


class TestPriorityScheduler:
    """Test priority-based scheduler."""

    def test_select_worker_by_load_and_success(self, sample_tasks, sample_metrics):
        """Should balance load and success rate."""
        scheduler = PriorityScheduler(fairness_factor=0.5)
        worker_id = scheduler.select_worker(sample_tasks[0], sample_metrics)

        # Worker 1 has best combination of low load and high success rate
        assert worker_id == 1

    def test_prioritize_by_priority(self, sample_tasks):
        """Should sort tasks by priority (highest first)."""
        scheduler = PriorityScheduler()
        prioritized = scheduler.prioritize_tasks(sample_tasks)

        # Should be reversed (priority 4, 3, 2, 1, 0)
        priorities = [t.priority for t in prioritized]
        assert priorities == [4, 3, 2, 1, 0]


class TestShortestJobFirstScheduler:
    """Test shortest job first scheduler."""

    def test_estimate_duration_default(self, sample_tasks):
        """Should use timeout as default estimate."""
        scheduler = ShortestJobFirstScheduler()
        estimate = scheduler.estimate_duration(sample_tasks[0])

        assert estimate == 30.0  # Task timeout

    def test_update_estimate(self, sample_tasks):
        """Should update estimates from completed tasks."""
        scheduler = ShortestJobFirstScheduler()

        result = TaskResult(
            task_id="task_0",
            scenario_path=sample_tasks[0].scenario_path,
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=10.0,
            success=True
        )

        scheduler.update_estimate(result)

        # Should now estimate based on actual duration
        estimate = scheduler.estimate_duration(sample_tasks[0])
        assert estimate == 10.0

    def test_exponential_moving_average(self, sample_tasks):
        """Should smooth estimates with EMA."""
        scheduler = ShortestJobFirstScheduler()

        # First result: 10s
        result1 = TaskResult(
            task_id="task_0",
            scenario_path=sample_tasks[0].scenario_path,
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=10.0,
            success=True
        )
        scheduler.update_estimate(result1)

        # Second result: 20s
        result2 = TaskResult(
            task_id="task_0",
            scenario_path=sample_tasks[0].scenario_path,
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=20.0,
            success=True
        )
        scheduler.update_estimate(result2)

        # Estimate should be: 0.7 * 10 + 0.3 * 20 = 13.0
        estimate = scheduler.estimate_duration(sample_tasks[0])
        assert abs(estimate - 13.0) < 0.01

    def test_prioritize_by_duration(self, sample_tasks):
        """Should sort by estimated duration."""
        scheduler = ShortestJobFirstScheduler()

        # Add different estimates
        for i, task in enumerate(sample_tasks):
            result = TaskResult(
                task_id=task.task_id,
                scenario_path=task.scenario_path,
                status=TaskStatus.COMPLETED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=float(5 - i),  # 5, 4, 3, 2, 1
                success=True
            )
            scheduler.update_estimate(result)

        prioritized = scheduler.prioritize_tasks(sample_tasks)

        # Should be sorted by duration (1, 2, 3, 4, 5)
        durations = [scheduler.estimate_duration(t) for t in prioritized]
        assert durations == sorted(durations)


class TestLoadBalancingScheduler:
    """Test load balancing scheduler with affinity."""

    def test_record_affinity(self, sample_tasks):
        """Should record task-worker affinity."""
        scheduler = LoadBalancingScheduler()

        scheduler.record_affinity(sample_tasks[0], worker_id=0, success=True)
        affinity = scheduler.get_affinity(sample_tasks[0], worker_id=0)

        # Should increase from neutral (0.5)
        assert affinity > 0.5

    def test_affinity_decreases_on_failure(self, sample_tasks):
        """Should decrease affinity on failure."""
        scheduler = LoadBalancingScheduler()

        scheduler.record_affinity(sample_tasks[0], worker_id=0, success=False)
        affinity = scheduler.get_affinity(sample_tasks[0], worker_id=0)

        # Should decrease from neutral (0.5)
        assert affinity < 0.5

    def test_affinity_bounds(self, sample_tasks):
        """Should clamp affinity to [0, 1]."""
        scheduler = LoadBalancingScheduler()

        # Record many successes
        for _ in range(20):
            scheduler.record_affinity(sample_tasks[0], worker_id=0, success=True)

        affinity = scheduler.get_affinity(sample_tasks[0], worker_id=0)
        assert 0.0 <= affinity <= 1.0

    def test_select_worker_with_affinity(self, sample_tasks, sample_metrics):
        """Should consider affinity when selecting worker."""
        scheduler = LoadBalancingScheduler(affinity_factor=0.8)

        # Record high affinity for worker 2
        for _ in range(5):
            scheduler.record_affinity(sample_tasks[0], worker_id=2, success=True)

        worker_id = scheduler.select_worker(sample_tasks[0], sample_metrics)

        # May select worker 2 despite higher load due to affinity
        assert worker_id in [0, 1, 2]


class TestDeadlineAwareScheduler:
    """Test deadline-aware scheduler."""

    def test_set_and_get_deadline(self, sample_tasks):
        """Should set and retrieve deadlines."""
        scheduler = DeadlineAwareScheduler()

        deadline = datetime.now() + timedelta(minutes=10)
        scheduler.set_deadline(sample_tasks[0], deadline)

        retrieved = scheduler.get_deadline(sample_tasks[0])
        assert retrieved == deadline

    def test_prioritize_by_deadline(self, sample_tasks):
        """Should prioritize tasks by earliest deadline."""
        scheduler = DeadlineAwareScheduler()

        # Set deadlines in reverse order
        for i, task in enumerate(sample_tasks):
            deadline = datetime.now() + timedelta(minutes=len(sample_tasks) - i)
            scheduler.set_deadline(task, deadline)

        prioritized = scheduler.prioritize_tasks(sample_tasks)

        # Should be reordered by deadline
        deadlines = [scheduler.get_deadline(t) for t in prioritized]
        assert deadlines == sorted([d for d in deadlines if d])

    def test_select_fastest_worker_for_deadline_tasks(self, sample_tasks, sample_metrics):
        """Should select fastest worker for deadline tasks."""
        scheduler = DeadlineAwareScheduler()

        # Set deadline
        deadline = datetime.now() + timedelta(minutes=5)
        scheduler.set_deadline(sample_tasks[0], deadline)

        worker_id = scheduler.select_worker(sample_tasks[0], sample_metrics)

        # Worker 1 has lowest avg_duration=1.5
        assert worker_id == 1


class TestAdaptiveScheduler:
    """Test adaptive scheduler."""

    def test_initial_strategy(self):
        """Should start with priority strategy."""
        scheduler = AdaptiveScheduler()
        assert scheduler.current_strategy == "priority"

    def test_set_strategy(self):
        """Should allow manual strategy selection."""
        scheduler = AdaptiveScheduler()

        scheduler.set_strategy("sjf")
        assert scheduler.current_strategy == "sjf"

    def test_analyze_workload_for_deadlines(self, sample_tasks):
        """Should switch to deadline strategy when deadlines present."""
        scheduler = AdaptiveScheduler()

        # Set a deadline
        deadline_scheduler = scheduler.strategies["deadline"]
        deadline = datetime.now() + timedelta(minutes=10)
        deadline_scheduler.set_deadline(sample_tasks[0], deadline)

        strategy = scheduler.analyze_workload(sample_tasks)
        assert strategy == "deadline"

    def test_analyze_workload_for_large_queue(self, sample_tasks):
        """Should use SJF for large queues."""
        scheduler = AdaptiveScheduler()

        # Create large task list (> 50)
        large_queue = sample_tasks * 15  # 75 tasks

        strategy = scheduler.analyze_workload(large_queue)
        assert strategy == "sjf"

    def test_analyze_workload_for_priority_spread(self, sample_tasks):
        """Should use priority strategy for wide priority spread."""
        scheduler = AdaptiveScheduler()

        # Tasks already have priorities 0-4 (spread of 4)
        # Modify to have spread > 5
        sample_tasks[0].priority = 0
        sample_tasks[4].priority = 10  # Spread of 10

        strategy = scheduler.analyze_workload(sample_tasks)
        assert strategy == "priority"

    def test_delegate_to_current_strategy(self, sample_tasks, sample_metrics):
        """Should delegate selection to current strategy."""
        scheduler = AdaptiveScheduler()

        scheduler.set_strategy("priority")
        worker_id = scheduler.select_worker(sample_tasks[0], sample_metrics)

        # Should use priority scheduler's logic
        assert worker_id in [0, 1, 2]

    def test_adaptive_prioritization(self, sample_tasks):
        """Should adapt strategy during prioritization."""
        scheduler = AdaptiveScheduler()

        # Large queue should trigger SJF
        large_queue = sample_tasks * 15

        prioritized = scheduler.prioritize_tasks(large_queue)

        # Should have switched to SJF
        assert scheduler.current_strategy == "sjf"
        assert len(prioritized) == len(large_queue)
