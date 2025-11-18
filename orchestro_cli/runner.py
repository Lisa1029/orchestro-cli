"""Scenario-driven CLI harness using pexpect.

This module reads a YAML scenario describing menu navigation, inputs,
and validations, then drives a CLI application accordingly. Designed
to be repo-agnostic so other projects can reuse it by supplying a
scenario file.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import time

import pexpect
import yaml

try:
    from .sentinel_monitor import SentinelMonitor
    from .junit_reporter import JUnitReporter, ScenarioTestResult
except ImportError:
    from sentinel_monitor import SentinelMonitor
    from junit_reporter import JUnitReporter, ScenarioTestResult

if TYPE_CHECKING:
    from orchestro_cli.snapshot import SnapshotMode


@dataclass
class ScenarioStep:
    expect: Optional[str] = None
    send: Optional[str] = None
    control: Optional[str] = None
    note: Optional[str] = None
    timeout: Optional[float] = None
    raw: bool = False
    screenshot: Optional[str] = None


@dataclass
class Validation:
    type: str
    path: Optional[str] = None
    text: Optional[str] = None


class ScenarioRunner:
    """Executes CLI scenarios defined in YAML."""

    def __init__(
        self,
        scenario_path: Path,
        workspace: Optional[Path] = None,
        verbose: bool = False,
        junit_xml_path: Optional[Path] = None,
        snapshot_mode: Optional[SnapshotMode] = None,
        snapshot_dir: Optional[Path] = None,
        snapshot_interactive: bool = False,
    ) -> None:
        self.scenario_path = scenario_path.resolve()
        self.verbose = verbose
        self.workspace = workspace.resolve() if workspace else None
        self.junit_xml_path = junit_xml_path
        self.snapshot_mode = snapshot_mode
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else Path(".snapshots")
        self.snapshot_interactive = snapshot_interactive
        self.spec = self._load_spec()
        self.process: Optional[pexpect.spawn] = None
        # Initialize sentinel monitor with cross-platform temp directory
        temp_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro"
        temp_dir.mkdir(parents=True, exist_ok=True)
        sentinel_file = temp_dir / "sentinels"
        self.sentinel_monitor = SentinelMonitor(sentinel_file)
        # Store trigger directory
        self.trigger_dir = temp_dir / "screenshot_triggers"
        self.trigger_dir.mkdir(parents=True, exist_ok=True)

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[CLI Orchestro] {message}")

    def _load_spec(self) -> Dict[str, Any]:
        with open(self.scenario_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def _prepare_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        scenario_env = self.spec.get("env", {})
        env.update({str(k): str(v) for k, v in scenario_env.items()})
        if self.workspace:
            home = self.workspace / "home"
            data = self.workspace / "data"
            home.mkdir(parents=True, exist_ok=True)
            data.mkdir(parents=True, exist_ok=True)
            env["HOME"] = str(home)
            env["VYB_DATA_ROOT"] = str(data)

        # Enable automated screenshot monitoring
        env["VYB_AUTO_SCREENSHOT"] = "1"

        return env

    def _parse_steps(self) -> List[ScenarioStep]:
        steps: List[ScenarioStep] = []
        for raw in self.spec.get("steps", []):
            # Support both "expect" and "pattern" for compatibility
            expect_pattern = raw.get("expect") or raw.get("pattern")

            steps.append(
                ScenarioStep(
                    expect=expect_pattern,
                    send=raw.get("send"),
                    control=raw.get("control"),
                    note=raw.get("note"),
                    timeout=raw.get("timeout"),
                    raw=bool(raw.get("raw", False)),
                    screenshot=raw.get("screenshot"),
                )
            )
        return steps

    def _parse_validations(self) -> List[Validation]:
        validations: List[Validation] = []
        for raw in self.spec.get("validations", []):
            validations.append(
                Validation(
                    type=raw.get("type"),
                    path=raw.get("path"),
                    text=raw.get("text"),
                )
            )
        return validations

    def validate(self) -> Dict[str, Any]:
        """Validate scenario structure without executing.

        Returns:
            Dictionary with validation results containing:
                - valid: bool - overall validation status
                - errors: List[str] - validation errors
                - warnings: List[str] - validation warnings
        """
        errors = []
        warnings = []

        print(f"[DRY RUN] Validating scenario: {self.spec.get('name', 'Unnamed')}")
        if desc := self.spec.get('description'):
            print(f"[DRY RUN] Description: {desc}")

        # Validate command exists
        command = self.spec.get('command')
        if not command:
            errors.append("Scenario missing 'command' field")
            print("[DRY RUN] ❌ No command specified")
        else:
            # Handle both string and list commands
            if isinstance(command, str):
                import shlex
                cmd_parts = shlex.split(command)
            else:
                cmd_parts = command

            cmd_name = cmd_parts[0]
            print(f"[DRY RUN] Command: {' '.join(cmd_parts)}")

            # Check if command exists in PATH or is a file
            if cmd_name.startswith('./') or cmd_name.startswith('/'):
                # Relative or absolute path
                cmd_path = Path(cmd_name)
                if not cmd_path.exists():
                    warnings.append(f"Command file not found: {cmd_name}")
                    print(f"[DRY RUN] ⚠️  Command file not found: {cmd_name}")
                elif not os.access(cmd_path, os.X_OK):
                    warnings.append(f"Command file not executable: {cmd_name}")
                    print(f"[DRY RUN] ⚠️  Command file not executable: {cmd_name}")
                else:
                    print(f"[DRY RUN] ✓ Command file exists and is executable")
            else:
                # Check in PATH
                if shutil.which(cmd_name):
                    print(f"[DRY RUN] ✓ Command found in PATH")
                else:
                    warnings.append(f"Command not found in PATH: {cmd_name}")
                    print(f"[DRY RUN] ⚠️  Command '{cmd_name}' not found in PATH")

        # Validate timeout
        timeout = self.spec.get('timeout', 30)
        try:
            timeout_val = float(timeout)
            if timeout_val <= 0:
                errors.append(f"Timeout must be positive, got: {timeout}")
                print(f"[DRY RUN] ❌ Invalid timeout: {timeout}")
            else:
                print(f"[DRY RUN] Timeout: {timeout_val}s")
        except (ValueError, TypeError):
            errors.append(f"Invalid timeout value: {timeout}")
            print(f"[DRY RUN] ❌ Invalid timeout: {timeout}")

        # Validate environment variables
        env = self.spec.get('env', {})
        if env:
            print(f"[DRY RUN] Environment variables: {len(env)} defined")
            for key, value in env.items():
                if not isinstance(key, str):
                    errors.append(f"Environment variable key must be string: {key}")

        # Validate steps
        steps = self._parse_steps()
        print(f"[DRY RUN] Steps: {len(steps)} step(s)")

        for i, step in enumerate(steps, 1):
            step_desc = []

            if step.note:
                print(f"[DRY RUN]   {i}. Note: {step.note}")

            if step.expect:
                step_desc.append(f"Expect pattern: '{step.expect}'")
                # Validate regex pattern
                try:
                    re.compile(step.expect)
                except re.error as e:
                    errors.append(f"Step {i}: Invalid regex pattern '{step.expect}': {e}")
                    print(f"[DRY RUN]   {i}. ❌ Invalid expect pattern: '{step.expect}' - {e}")
                    continue

            if step.send is not None:
                step_desc.append(f"Send: '{step.send}'{' (raw)' if step.raw else ''}")

            if step.control:
                step_desc.append(f"Control: {step.control}")

            if step.screenshot:
                screenshot_name = step.screenshot
                if not screenshot_name.endswith('.svg'):
                    screenshot_name = f"{screenshot_name}.svg"
                step_desc.append(f"Screenshot: {screenshot_name}")

                # Validate screenshot name
                if not re.match(r'^[a-zA-Z0-9_-]+(?:\.svg)?$', step.screenshot):
                    warnings.append(f"Step {i}: Screenshot name contains special characters: '{step.screenshot}'")
                    print(f"[DRY RUN]   {i}. ⚠️  Screenshot name may contain invalid characters")

            if step.timeout:
                try:
                    step_timeout = float(step.timeout)
                    if step_timeout <= 0:
                        errors.append(f"Step {i}: Timeout must be positive, got: {step.timeout}")
                        print(f"[DRY RUN]   {i}. ❌ Invalid timeout: {step.timeout}")
                    else:
                        step_desc.append(f"timeout: {step_timeout}s")
                except (ValueError, TypeError):
                    errors.append(f"Step {i}: Invalid timeout value: {step.timeout}")
                    print(f"[DRY RUN]   {i}. ❌ Invalid timeout: {step.timeout}")

            if step_desc:
                print(f"[DRY RUN]   {i}. {', '.join(step_desc)}")

        # Validate validations
        validations = self._parse_validations()
        if validations:
            print(f"[DRY RUN] Validations: {len(validations)} rule(s)")

            for i, validation in enumerate(validations, 1):
                if validation.type == 'path_exists':
                    if not validation.path:
                        errors.append(f"Validation {i}: 'path_exists' requires 'path' field")
                        print(f"[DRY RUN]   {i}. ❌ path_exists missing 'path' field")
                    else:
                        # Check if path format is valid
                        try:
                            Path(validation.path)
                            print(f"[DRY RUN]   {i}. ✓ path_exists: {validation.path}")
                        except Exception as e:
                            errors.append(f"Validation {i}: Invalid path format: {validation.path}")
                            print(f"[DRY RUN]   {i}. ❌ Invalid path format: {validation.path}")

                elif validation.type == 'file_contains':
                    if not validation.path:
                        errors.append(f"Validation {i}: 'file_contains' requires 'path' field")
                        print(f"[DRY RUN]   {i}. ❌ file_contains missing 'path' field")
                    elif validation.text is None:
                        errors.append(f"Validation {i}: 'file_contains' requires 'text' field")
                        print(f"[DRY RUN]   {i}. ❌ file_contains missing 'text' field")
                    else:
                        # Validate regex pattern
                        try:
                            re.compile(validation.text)
                            print(f"[DRY RUN]   {i}. ✓ file_contains: {validation.path} ~ '{validation.text}'")
                        except re.error as e:
                            errors.append(f"Validation {i}: Invalid regex pattern '{validation.text}': {e}")
                            print(f"[DRY RUN]   {i}. ❌ Invalid regex pattern: {e}")

                else:
                    errors.append(f"Validation {i}: Unknown validation type: {validation.type}")
                    print(f"[DRY RUN]   {i}. ❌ Unknown validation type: {validation.type}")
        else:
            print("[DRY RUN] Validations: None defined")

        # Print summary
        print()
        if errors:
            print(f"[DRY RUN] ❌ Validation failed with {len(errors)} error(s):")
            for error in errors:
                print(f"[DRY RUN]   - {error}")

        if warnings:
            print(f"[DRY RUN] ⚠️  {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"[DRY RUN]   - {warning}")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }

    def run(self) -> None:
        """Run scenario synchronously (wraps async implementation)."""
        # Initialize test result tracking if JUnit XML is enabled
        test_result = None
        if self.junit_xml_path:
            scenario_name = self.spec.get("name", "Orchestro Test Scenario")
            test_result = ScenarioTestResult(scenario_name)
            test_result.start()

        try:
            # Run the scenario
            asyncio.run(self._run_async())

            # Mark as successful if no exception was raised
            if test_result:
                test_result.finish(success=True)

        except Exception as e:
            # Record failure
            if test_result:
                test_result.finish(success=False, error=e)
            raise

        finally:
            # Generate JUnit XML report if path is provided
            if test_result and self.junit_xml_path:
                reporter = JUnitReporter()
                reporter.add_test_suite(test_result.to_test_suite())
                reporter.generate_xml(self.junit_xml_path)

    async def _run_async(self) -> None:
        """Run scenario with async sentinel support."""
        command = self.spec.get("command")
        if not command:
            raise ValueError("Scenario missing 'command'")

        # Handle both string and list commands
        if isinstance(command, str):
            import shlex
            command = shlex.split(command)

        env = self._prepare_env()
        timeout = float(self.spec.get("timeout", 30))

        # Clear sentinel file before starting
        self.sentinel_monitor.clear()

        self._log(f"Spawning command: {' '.join(command)}")
        # Spawn with proper TTY dimensions for Textual apps
        self.process = pexpect.spawn(
            command[0],
            command[1:],
            env=env,
            encoding="utf-8",
            timeout=timeout,
            dimensions=(80, 120),  # rows, cols - give Textual enough space
            echo=False  # Don't echo input back
        )

        # Give Textual app time to initialize properly
        await asyncio.sleep(2)

        # Debug: Check if process is alive
        if not self.process.isalive():
            self._log(f"ERROR: Process died during initialization")
            self._log(f"Exit status: {self.process.exitstatus}")
            self._log(f"Signal status: {self.process.signalstatus}")
            raise RuntimeError("Process failed to start")

        self._log(f"Process is alive and ready")

        # Try to read any initial output
        try:
            before = self.process.before or ""
            after = self.process.after or ""
            if before or after:
                self._log(f"Initial output - Before: {before[:100] if before else 'None'}")
                self._log(f"Initial output - After: {after[:100] if after else 'None'}")
        except:
            pass

        steps = self._parse_steps()
        for step in steps:
            if step.note:
                self._log(step.note)
            if step.expect:
                await self._handle_expect(step.expect, step.timeout or timeout)
            if step.control:
                self._log(f"Sending control: {step.control}")
                self.process.sendcontrol(step.control)
            elif step.send is not None:
                self._log(f"Sending{' (raw)' if step.raw else ''}: {step.send}")
                if step.raw:
                    self.process.send(step.send)
                else:
                    self.process.sendline(step.send)

            if step.screenshot:
                await self._handle_screenshot(step.screenshot, step.timeout or timeout)

        # Read remainder
        try:
            self.process.expect(pexpect.EOF)
        except pexpect.exceptions.TIMEOUT:
            self._log("Process timed out waiting for EOF; continuing to validations")

        # Cleanup sentinel file
        self.sentinel_monitor.cleanup()

        self._run_validations(env)

    async def _handle_expect(self, pattern: str, timeout: float) -> None:
        """Handle expect step with sentinel monitoring support.

        Args:
            pattern: Pattern to match (pexpect or sentinel)
            timeout: Timeout in seconds
        """
        # Check if this is a sentinel pattern (escaped brackets in YAML)
        if any(token in pattern for token in ("[PROMPT]", "[WIDGET]", r"\[PROMPT\]", r"\[WIDGET\]")):
            self._log(f"Waiting for sentinel pattern: {pattern}")

            # Normalize escapes
            clean_pattern = pattern.replace(r"\[", "[").replace(r"\]", "]")
            literal_pattern = re.escape(clean_pattern)

            # Wait for sentinel file
            start_time = time.time()
            found = await self.sentinel_monitor.wait_for(literal_pattern, timeout=timeout)
            end_time = time.time()

            self._append_runlog({
                "event": "sentinel_wait",
                "pattern": clean_pattern,
                "result": "found" if found else "timeout",
                "timeout_s": timeout,
                "latency_s": round(end_time - start_time, 3)
            })

            if not found:
                raise TimeoutError(f"Sentinel pattern not found: {pattern}")
        else:
            # Normal pexpect expect
            self._log(f"Waiting for pexpect pattern: {pattern}")
            self.process.expect(pattern, timeout=timeout)

    def _run_validations(self, env: Dict[str, str]) -> None:
        validations = self._parse_validations()
        # Use workspace if set, otherwise use current directory
        base_dir = Path(self.workspace or Path.cwd())
        for validation in validations:
            if validation.type == "path_exists":
                if not validation.path:
                    raise ValueError("path_exists validation requires 'path'")

                # If path is absolute or starts with known dirs, use it as-is
                val_path = Path(validation.path)
                if val_path.is_absolute() or str(validation.path).startswith(("artifacts/", "tmp/", ".")):
                    target = Path.cwd() / validation.path if not val_path.is_absolute() else val_path
                else:
                    target = base_dir / validation.path

                if not target.exists():
                    raise AssertionError(f"Expected path to exist: {target}")
            elif validation.type == "file_contains":
                if not validation.path or validation.text is None:
                    raise ValueError("file_contains validation requires 'path' and 'text'")
                target = base_dir / validation.path
                if not target.exists():
                    raise AssertionError(f"Expected file for content check: {target}")
                content = target.read_text(encoding="utf-8")
                if not re.search(validation.text, content):
                    raise AssertionError(f"Text '{validation.text}' not found in {target}")
            else:
                raise ValueError(f"Unknown validation type: {validation.type}")

    async def _handle_screenshot(self, name: str, timeout: float) -> None:
        """Trigger in-app screenshot capture via file trigger mechanism."""
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower()) or "screenshot"
        filename = slug if slug.endswith(".svg") else f"{slug}.svg"
        screenshot_path = Path.cwd() / "artifacts" / "screenshots" / filename

        self._log(f"Capturing screenshot: {filename}")
        self._log(f"Expected path: {screenshot_path}")

        # Use the cross-platform trigger directory
        self._log(f"Creating trigger file: {self.trigger_dir / f'{slug}.trigger'}")
        trigger_file = self.trigger_dir / f"{slug}.trigger"
        trigger_file.touch()

        # Wait for the screenshot to appear
        start_time = time.time()
        deadline = time.time() + timeout
        checks = 0
        while time.time() < deadline:
            checks += 1

            # Check if trigger was consumed (app processed it)
            if not trigger_file.exists():
                self._log(f"Trigger file consumed by app")

            # Check if screenshot exists
            if screenshot_path.exists():
                end_time = time.time()
                self._log(f"Screenshot saved: {screenshot_path} (after {checks} checks)")

                # Clean up trigger file if still exists
                if trigger_file.exists():
                    trigger_file.unlink()

                self._append_runlog({"event": "screenshot", "name": filename, "trigger_created_at": start_time, "artifact_detected_at": end_time, "latency_s": round(end_time - start_time, 3)})
                return

            if checks % 5 == 0:  # Log every 5 checks (1 second)
                self._log(f"Still waiting for screenshot... (check #{checks})")

            await asyncio.sleep(0.2)

        self._log(f"ERROR: Screenshot not found after {checks} checks")
        self._log(f"Listing artifacts/screenshots:")
        try:
            import os
            for f in os.listdir("artifacts/screenshots"):
                self._log(f"  Found: {f}")
        except Exception as e:
            self._log(f"  Could not list directory: {e}")

        # Clean up trigger file
        if trigger_file.exists():
            trigger_file.unlink()

        raise TimeoutError(f"Screenshot '{filename}' not created within {timeout} seconds")

    def _append_runlog(self, payload: Dict[str, Any]) -> None:
        try:
            with open("runlog.jsonl", "a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
        except OSError:
            pass
