"""Step plugin protocol for custom step types.

This protocol enables extending Orchestro with custom step implementations
without modifying the core execution engine.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from ..parsing.models import Step


class ExecutionContext:
    """Context passed to step plugins during execution.

    Provides access to process, state, and utilities.
    """

    def __init__(
        self,
        process: Any,
        scenario_state: Dict[str, Any],
        verbose: bool = False
    ):
        """Initialize execution context.

        Args:
            process: Process handle (ProcessDriver implementation)
            scenario_state: Shared state for the scenario execution
            verbose: Enable verbose logging
        """
        self.process = process
        self.scenario_state = scenario_state
        self.verbose = verbose

    def log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[Step] {message}")


class StepPlugin(Protocol):
    """Protocol for custom step implementations.

    Plugins can add new step types beyond the built-in expect/send/control/screenshot.

    Examples:
        - HTTPRequestStep (make API calls)
        - DatabaseQueryStep (verify database state)
        - FileOperationStep (create/modify files)
        - DelayStep (wait for specific time)
        - SnapshotStep (capture full state)
        - ConditionalStep (branching logic)
    """

    @property
    def step_type(self) -> str:
        """Unique identifier for this step type.

        Returns:
            Step type name (e.g., 'http_request', 'db_query')
        """
        ...

    def can_handle(self, step: Step) -> bool:
        """Check if this plugin can handle the given step.

        Args:
            step: Step object from scenario

        Returns:
            True if this plugin handles this step type
        """
        ...

    async def execute(
        self,
        step: Step,
        context: ExecutionContext,
        timeout: float
    ) -> Optional[Dict[str, Any]]:
        """Execute the step.

        Args:
            step: Step to execute
            context: Execution context with process and state
            timeout: Default timeout for this step

        Returns:
            Optional dict of results to add to scenario state

        Raises:
            StepExecutionError: If step fails
            TimeoutError: If step exceeds timeout
        """
        ...

    def validate_step(self, step: Step) -> List[str]:
        """Validate step configuration during dry-run.

        Args:
            step: Step to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


class StepResult:
    """Result of step execution."""

    def __init__(
        self,
        success: bool,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        duration: float = 0.0
    ):
        """Initialize step result.

        Args:
            success: Whether step succeeded
            message: Optional message about execution
            data: Optional data to add to scenario state
            duration: Execution duration in seconds
        """
        self.success = success
        self.message = message
        self.data = data or {}
        self.duration = duration
