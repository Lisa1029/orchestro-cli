"""Tests for SentinelMonitor."""

import asyncio
from pathlib import Path

import pytest

from orchestro_cli.sentinel_monitor import SentinelMonitor


class TestSentinelMonitor:
    """Tests for SentinelMonitor class."""

    @pytest.mark.asyncio
    async def test_init(self, sentinel_file: Path):
        """Test SentinelMonitor initialization."""
        monitor = SentinelMonitor(sentinel_file)

        assert monitor.sentinel_file == sentinel_file
        assert monitor.running is False
        assert monitor.lines == []

    @pytest.mark.asyncio
    async def test_start_stop(self, sentinel_file: Path):
        """Test starting and stopping monitor."""
        monitor = SentinelMonitor(sentinel_file)

        await monitor.start()
        assert monitor.running is True
        assert monitor.monitor_task is not None

        await monitor.stop()
        assert monitor.running is False

    @pytest.mark.asyncio
    async def test_clear(self, sentinel_file: Path):
        """Test clearing sentinel file."""
        sentinel_file.write_text("test content\n")

        monitor = SentinelMonitor(sentinel_file)
        monitor.clear()

        content = sentinel_file.read_text()
        assert content == ""
        assert monitor.lines == []

    @pytest.mark.asyncio
    async def test_wait_for_pattern_found(self, sentinel_file: Path):
        """Test waiting for pattern that exists."""
        monitor = SentinelMonitor(sentinel_file)

        # Write sentinel before waiting
        sentinel_file.write_text("[PROMPT] main_menu\n")

        found = await monitor.wait_for(r"\[PROMPT\] main_menu", timeout=2.0)
        assert found is True

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_pattern_timeout(self, sentinel_file: Path):
        """Test waiting for pattern that doesn't exist."""
        monitor = SentinelMonitor(sentinel_file)

        found = await monitor.wait_for(r"\[PROMPT\] missing", timeout=0.5)
        assert found is False

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_pattern_appears_later(self, sentinel_file: Path):
        """Test waiting for pattern that appears during wait."""
        monitor = SentinelMonitor(sentinel_file)

        async def write_delayed():
            await asyncio.sleep(0.3)
            with open(sentinel_file, "a") as f:
                f.write("[WIDGET] status_bar\n")

        # Start writing task
        write_task = asyncio.create_task(write_delayed())

        # Wait for pattern
        found = await monitor.wait_for(r"\[WIDGET\] status_bar", timeout=2.0)
        assert found is True

        await write_task
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_regex_pattern(self, sentinel_file: Path):
        """Test waiting for regex pattern."""
        monitor = SentinelMonitor(sentinel_file)

        sentinel_file.write_text("[PROMPT] screen_.*\n[PROMPT] screen_settings\n")

        found = await monitor.wait_for(r"\[PROMPT\] screen_\w+", timeout=2.0)
        assert found is True

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_any_patterns(self, sentinel_file: Path):
        """Test waiting for any of multiple patterns."""
        monitor = SentinelMonitor(sentinel_file)

        sentinel_file.write_text("[ERROR] something went wrong\n")

        found, matched = await monitor.wait_for_any([
            r"\[PROMPT\] main",
            r"\[ERROR\] .*",
            r"\[WIDGET\] test"
        ], timeout=2.0)

        assert found is True
        assert matched == r"\[ERROR\] .*"

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_any_timeout(self, sentinel_file: Path):
        """Test wait_for_any with timeout."""
        monitor = SentinelMonitor(sentinel_file)

        found, matched = await monitor.wait_for_any([
            r"\[PROMPT\] missing",
            r"\[WIDGET\] missing"
        ], timeout=0.5)

        assert found is False
        assert matched is None

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_get_all_sentinels(self, sentinel_file: Path):
        """Test retrieving all captured sentinel lines."""
        monitor = SentinelMonitor(sentinel_file)

        sentinel_file.write_text(
            "[PROMPT] main\n"
            "[WIDGET] status\n"
            "[PROMPT] settings\n"
        )

        await monitor.start()
        await asyncio.sleep(0.3)  # Let monitor read lines

        sentinels = monitor.get_all_sentinels()
        assert len(sentinels) >= 3

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_context_manager(self, sentinel_file: Path):
        """Test using monitor as async context manager."""
        sentinel_file.write_text("[PROMPT] test\n")

        monitor = SentinelMonitor(sentinel_file)
        async with monitor:
            assert monitor.running is True
            found = await monitor.wait_for(r"\[PROMPT\] test", timeout=1.0)
            assert found is True

        # Monitor should be stopped after context exit
        assert monitor.running is False

    @pytest.mark.asyncio
    async def test_monitor_large_file(self, sentinel_file: Path):
        """Test monitoring file with many lines (memory management)."""
        monitor = SentinelMonitor(sentinel_file)

        # Write 2000 lines (more than the 1000 line limit)
        lines = [f"[PROMPT] line_{i}\n" for i in range(2000)]
        sentinel_file.write_text("".join(lines))

        await monitor.start()
        await asyncio.sleep(0.5)  # Let monitor read

        # Should keep only last 1000 lines
        sentinels = monitor.get_all_sentinels()
        assert len(sentinels) <= 1000

        await monitor.stop()

    def test_cleanup_sync(self, sentinel_file: Path):
        """Test synchronous cleanup method."""
        monitor = SentinelMonitor(sentinel_file)
        monitor.running = True

        # Should not raise even without event loop
        monitor.cleanup()
