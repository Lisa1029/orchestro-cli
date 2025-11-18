"""Example: Delay step plugin.

Adds a 'delay' step type that waits for a specified duration.

Usage in YAML:
  steps:
    - delay: 2.5  # Wait 2.5 seconds
      note: "Waiting for animation to complete"
"""

import asyncio
from typing import Any, Dict, List, Optional

from orchestro_cli.interfaces.step_plugin import ExecutionContext, StepPlugin
from orchestro_cli.parsing.models import Step


class DelayStepPlugin:
    """Plugin that adds delay/wait capability to scenarios."""

    @property
    def step_type(self) -> str:
        """Step type identifier."""
        return "delay"

    def can_handle(self, step: Step) -> bool:
        """Check if step has delay field."""
        # In a real implementation, Step would have a custom_data field
        # For now, we check if step.note contains 'delay:'
        return (
            step.note is not None and
            step.note.strip().startswith("delay:")
        )

    async def execute(
        self,
        step: Step,
        context: ExecutionContext,
        timeout: float
    ) -> Optional[Dict[str, Any]]:
        """Execute delay step.

        Args:
            step: Step with delay configuration
            context: Execution context
            timeout: Maximum allowed delay

        Returns:
            Dict with delay duration

        Raises:
            ValueError: If delay exceeds timeout
        """
        # Extract delay from note (format: "delay: 2.5")
        delay_str = step.note.replace("delay:", "").strip()
        try:
            delay = float(delay_str)
        except ValueError:
            raise ValueError(f"Invalid delay value: {delay_str}")

        if delay > timeout:
            raise ValueError(
                f"Delay {delay}s exceeds timeout {timeout}s"
            )

        context.log(f"Delaying for {delay} seconds...")
        await asyncio.sleep(delay)
        context.log(f"Delay complete")

        return {"delay_duration": delay}

    def validate_step(self, step: Step) -> List[str]:
        """Validate delay step configuration.

        Args:
            step: Step to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if step.note is None:
            errors.append("Delay step requires 'note' field")
            return errors

        if not step.note.strip().startswith("delay:"):
            errors.append("Delay step note must start with 'delay:'")
            return errors

        delay_str = step.note.replace("delay:", "").strip()
        try:
            delay = float(delay_str)
            if delay <= 0:
                errors.append(f"Delay must be positive, got {delay}")
            if delay > 300:  # 5 minutes max
                errors.append(f"Delay too long (max 300s), got {delay}")
        except ValueError:
            errors.append(f"Invalid delay value: {delay_str}")

        return errors


def register(registry):
    """Register delay step plugin.

    Args:
        registry: PluginRegistry instance
    """
    plugin = DelayStepPlugin()
    registry.register_step_plugin(plugin)
    print(f"[Plugin] Registered: {plugin.step_type} step")
