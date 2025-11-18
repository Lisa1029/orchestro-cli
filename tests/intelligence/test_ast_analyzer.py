"""Tests for the AST analyzer module."""

import pytest
import tempfile
from pathlib import Path
from textwrap import dedent

from orchestro_cli.intelligence import ASTAnalyzer
from orchestro_cli.intelligence.models import AppKnowledge, ScreenInfo


class TestASTAnalyzer:
    """Test suite for ASTAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create an AST analyzer instance."""
        return ASTAnalyzer()

    @pytest.fixture
    def sample_textual_screen(self):
        """Sample Textual screen code."""
        return dedent("""
            from textual.app import App
            from textual.screen import Screen
            from textual.widgets import Button, Static
            from textual.binding import Binding

            class MainMenuScreen(Screen):
                '''Main menu screen for the application.'''

                BINDINGS = [
                    Binding("q", "quit", "Quit"),
                    Binding("s", "show_settings", "Settings"),
                    Binding("h", "show_help", "Help"),
                ]

                def compose(self):
                    yield Static("Welcome to My App", id="title")
                    yield Button("Start", id="btn-start")
                    yield Button("Settings", id="btn-settings")
                    yield Button("Quit", id="btn-quit")

                def action_quit(self):
                    self.app.exit()

                def action_show_settings(self):
                    self.app.push_screen("SettingsScreen")

                def action_show_help(self):
                    self.app.push_screen("HelpScreen")
        """)

    @pytest.fixture
    def sample_non_screen_class(self):
        """Sample non-screen class code."""
        return dedent("""
            class DataManager:
                '''Manages application data.'''

                def __init__(self):
                    self.data = {}

                def load_data(self):
                    pass
        """)

    @pytest.fixture
    def temp_project(self, sample_textual_screen):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_app"
            project_path.mkdir()

            # Create main screen file
            (project_path / "main_screen.py").write_text(sample_textual_screen)

            # Create settings screen file
            settings_code = dedent("""
                from textual.screen import Screen
                from textual.widgets import Static
                from textual.binding import Binding

                class SettingsScreen(Screen):
                    '''Settings screen.'''

                    BINDINGS = [
                        Binding("escape", "back", "Back"),
                    ]

                    def compose(self):
                        yield Static("Settings")

                    def action_back(self):
                        self.app.pop_screen()
            """)
            (project_path / "settings_screen.py").write_text(settings_code)

            yield project_path

    def test_supports_framework(self, analyzer):
        """Test framework support checking."""
        assert analyzer.supports_framework("textual") is True
        assert analyzer.supports_framework("Textual") is True
        assert analyzer.supports_framework("TEXTUAL") is True
        assert analyzer.supports_framework("click") is False
        assert analyzer.supports_framework("unknown") is False

    @pytest.mark.asyncio
    async def test_analyze_file_basic(self, analyzer, sample_textual_screen):
        """Test basic file analysis."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_textual_screen)
            f.flush()
            file_path = Path(f.name)

        try:
            result = await analyzer.analyze_file(file_path)

            assert result["file_path"] == str(file_path)
            assert result["framework"] == "textual"
            assert len(result["screens"]) == 1
            assert result["screens"][0]["name"] == "MainMenuScreen"
            assert result["screens"][0]["class_name"] == "MainMenuScreen"
        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self, analyzer):
        """Test file not found error."""
        with pytest.raises(FileNotFoundError):
            await analyzer.analyze_file(Path("/nonexistent/file.py"))

    @pytest.mark.asyncio
    async def test_analyze_file_syntax_error(self, analyzer):
        """Test handling of syntax errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("this is not valid python code def :")
            f.flush()
            file_path = Path(f.name)

        try:
            with pytest.raises(SyntaxError):
                await analyzer.analyze_file(file_path)
        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_analyze_file_non_screen(self, analyzer, sample_non_screen_class):
        """Test analyzing file with non-screen class."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_non_screen_class)
            f.flush()
            file_path = Path(f.name)

        try:
            result = await analyzer.analyze_file(file_path)

            assert result["framework"] is None
            assert len(result["screens"]) == 0
        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_analyze_project(self, analyzer, temp_project):
        """Test full project analysis."""
        knowledge = await analyzer.analyze_project(temp_project)

        assert isinstance(knowledge, AppKnowledge)
        assert knowledge.project_path == temp_project
        assert len(knowledge.screens) == 2

        # Check main menu screen
        assert "MainMenuScreen" in knowledge.screens
        main_screen = knowledge.screens["MainMenuScreen"]
        assert main_screen.class_name == "MainMenuScreen"
        assert len(main_screen.keybindings) == 3
        assert any(kb.key == "q" for kb in main_screen.keybindings)
        assert any(kb.action == "quit" for kb in main_screen.keybindings)

        # Check settings screen
        assert "SettingsScreen" in knowledge.screens
        settings_screen = knowledge.screens["SettingsScreen"]
        assert settings_screen.class_name == "SettingsScreen"
        assert len(settings_screen.keybindings) == 1
        assert settings_screen.keybindings[0].key == "escape"

    @pytest.mark.asyncio
    async def test_extract_keybindings(self, analyzer, temp_project):
        """Test keybinding extraction."""
        knowledge = await analyzer.analyze_project(temp_project)

        main_screen = knowledge.screens["MainMenuScreen"]

        # Check all keybindings are extracted
        assert len(main_screen.keybindings) == 3

        # Check keybinding details
        quit_binding = next(kb for kb in main_screen.keybindings if kb.key == "q")
        assert quit_binding.action == "quit"
        assert quit_binding.description == "Quit"

        settings_binding = next(kb for kb in main_screen.keybindings if kb.key == "s")
        assert settings_binding.action == "show_settings"
        assert settings_binding.description == "Settings"

    @pytest.mark.asyncio
    async def test_extract_widgets(self, analyzer, temp_project):
        """Test widget extraction."""
        knowledge = await analyzer.analyze_project(temp_project)

        main_screen = knowledge.screens["MainMenuScreen"]

        # Check widgets are extracted
        assert len(main_screen.widgets) == 4

        # Check widget types
        widget_types = {w.widget_type for w in main_screen.widgets}
        assert "Static" in widget_types
        assert "Button" in widget_types

        # Check widget IDs
        title_widget = next(
            (w for w in main_screen.widgets if w.widget_id == "title"), None
        )
        assert title_widget is not None
        assert title_widget.widget_type == "Static"

    @pytest.mark.asyncio
    async def test_extract_methods(self, analyzer, temp_project):
        """Test method extraction."""
        knowledge = await analyzer.analyze_project(temp_project)

        main_screen = knowledge.screens["MainMenuScreen"]

        # Check methods are extracted
        assert "compose" in main_screen.methods
        assert "action_quit" in main_screen.methods
        assert "action_show_settings" in main_screen.methods
        assert "action_show_help" in main_screen.methods

    @pytest.mark.asyncio
    async def test_extract_navigation_targets(self, analyzer, temp_project):
        """Test navigation target extraction."""
        knowledge = await analyzer.analyze_project(temp_project)

        main_screen = knowledge.screens["MainMenuScreen"]

        # Check navigation targets
        assert "SettingsScreen" in main_screen.navigation_targets
        assert "HelpScreen" in main_screen.navigation_targets

    @pytest.mark.asyncio
    async def test_determine_entry_screen(self, analyzer, temp_project):
        """Test entry screen determination."""
        knowledge = await analyzer.analyze_project(temp_project)

        # Entry screen should be detected (likely MainMenuScreen)
        assert knowledge.entry_screen is not None
        assert knowledge.entry_screen in knowledge.screens

    @pytest.mark.asyncio
    async def test_build_navigation_paths(self, analyzer, temp_project):
        """Test navigation path building."""
        knowledge = await analyzer.analyze_project(temp_project)

        # Should have navigation paths
        assert len(knowledge.navigation_paths) > 0

        # Check for specific navigation path
        settings_paths = [
            p for p in knowledge.navigation_paths
            if p.end_screen == "SettingsScreen"
        ]
        assert len(settings_paths) > 0

    @pytest.mark.asyncio
    async def test_empty_project(self, analyzer):
        """Test analyzing empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            with pytest.raises(ValueError, match="No Python files found"):
                await analyzer.analyze_project(project_path)

    @pytest.mark.asyncio
    async def test_project_with_non_python_files(self, analyzer):
        """Test project with non-Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create some non-Python files
            (project_path / "README.md").write_text("# Test Project")
            (project_path / "data.json").write_text('{"key": "value"}')

            with pytest.raises(ValueError, match="No Python files found"):
                await analyzer.analyze_project(project_path)

    @pytest.mark.asyncio
    async def test_nested_project_structure(self, analyzer):
        """Test analyzing project with nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "app"
            project_path.mkdir()

            # Create nested structure
            screens_dir = project_path / "screens"
            screens_dir.mkdir()

            screen_code = dedent("""
                from textual.screen import Screen
                from textual.binding import Binding

                class NestedScreen(Screen):
                    BINDINGS = [Binding("q", "quit", "Quit")]

                    def compose(self):
                        pass
            """)
            (screens_dir / "nested.py").write_text(screen_code)

            knowledge = await analyzer.analyze_project(project_path)

            assert len(knowledge.screens) == 1
            assert "NestedScreen" in knowledge.screens

    @pytest.mark.asyncio
    async def test_multiple_screens_in_one_file(self, analyzer):
        """Test analyzing file with multiple screen classes."""
        code = dedent("""
            from textual.screen import Screen

            class Screen1(Screen):
                def compose(self):
                    pass

            class Screen2(Screen):
                def compose(self):
                    pass

            class Screen3(Screen):
                def compose(self):
                    pass
        """)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            file_path = Path(f.name)

        try:
            result = await analyzer.analyze_file(file_path)

            assert len(result["screens"]) == 3
            screen_names = {s["name"] for s in result["screens"]}
            assert screen_names == {"Screen1", "Screen2", "Screen3"}
        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_app_knowledge_serialization(self, analyzer, temp_project):
        """Test AppKnowledge serialization/deserialization."""
        knowledge = await analyzer.analyze_project(temp_project)

        # Serialize
        data = knowledge.to_dict()

        assert isinstance(data, dict)
        assert "project_path" in data
        assert "screens" in data
        assert "navigation_paths" in data

        # Deserialize
        from orchestro_cli.intelligence.models import AppKnowledge
        restored = AppKnowledge.from_dict(data)

        assert restored.project_path == knowledge.project_path
        assert len(restored.screens) == len(knowledge.screens)
        assert len(restored.navigation_paths) == len(knowledge.navigation_paths)


class TestASTAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def analyzer(self):
        return ASTAnalyzer()

    @pytest.mark.asyncio
    async def test_screen_without_bindings(self, analyzer):
        """Test screen class without BINDINGS."""
        code = dedent("""
            from textual.screen import Screen

            class SimpleScreen(Screen):
                def compose(self):
                    pass
        """)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            file_path = Path(f.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir)
                (project_path / "screen.py").write_text(code)

                knowledge = await analyzer.analyze_project(project_path)

                assert len(knowledge.screens) == 1
                screen = knowledge.screens["SimpleScreen"]
                assert len(screen.keybindings) == 0
        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_screen_without_compose(self, analyzer):
        """Test screen class without compose method."""
        code = dedent("""
            from textual.screen import Screen

            class BarebonesScreen(Screen):
                pass
        """)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "screen.py").write_text(code)

            knowledge = await analyzer.analyze_project(project_path)

            assert len(knowledge.screens) == 1
            screen = knowledge.screens["BarebonesScreen"]
            assert len(screen.widgets) == 0

    @pytest.mark.asyncio
    async def test_invalid_binding_format(self, analyzer):
        """Test handling of invalid binding formats."""
        code = dedent("""
            from textual.screen import Screen

            class WeirdScreen(Screen):
                # Invalid BINDINGS format
                BINDINGS = "not a list"

                def compose(self):
                    pass
        """)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "screen.py").write_text(code)

            # Should not crash, just skip invalid bindings
            knowledge = await analyzer.analyze_project(project_path)

            assert len(knowledge.screens) == 1
            screen = knowledge.screens["WeirdScreen"]
            assert len(screen.keybindings) == 0
