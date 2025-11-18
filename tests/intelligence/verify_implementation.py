#!/usr/bin/env python
"""Verification script for AST Analyzer implementation.

This script demonstrates all required functionality of the AST Analyzer module.
"""

import asyncio
import tempfile
from pathlib import Path
from textwrap import dedent

from orchestro_cli.intelligence import (
    ASTAnalyzer,
    AppKnowledge,
    ScreenInfo,
    KeybindingInfo,
)


async def main():
    """Run verification tests."""
    print("=" * 80)
    print("AST Analyzer Implementation Verification")
    print("=" * 80)
    print()

    # Initialize analyzer
    analyzer = ASTAnalyzer()
    print("✓ ASTAnalyzer initialized")

    # Test 1: Framework support
    print("\n1. Testing framework support...")
    assert analyzer.supports_framework("textual") is True
    assert analyzer.supports_framework("click") is False
    print("   ✓ Framework detection works")

    # Test 2: Single file analysis
    print("\n2. Testing single file analysis...")
    sample_code = dedent("""
        from textual.screen import Screen
        from textual.binding import Binding

        class TestScreen(Screen):
            '''Test screen.'''
            BINDINGS = [
                Binding("q", "quit", "Quit"),
            ]

            def compose(self):
                pass

            def action_quit(self):
                pass
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_code)
        f.flush()
        file_path = Path(f.name)

    try:
        result = await analyzer.analyze_file(file_path)
        assert result["framework"] == "textual"
        assert len(result["screens"]) == 1
        assert result["screens"][0]["name"] == "TestScreen"
        print("   ✓ File analysis works")
    finally:
        file_path.unlink()

    # Test 3: Project analysis
    print("\n3. Testing project analysis...")
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_app"
        project_path.mkdir()

        # Create main screen
        main_screen = dedent("""
            from textual.screen import Screen
            from textual.binding import Binding
            from textual.widgets import Button, Static

            class MainScreen(Screen):
                BINDINGS = [
                    Binding("q", "quit", "Quit"),
                    Binding("h", "show_help", "Help"),
                ]

                def compose(self):
                    yield Static("Welcome", id="title")
                    yield Button("Help", id="btn-help")

                def action_quit(self):
                    self.app.exit()

                def action_show_help(self):
                    self.app.push_screen("HelpScreen")
        """)
        (project_path / "main.py").write_text(main_screen)

        # Create help screen
        help_screen = dedent("""
            from textual.screen import Screen

            class HelpScreen(Screen):
                def compose(self):
                    pass
        """)
        (project_path / "help.py").write_text(help_screen)

        # Analyze project
        knowledge = await analyzer.analyze_project(project_path)

        assert isinstance(knowledge, AppKnowledge)
        assert len(knowledge.screens) == 2
        assert "MainScreen" in knowledge.screens
        assert "HelpScreen" in knowledge.screens
        print("   ✓ Project analysis works")

        # Test 4: Keybinding extraction
        print("\n4. Testing keybinding extraction...")
        main_screen_obj = knowledge.screens["MainScreen"]
        assert len(main_screen_obj.keybindings) == 2
        quit_binding = next(
            kb for kb in main_screen_obj.keybindings if kb.key == "q"
        )
        assert quit_binding.action == "quit"
        assert quit_binding.description == "Quit"
        print("   ✓ Keybinding extraction works")

        # Test 5: Widget extraction
        print("\n5. Testing widget extraction...")
        assert len(main_screen_obj.widgets) == 2
        widget_types = {w.widget_type for w in main_screen_obj.widgets}
        assert "Static" in widget_types
        assert "Button" in widget_types
        print("   ✓ Widget extraction works")

        # Test 6: Method extraction
        print("\n6. Testing method extraction...")
        assert "compose" in main_screen_obj.methods
        assert "action_quit" in main_screen_obj.methods
        assert "action_show_help" in main_screen_obj.methods
        print("   ✓ Method extraction works")

        # Test 7: Navigation target extraction
        print("\n7. Testing navigation target extraction...")
        assert "HelpScreen" in main_screen_obj.navigation_targets
        print("   ✓ Navigation target extraction works")

        # Test 8: Entry screen detection
        print("\n8. Testing entry screen detection...")
        assert knowledge.entry_screen is not None
        assert knowledge.entry_screen in knowledge.screens
        print("   ✓ Entry screen detection works")

        # Test 9: Serialization
        print("\n9. Testing serialization...")
        data = knowledge.to_dict()
        assert "screens" in data
        assert "navigation_paths" in data

        restored = AppKnowledge.from_dict(data)
        assert len(restored.screens) == len(knowledge.screens)
        print("   ✓ Serialization works")

    # Test 10: Error handling
    print("\n10. Testing error handling...")

    # Non-existent file
    try:
        await analyzer.analyze_file(Path("/nonexistent/file.py"))
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        print("   ✓ FileNotFoundError handling works")

    # Empty project
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_path = Path(tmpdir)
        try:
            await analyzer.analyze_project(empty_path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No Python files found" in str(e)
            print("   ✓ Empty project handling works")

    # Syntax error
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("this is not valid python def :")
        f.flush()
        file_path = Path(f.name)

    try:
        await analyzer.analyze_file(file_path)
        assert False, "Should have raised SyntaxError"
    except SyntaxError:
        print("   ✓ SyntaxError handling works")
    finally:
        file_path.unlink()

    print()
    print("=" * 80)
    print("ALL VERIFICATION TESTS PASSED ✓")
    print("=" * 80)
    print()
    print("Summary:")
    print("  - ASTAnalyzer implements all required methods")
    print("  - File and project analysis working")
    print("  - Keybinding, widget, and method extraction working")
    print("  - Navigation target detection working")
    print("  - Entry screen detection working")
    print("  - Serialization/deserialization working")
    print("  - Error handling working")
    print()
    print("The AST Analyzer module is production-ready!")


if __name__ == "__main__":
    asyncio.run(main())
