"""Non-blocking sentinel file monitoring for CLI Orchestro scenarios.

Provides tail -f style monitoring of sentinel files with async/await API
for integration with pexpect-based scenario runners. Supports pattern
matching, timeouts, and context manager cleanup.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


class SentinelMonitor:
    r"""Non-blocking file monitor for sentinel patterns.

    Monitors a sentinel file (typically /tmp/.vyb_orchestro_sentinels) for
    specific patterns like [PROMPT] identifier or [WIDGET] identifier.
    Works in parallel with pexpect for comprehensive scenario validation.

    Usage:
        monitor = SentinelMonitor("/tmp/.vyb_orchestro_sentinels")
        found = await monitor.wait_for(r"\[PROMPT\] main_menu", timeout=5.0)
        monitor.cleanup()

    Or with context manager:
        async with SentinelMonitor.create("/tmp/.vyb_orchestro_sentinels") as monitor:
            found = await monitor.wait_for(r"\[WIDGET\] status_bar")
    """

    def __init__(self, sentinel_file: str | Path = "/tmp/.vyb_orchestro_sentinels") -> None:
        """Initialize sentinel monitor.

        Args:
            sentinel_file: Path to sentinel file to monitor
        """
        self.sentinel_file = Path(sentinel_file)
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.lines: list[str] = []
        self.last_position = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start monitoring the sentinel file."""
        if self.running:
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        LOGGER.debug("Started sentinel monitor for %s", self.sentinel_file)

    async def stop(self) -> None:
        """Stop monitoring and cleanup."""
        if not self.running:
            return

        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None

        LOGGER.debug("Stopped sentinel monitor")

    def clear(self) -> None:
        """Clear sentinel file contents."""
        try:
            self.sentinel_file.write_text("", encoding="utf-8")
            self.lines = []
            self.last_position = 0
        except OSError:
            pass  # Best effort

    def cleanup(self) -> None:
        """Synchronous cleanup wrapper for compatibility."""
        if self.running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule cleanup but don't block
                    asyncio.create_task(self.stop())
                else:
                    loop.run_until_complete(self.stop())
            except RuntimeError:
                # No event loop, just mark as stopped
                self.running = False
                if self.monitor_task:
                    self.monitor_task.cancel()

    async def wait_for(self, pattern: str, timeout: float = 5.0) -> bool:
        r"""Wait for sentinel matching pattern.

        Args:
            pattern: Regex pattern to match (e.g., r"\[PROMPT\] main_menu")
            timeout: Maximum time to wait in seconds

        Returns:
            True if pattern found before timeout, False otherwise

        Example:
            # Wait for specific prompt sentinel
            found = await monitor.wait_for(r"\[PROMPT\] settings", timeout=3.0)

            # Wait for widget sentinel with specific identifier
            found = await monitor.wait_for(r"\[WIDGET\] file_tree_.*", timeout=5.0)
        """
        if not self.running:
            await self.start()

        compiled = re.compile(pattern)
        start_time = asyncio.get_event_loop().time()
        end_time = start_time + timeout
        poll_interval = 0.05  # Check every 50ms for faster response

        LOGGER.debug("Waiting for sentinel pattern: %s (timeout=%.1fs)", pattern, timeout)

        # Check existing lines first
        async with self._lock:
            for line in self.lines:
                if compiled.search(line):
                    LOGGER.info("Found sentinel pattern in existing lines: %s", line.strip())
                    return True

        # Poll for new lines
        while asyncio.get_event_loop().time() < end_time:
            await asyncio.sleep(poll_interval)

            async with self._lock:
                for line in self.lines:
                    if compiled.search(line):
                        LOGGER.info("Found sentinel pattern: %s", line.strip())
                        return True

        LOGGER.warning("Timeout waiting for sentinel pattern: %s", pattern)
        return False

    async def _monitor_loop(self) -> None:
        """Internal monitoring loop (runs in background task)."""
        try:
            while self.running:
                await self._read_new_lines()
                await asyncio.sleep(0.1)  # Poll every 100ms
        except asyncio.CancelledError:
            LOGGER.debug("Monitor loop cancelled")
            raise
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Error in monitor loop: %s", exc)

    async def _read_new_lines(self) -> None:
        """Read new lines from sentinel file since last position."""
        if not self.sentinel_file.exists():
            return

        try:
            # Read file asynchronously
            def _read() -> tuple[list[str], int]:
                with open(self.sentinel_file, "r", encoding="utf-8") as f:
                    f.seek(self.last_position)
                    new_content = f.read()
                    new_position = f.tell()
                    return new_content.splitlines(keepends=True), new_position

            new_lines, new_position = await asyncio.to_thread(_read)

            if new_lines:
                async with self._lock:
                    self.lines.extend(new_lines)
                    self.last_position = new_position
                    # Keep only last 1000 lines to prevent memory growth
                    if len(self.lines) > 1000:
                        self.lines = self.lines[-1000:]

                LOGGER.debug("Read %d new sentinel lines", len(new_lines))

        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Error reading sentinel file: %s", exc)

    @classmethod
    async def create(cls, sentinel_file: str | Path = "/tmp/.vyb_orchestro_sentinels") -> SentinelMonitor:
        r"""Create and start a monitor (for context manager usage).

        Example:
            async with SentinelMonitor.create() as monitor:
                found = await monitor.wait_for(r"\[PROMPT\] menu")
        """
        monitor = cls(sentinel_file)
        await monitor.start()
        return monitor

    async def __aenter__(self) -> SentinelMonitor:
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        """Context manager exit."""
        await self.stop()

    def get_all_sentinels(self) -> list[str]:
        """Get all collected sentinel lines (for debugging).

        Returns:
            List of all sentinel lines captured so far
        """
        return list(self.lines)

    async def wait_for_any(self, patterns: list[str], timeout: float = 5.0) -> tuple[bool, Optional[str]]:
        r"""Wait for any of multiple patterns.

        Args:
            patterns: List of regex patterns to match
            timeout: Maximum time to wait in seconds

        Returns:
            Tuple of (found, matched_pattern) where found is True if any pattern
            matched, and matched_pattern is the pattern that matched (or None)

        Example:
            found, pattern = await monitor.wait_for_any([
                r"\[PROMPT\] main_menu",
                r"\[PROMPT\] settings",
                r"\[ERROR\] .*"
            ], timeout=5.0)
            if found:
                print(f"Matched: {pattern}")
        """
        if not self.running:
            await self.start()

        compiled_patterns = [(p, re.compile(p)) for p in patterns]
        start_time = asyncio.get_event_loop().time()
        end_time = start_time + timeout
        poll_interval = 0.1

        LOGGER.debug("Waiting for any of %d patterns (timeout=%.1fs)", len(patterns), timeout)

        # Check existing lines first
        async with self._lock:
            for line in self.lines:
                for pattern, compiled in compiled_patterns:
                    if compiled.search(line):
                        LOGGER.info("Found sentinel pattern in existing lines: %s", line.strip())
                        return True, pattern

        # Poll for new lines
        while asyncio.get_event_loop().time() < end_time:
            await asyncio.sleep(poll_interval)

            async with self._lock:
                for line in self.lines:
                    for pattern, compiled in compiled_patterns:
                        if compiled.search(line):
                            LOGGER.info("Found sentinel pattern: %s", line.strip())
                            return True, pattern

        LOGGER.warning("Timeout waiting for any of %d patterns", len(patterns))
        return False, None
