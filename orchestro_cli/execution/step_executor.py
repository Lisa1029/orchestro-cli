"""Step execution orchestration."""

import asyncio
import re
import time
from pathlib import Path
from typing import Optional, List
import pexpect

from ..parsing.models import Step
from ..sentinel_monitor import SentinelMonitor
from ..assertions.models import Assertion, AssertionType
from ..assertions.engine import AssertionEngine
from .step_result import StepResult


class StepExecutor:
    """Executes individual scenario steps.

    Single Responsibility: Orchestrate step execution against a process.
    """

    def __init__(
        self,
        process: pexpect.spawn,
        sentinel_monitor: SentinelMonitor,
        trigger_dir: Path,
        verbose: bool = False,
        assertion_engine: Optional[AssertionEngine] = None
    ):
        """Initialize step executor.

        Args:
            process: Process to execute steps against
            sentinel_monitor: Sentinel monitoring system
            trigger_dir: Directory for screenshot triggers
            verbose: Enable verbose logging
            assertion_engine: Engine for running inline assertions
        """
        self.process = process
        self.sentinel_monitor = sentinel_monitor
        self.trigger_dir = trigger_dir
        self.verbose = verbose
        self.assertion_engine = assertion_engine or AssertionEngine(
            fail_fast=False,
            verbose=verbose
        )
        self._last_output: Optional[str] = None
        self._last_exit_code: Optional[int] = None

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[StepExecutor] {message}")

    async def execute_step(self, step: Step, default_timeout: float, step_index: int = 0) -> StepResult:
        """Execute a single step with assertion support.

        Args:
            step: Step to execute
            default_timeout: Default timeout if step doesn't specify
            step_index: Index of the step in the scenario

        Returns:
            StepResult with execution details and assertion results
        """
        start_time = time.time()
        result = StepResult(step_index=step_index)

        try:
            timeout = step.timeout or default_timeout

            if step.note:
                self._log(step.note)

            if step.expect:
                await self._handle_expect(step.expect, timeout)

            # Capture output before sending command
            before_output = self.process.before if hasattr(self.process, 'before') else None

            if step.control:
                self._log(f"Sending control: {step.control}")
                self.process.sendcontrol(step.control)
            elif step.send is not None:
                self._log(f"Sending{' (raw)' if step.raw else ''}: {step.send}")
                if step.raw:
                    self.process.send(step.send)
                else:
                    self.process.sendline(step.send)

            # Capture output after command
            # Give the process a moment to produce output
            await asyncio.sleep(0.1)

            # Collect output from process buffer
            captured_output = self._capture_output()
            self._last_output = captured_output
            result.output = captured_output

            if step.screenshot:
                await self._handle_screenshot(step.screenshot, timeout)

            # Run inline assertions if present
            if step.has_assertions:
                assertion_results = self._run_assertions(step, captured_output)
                result.assertion_results = assertion_results
                result.success = not result.has_assertion_failures

            result.duration = time.time() - start_time
            return result

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration = time.time() - start_time
            return result

    def _capture_output(self) -> str:
        """Capture output from process buffer.

        Returns:
            Captured output as string
        """
        try:
            # Get output from pexpect process
            if hasattr(self.process, 'before') and self.process.before:
                output = self.process.before
                if isinstance(output, bytes):
                    return output.decode('utf-8', errors='replace')
                return str(output)
            return ""
        except Exception as e:
            self._log(f"Error capturing output: {e}")
            return ""

    def _run_assertions(self, step: Step, output: str) -> List:
        """Run inline assertions for a step.

        Args:
            step: Step with assertions
            output: Captured output to validate

        Returns:
            List of AssertionResult objects
        """
        assertions = []

        # Build assertion objects from step fields
        if step.expect_output is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.OUTPUT,
                    expected=step.expect_output,
                    actual=output,
                )
            )

        if step.expect_code is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.CODE,
                    expected=step.expect_code,
                    actual=self._last_exit_code,
                )
            )

        if step.expect_contains is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.CONTAINS,
                    expected=step.expect_contains,
                    actual=output,
                )
            )

        if step.expect_regex is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.REGEX,
                    expected=step.expect_regex,
                    actual=output,
                )
            )

        if step.expect_lines is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.LINES,
                    expected=step.expect_lines,
                    actual=output,
                )
            )

        if step.expect_not_contains is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.NOT_CONTAINS,
                    expected=step.expect_not_contains,
                    actual=output,
                )
            )

        if step.expect_json is not None:
            assertions.append(
                Assertion(
                    assertion_type=AssertionType.JSON,
                    expected=step.expect_json,
                    actual=output,
                )
            )

        # Validate all assertions
        return self.assertion_engine.validate_all(assertions)

    async def _handle_expect(self, pattern: str, timeout: float) -> None:
        """Handle expect step with sentinel monitoring support."""
        # Check if this is a sentinel pattern
        if any(token in pattern for token in ("[PROMPT]", "[WIDGET]", r"\[PROMPT\]", r"\[WIDGET\]")):
            self._log(f"Waiting for sentinel pattern: {pattern}")

            # Normalize escapes
            clean_pattern = pattern.replace(r"\[", "[").replace(r"\]", "]")
            literal_pattern = re.escape(clean_pattern)

            # Wait for sentinel file
            found = await self.sentinel_monitor.wait_for(literal_pattern, timeout=timeout)

            if not found:
                raise TimeoutError(f"Sentinel pattern not found: {pattern}")
        else:
            # Normal pexpect expect
            self._log(f"Waiting for pexpect pattern: {pattern}")
            self.process.expect(pattern, timeout=timeout)

    async def _handle_screenshot(self, name: str, timeout: float) -> None:
        """Trigger screenshot capture via file trigger mechanism."""
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower()) or "screenshot"
        filename = slug if slug.endswith(".svg") else f"{slug}.svg"
        screenshot_path = Path.cwd() / "artifacts" / "screenshots" / filename

        self._log(f"Capturing screenshot: {filename}")
        self._log(f"Expected path: {screenshot_path}")

        # Create trigger file
        trigger_file = self.trigger_dir / f"{slug}.trigger"
        self._log(f"Creating trigger file: {trigger_file}")
        trigger_file.touch()

        # Wait for the screenshot to appear
        deadline = time.time() + timeout
        checks = 0

        while time.time() < deadline:
            checks += 1

            # Check if trigger was consumed
            if not trigger_file.exists():
                self._log(f"Trigger file consumed by app")

            # Check if screenshot exists
            if screenshot_path.exists():
                self._log(f"Screenshot saved: {screenshot_path} (after {checks} checks)")

                # Clean up trigger file if still exists
                if trigger_file.exists():
                    trigger_file.unlink()

                return

            if checks % 5 == 0:
                self._log(f"Still waiting for screenshot... (check #{checks})")

            await asyncio.sleep(0.2)

        self._log(f"ERROR: Screenshot not found after {checks} checks")

        # Clean up trigger file
        if trigger_file.exists():
            trigger_file.unlink()

        raise TimeoutError(f"Screenshot '{filename}' not created within {timeout} seconds")
