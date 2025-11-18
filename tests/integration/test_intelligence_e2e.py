"""End-to-end integration tests for the intelligence system."""

import pytest
import asyncio
import json
from pathlib import Path
from orchestro_cli.intelligence.indexing import ASTAnalyzer
from orchestro_cli.intelligence.generation import ScenarioGenerator
from orchestro_cli.intelligence.models import AppKnowledge


@pytest.fixture
def sample_app_path():
    """Path to the sample TUI application."""
    return Path(__file__).parent.parent.parent / "examples" / "sample_tui_app"


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory for tests."""
    return tmp_path / "generated_tests"


class TestIntelligenceSystemE2E:
    """End-to-end tests for the complete intelligence workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_analysis_to_generation(
        self, sample_app_path, output_dir
    ):
        """Test complete workflow: analyze → save → load → generate."""
        # Step 1: Analyze the sample app
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        # Verify analysis results
        assert knowledge is not None
        assert knowledge.project_path == sample_app_path
        assert len(knowledge.screens) >= 3  # At least MainMenu, Settings, Dashboard

        # Verify screens were discovered
        screen_names = set(knowledge.screens.keys())
        assert "MainMenuScreen" in screen_names
        assert "SettingsScreen" in screen_names
        assert "DashboardScreen" in screen_names

        # Verify entry screen was identified
        assert knowledge.entry_screen is not None
        assert knowledge.entry_screen in knowledge.screens

        # Step 2: Save knowledge to JSON
        output_dir.mkdir(parents=True, exist_ok=True)
        knowledge_file = output_dir / "knowledge.json"
        knowledge_file.write_text(json.dumps(knowledge.to_dict(), indent=2))

        assert knowledge_file.exists()
        assert knowledge_file.stat().st_size > 0

        # Step 3: Load knowledge from JSON
        loaded_data = json.loads(knowledge_file.read_text())
        loaded_knowledge = AppKnowledge.from_dict(loaded_data)

        assert len(loaded_knowledge.screens) == len(knowledge.screens)
        assert loaded_knowledge.entry_screen == knowledge.entry_screen

        # Step 4: Generate scenarios
        generator = ScenarioGenerator(loaded_knowledge)
        generated_files = generator.generate_all_tests(output_dir)

        # Verify generation
        assert len(generated_files) == 3  # Smoke, keybinding, navigation tests
        for file_path in generated_files:
            assert file_path.exists()
            assert file_path.suffix == ".yaml"
            assert file_path.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_ast_analyzer_discovers_screens(self, sample_app_path):
        """Test that AST analyzer correctly discovers all screens."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        # Verify screens
        assert "MainMenuScreen" in knowledge.screens
        assert "SettingsScreen" in knowledge.screens
        assert "DashboardScreen" in knowledge.screens

        # Verify screen details
        main_menu = knowledge.screens["MainMenuScreen"]
        assert main_menu.name == "MainMenuScreen"
        assert main_menu.class_name == "MainMenuScreen"
        assert main_menu.file_path.exists()
        assert len(main_menu.keybindings) > 0

    @pytest.mark.asyncio
    async def test_ast_analyzer_discovers_keybindings(self, sample_app_path):
        """Test that AST analyzer correctly discovers keybindings."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        main_menu = knowledge.screens["MainMenuScreen"]
        keybindings = {kb.key: kb for kb in main_menu.keybindings}

        # Verify specific keybindings from sample app
        assert "s" in keybindings
        assert keybindings["s"].action == "goto_settings"

        assert "d" in keybindings
        assert keybindings["d"].action == "goto_dashboard"

        assert "q" in keybindings
        assert keybindings["q"].action == "quit"

    @pytest.mark.asyncio
    async def test_ast_analyzer_discovers_widgets(self, sample_app_path):
        """Test that AST analyzer correctly discovers widgets."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        main_menu = knowledge.screens["MainMenuScreen"]

        # Verify widgets were discovered
        assert len(main_menu.widgets) > 0

        # Check for expected widget types (top-level only in current implementation)
        widget_types = {w.widget_type for w in main_menu.widgets}
        assert "Header" in widget_types
        assert "Footer" in widget_types
        assert "Container" in widget_types

        # Verify widget IDs for containers
        widget_ids = {w.widget_id for w in main_menu.widgets if w.widget_id}
        assert "main-menu" in widget_ids

    @pytest.mark.asyncio
    async def test_navigation_path_discovery(self, sample_app_path):
        """Test that navigation paths are discovered correctly."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        # Verify navigation paths were created
        assert len(knowledge.navigation_paths) > 0

        # Check for specific navigation path
        main_to_settings = knowledge.find_navigation_path(
            "MainMenuScreen", "settings"
        )
        assert main_to_settings is not None
        assert len(main_to_settings.steps) > 0

    @pytest.mark.asyncio
    async def test_smoke_test_generation(self, sample_app_path, output_dir):
        """Test smoke test scenario generation."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        generator = ScenarioGenerator(knowledge)
        yaml_content = generator.generate_smoke_test()

        # Verify YAML content
        assert yaml_content
        assert "name:" in yaml_content
        assert "Smoke Test" in yaml_content
        assert "steps:" in yaml_content
        assert "screenshot:" in yaml_content

        # Verify it's valid YAML
        import yaml
        scenario = yaml.safe_load(yaml_content)
        assert "name" in scenario
        assert "steps" in scenario
        assert len(scenario["steps"]) > 0

    @pytest.mark.asyncio
    async def test_keybinding_test_generation(self, sample_app_path, output_dir):
        """Test keybinding test scenario generation."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        generator = ScenarioGenerator(knowledge)
        yaml_content = generator.generate_keybinding_test()

        # Verify YAML content
        assert yaml_content
        assert "Keybinding Test" in yaml_content
        assert "keystroke:" in yaml_content

        # Verify it's valid YAML
        import yaml
        scenario = yaml.safe_load(yaml_content)
        assert len(scenario["steps"]) > 0

    @pytest.mark.asyncio
    async def test_navigation_test_generation(self, sample_app_path, output_dir):
        """Test navigation test scenario generation."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        generator = ScenarioGenerator(knowledge)
        yaml_content = generator.generate_navigation_test()

        # Verify YAML content
        assert yaml_content
        assert "Navigation Test" in yaml_content

        # Verify it's valid YAML
        import yaml
        scenario = yaml.safe_load(yaml_content)
        assert len(scenario["steps"]) > 0

    @pytest.mark.asyncio
    async def test_knowledge_serialization(self, sample_app_path):
        """Test that AppKnowledge can be serialized and deserialized."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        # Serialize to dict
        data = knowledge.to_dict()
        assert isinstance(data, dict)
        assert "screens" in data
        assert "project_path" in data

        # Deserialize from dict
        restored = AppKnowledge.from_dict(data)
        assert len(restored.screens) == len(knowledge.screens)
        assert restored.entry_screen == knowledge.entry_screen

        # Verify screen details are preserved
        for screen_name in knowledge.screens:
            original = knowledge.screens[screen_name]
            restored_screen = restored.screens[screen_name]

            assert original.name == restored_screen.name
            assert original.class_name == restored_screen.class_name
            assert len(original.keybindings) == len(restored_screen.keybindings)

    @pytest.mark.asyncio
    async def test_generated_yaml_is_valid_orchestro_scenario(
        self, sample_app_path, output_dir
    ):
        """Test that generated YAML files are valid Orchestro scenarios."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        generator = ScenarioGenerator(knowledge)
        generated_files = generator.generate_all_tests(output_dir)

        import yaml

        for test_file in generated_files:
            # Load and verify YAML structure
            content = yaml.safe_load(test_file.read_text())

            assert "name" in content
            assert "steps" in content
            assert isinstance(content["steps"], list)

            # Each step should have a name
            for step in content["steps"]:
                assert "name" in step or "comment" in step

            # Verify basic scenario structure is valid
            assert len(content["steps"]) > 0
            assert isinstance(content["name"], str)
            assert len(content["name"]) > 0

    @pytest.mark.asyncio
    async def test_analyzer_handles_nonexistent_path(self):
        """Test that analyzer handles nonexistent paths gracefully."""
        analyzer = ASTAnalyzer()
        nonexistent = Path("/tmp/nonexistent_directory_12345")

        # Should raise ValueError for nonexistent path
        with pytest.raises(ValueError, match="No Python files found"):
            await analyzer.analyze_project(nonexistent)

    @pytest.mark.asyncio
    async def test_multiple_screens_with_same_keybindings(self, sample_app_path):
        """Test handling of multiple screens with overlapping keybindings."""
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(sample_app_path)

        # Find keybindings that appear in multiple screens
        all_keys = {}
        for screen_name, screen in knowledge.screens.items():
            for kb in screen.keybindings:
                if kb.key not in all_keys:
                    all_keys[kb.key] = []
                all_keys[kb.key].append(screen_name)

        # Verify that common keys (like 'q' and 'escape') appear in multiple screens
        common_keys = {key: screens for key, screens in all_keys.items() if len(screens) > 1}
        assert len(common_keys) > 0  # At least some keys should be common
