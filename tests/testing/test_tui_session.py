"""Tests for TUISession class."""

import pytest
from pathlib import Path

from orchestro_cli.testing import TUISession, SessionConfig


class TestTUISessionBasics:
    """Test basic TUI session functionality."""

    def test_tui_session_inherits_shell(self, tui_session):
        """Test that TUI session has shell capabilities."""
        result = tui_session.execute("echo test")
        assert result.success
        assert "test" in result.output

    def test_launch_tui_marks_active(self, tui_session):
        """Test that launching TUI sets active flag."""
        assert not tui_session.tui_active

        # Launch a simple TUI app (cat with no args will wait for input)
        tui_session.launch_tui("cat", timeout=0.5)

        assert tui_session.tui_active
        assert tui_session.app_name == "cat"

        # Clean up
        tui_session.exit_tui()


class TestKeySimulation:
    """Test keyboard input simulation."""

    def test_send_regular_keys(self, tui_session):
        """Test sending regular characters."""
        tui_session.launch_tui("cat", timeout=0.5)

        # Send keys (cat will echo them)
        tui_session.send_keys("hello")

        # Exit
        tui_session.exit_tui()

        assert tui_session.tui_active is False

    def test_send_special_keys(self, tui_session):
        """Test sending special key sequences."""
        # This is tricky to test without a real TUI app
        # Just verify the parsing works
        keys = tui_session._parse_keys("hello<Enter>world<Tab>test")

        assert "hello" in "".join(keys)
        assert "<Enter>" in keys
        assert "<Tab>" in keys


class TestTUILifecycle:
    """Test TUI application lifecycle."""

    def test_launch_and_exit(self, tui_session):
        """Test launching and exiting TUI."""
        tui_session.launch_tui("cat", timeout=0.5)
        assert tui_session.tui_active

        result = tui_session.exit_tui()
        assert not tui_session.tui_active
        assert result.success

    def test_exit_tui_with_keys(self, tui_session):
        """Test exiting TUI with custom keys."""
        tui_session.launch_tui("cat", timeout=0.5)

        # Exit with Ctrl+D (EOF for cat)
        result = tui_session.exit_tui(exit_keys="\x04")
        assert not tui_session.tui_active

    def test_cannot_launch_twice(self, tui_session):
        """Test that launching twice raises error."""
        tui_session.launch_tui("cat", timeout=0.5)

        with pytest.raises(RuntimeError, match="TUI already active"):
            tui_session.launch_tui("cat", timeout=0.5)

        tui_session.exit_tui()

    def test_close_exits_active_tui(self, tui_session):
        """Test that closing session exits TUI."""
        tui_session.launch_tui("cat", timeout=0.5)
        assert tui_session.tui_active

        tui_session.close()

        assert not tui_session.tui_active
        assert not tui_session.is_alive()


class TestKeyParsing:
    """Test special key parsing."""

    def test_parse_regular_chars(self, tui_session):
        """Test parsing regular characters."""
        keys = tui_session._parse_keys("abc123")
        assert keys == ['a', 'b', 'c', '1', '2', '3']

    def test_parse_special_keys(self, tui_session):
        """Test parsing special key sequences."""
        keys = tui_session._parse_keys("a<Enter>b<Tab>c")
        assert keys == ['a', '<Enter>', 'b', '<Tab>', 'c']

    def test_parse_complex_sequence(self, tui_session):
        """Test parsing complex key sequences."""
        keys = tui_session._parse_keys("hello<Space>world<Enter>")
        assert '<Space>' in keys
        assert '<Enter>' in keys
        assert 'hello' in ''.join(keys)


class TestErrorHandling:
    """Test error handling in TUI sessions."""

    def test_exit_without_launch_raises(self, tui_session):
        """Test exiting without launching raises error."""
        with pytest.raises(RuntimeError, match="No TUI application active"):
            tui_session.exit_tui()

    def test_send_keys_without_launch_raises(self, tui_session):
        """Test sending keys without launch raises error."""
        with pytest.raises(RuntimeError, match="No TUI application active"):
            tui_session.send_keys("test")

    def test_dangerous_command_blocked(self, tui_session):
        """Test that dangerous commands are blocked."""
        with pytest.raises(ValueError, match="blocked"):
            tui_session.launch_tui("rm -rf /")


class TestScreenInteraction:
    """Test screen interaction methods."""

    def test_get_screen_requires_active_tui(self, tui_session):
        """Test that get_screen requires active TUI."""
        with pytest.raises(RuntimeError, match="No TUI application active"):
            tui_session.get_screen()

    def test_expect_screen_requires_active_tui(self, tui_session):
        """Test that expect_screen requires active TUI."""
        with pytest.raises(RuntimeError, match="No TUI application active"):
            tui_session.expect_screen("test")


@pytest.mark.asyncio
class TestScreenshotIntegration:
    """Test screenshot capture integration."""

    async def test_capture_screenshot_requires_tui(self, tui_session, trigger_dir, artifacts_dir):
        """Test that screenshot requires active TUI."""
        with pytest.raises(RuntimeError, match="No TUI application active"):
            await tui_session.capture_screenshot(
                "test",
                trigger_dir,
                artifacts_dir
            )

    async def test_screenshot_trigger_creation(self, tui_session, trigger_dir, artifacts_dir):
        """Test that screenshot creates trigger file."""
        tui_session.launch_tui("cat", timeout=0.5)

        try:
            # This will timeout since cat doesn't produce screenshots
            # but we can verify the trigger mechanism works
            await tui_session.capture_screenshot(
                "test-screenshot",
                trigger_dir,
                artifacts_dir,
                timeout=1.0
            )
        except TimeoutError as e:
            # Expected - just verify error message is correct
            assert "not created" in str(e)
        finally:
            tui_session.exit_tui()
