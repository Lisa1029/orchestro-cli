"""Generate Orchestro test scenarios from application knowledge."""

from typing import List, Dict, Any
from pathlib import Path
import yaml

from orchestro_cli.intelligence.models import AppKnowledge, ScreenInfo


class ScenarioGenerator:
    """Generates Orchestro test scenarios based on discovered application structure."""

    def __init__(self, knowledge: AppKnowledge):
        self.knowledge = knowledge

    def generate_smoke_test(self) -> str:
        """
        Generate a smoke test that visits all screens and captures screenshots.

        Returns:
            YAML string containing the scenario
        """
        scenario = {
            "name": "Smoke Test - Visit All Screens",
            "description": "Automatically generated smoke test that visits all screens and captures screenshots",
            "steps": [],
        }

        # Add start step
        scenario["steps"].append({
            "name": "Start application",
            "command": f"python {self.knowledge.project_path}/app.py",
            "timeout": 5,
        })

        scenario["steps"].append({
            "name": "Wait for app to initialize",
            "wait": 1,
        })

        # Capture entry screen
        entry_screen = self.knowledge.entry_screen or "main"
        scenario["steps"].append({
            "name": f"Capture {entry_screen} screenshot",
            "screenshot": f"{entry_screen.lower()}_screen.png",
        })

        # Visit each screen
        visited = {entry_screen}
        for screen_name, screen in self.knowledge.screens.items():
            if screen_name in visited:
                continue

            # Find navigation path to this screen
            path = self.knowledge.find_navigation_path(entry_screen, screen_name)
            if not path:
                # Try from any visited screen
                for visited_screen in visited:
                    path = self.knowledge.find_navigation_path(visited_screen, screen_name)
                    if path:
                        break

            if path:
                # Navigate to screen
                for step in path.steps:
                    if step["type"] == "keybinding":
                        scenario["steps"].append({
                            "name": f"Navigate to {screen_name} using {step['action']}",
                            "keystroke": step["action"],
                        })
                    elif step["type"] == "button":
                        scenario["steps"].append({
                            "name": f"Navigate to {screen_name} via button",
                            "wait": 0.5,
                        })

                scenario["steps"].append({
                    "name": "Wait for screen transition",
                    "wait": 0.5,
                })

                scenario["steps"].append({
                    "name": f"Capture {screen_name} screenshot",
                    "screenshot": f"{screen_name.lower()}_screen.png",
                })

                visited.add(screen_name)

                # Navigate back
                scenario["steps"].append({
                    "name": f"Return from {screen_name}",
                    "keystroke": "escape",
                })

                scenario["steps"].append({
                    "name": "Wait for return",
                    "wait": 0.5,
                })

        # Quit application
        scenario["steps"].append({
            "name": "Quit application",
            "keystroke": "q",
        })

        scenario["steps"].append({
            "name": "Wait for shutdown",
            "wait": 1,
        })

        return yaml.dump(scenario, default_flow_style=False, sort_keys=False)

    def generate_keybinding_test(self) -> str:
        """
        Generate tests for all discovered keybindings.

        Returns:
            YAML string containing the scenario
        """
        scenario = {
            "name": "Keybinding Test - Verify All Shortcuts",
            "description": "Automatically generated test for all keybindings",
            "steps": [],
        }

        # Add start step
        scenario["steps"].append({
            "name": "Start application",
            "command": f"python {self.knowledge.project_path}/app.py",
            "timeout": 5,
        })

        scenario["steps"].append({
            "name": "Wait for app to initialize",
            "wait": 1,
        })

        # Test keybindings for each screen
        for screen_name, screen in self.knowledge.screens.items():
            if not screen.keybindings:
                continue

            scenario["steps"].append({
                "name": f"Testing keybindings for {screen_name}",
                "comment": f"Screen: {screen_name}",
            })

            for kb in screen.keybindings:
                # Skip quit keybindings for now
                if kb.action in ["quit", "app_quit"]:
                    continue

                scenario["steps"].append({
                    "name": f"Test {kb.key} -> {kb.description}",
                    "keystroke": kb.key,
                })

                scenario["steps"].append({
                    "name": "Wait for action",
                    "wait": 0.5,
                })

                scenario["steps"].append({
                    "name": f"Capture after {kb.key}",
                    "screenshot": f"{screen_name.lower()}_{kb.key.replace(' ', '_')}.png",
                })

                # Navigate back if we moved to another screen
                if kb.action.startswith("goto_") or kb.action.startswith("push_"):
                    scenario["steps"].append({
                        "name": "Return to previous screen",
                        "keystroke": "escape",
                    })
                    scenario["steps"].append({
                        "name": "Wait for return",
                        "wait": 0.5,
                    })

        # Quit application
        scenario["steps"].append({
            "name": "Quit application",
            "keystroke": "q",
        })

        scenario["steps"].append({
            "name": "Wait for shutdown",
            "wait": 1,
        })

        return yaml.dump(scenario, default_flow_style=False, sort_keys=False)

    def generate_navigation_test(self) -> str:
        """
        Generate tests for navigation paths.

        Returns:
            YAML string containing the scenario
        """
        scenario = {
            "name": "Navigation Test - Verify Screen Transitions",
            "description": "Automatically generated test for navigation paths",
            "steps": [],
        }

        # Add start step
        scenario["steps"].append({
            "name": "Start application",
            "command": f"python {self.knowledge.project_path}/app.py",
            "timeout": 5,
        })

        scenario["steps"].append({
            "name": "Wait for app to initialize",
            "wait": 1,
        })

        # Test each navigation path
        for path in self.knowledge.navigation_paths:
            scenario["steps"].append({
                "name": f"Navigate: {path.start_screen} → {path.end_screen}",
                "comment": f"Path cost: {path.cost}",
            })

            for step in path.steps:
                if step["type"] == "keybinding":
                    scenario["steps"].append({
                        "name": f"Press {step['action']}",
                        "keystroke": step["action"],
                    })
                elif step["type"] == "button":
                    scenario["steps"].append({
                        "name": f"Click button {step['action']}",
                        "wait": 0.5,
                    })

                scenario["steps"].append({
                    "name": "Wait for navigation",
                    "wait": 0.5,
                })

            scenario["steps"].append({
                "name": f"Verify {path.end_screen} reached",
                "screenshot": f"nav_{path.start_screen}_to_{path.end_screen}.png",
            })

            # Navigate back
            scenario["steps"].append({
                "name": "Return to start",
                "keystroke": "escape",
            })

            scenario["steps"].append({
                "name": "Wait for return",
                "wait": 0.5,
            })

        # Quit application
        scenario["steps"].append({
            "name": "Quit application",
            "keystroke": "q",
        })

        scenario["steps"].append({
            "name": "Wait for shutdown",
            "wait": 1,
        })

        return yaml.dump(scenario, default_flow_style=False, sort_keys=False)

    def generate_all_tests(self, output_dir: Path) -> List[Path]:
        """
        Generate all test scenarios and save to files.

        Args:
            output_dir: Directory to save generated tests

        Returns:
            List of paths to generated test files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Generate smoke test
        smoke_path = output_dir / "smoke_test.yaml"
        smoke_path.write_text(self.generate_smoke_test())
        generated_files.append(smoke_path)

        # Generate keybinding test
        keybinding_path = output_dir / "keybinding_test.yaml"
        keybinding_path.write_text(self.generate_keybinding_test())
        generated_files.append(keybinding_path)

        # Generate navigation test
        navigation_path = output_dir / "navigation_test.yaml"
        navigation_path.write_text(self.generate_navigation_test())
        generated_files.append(navigation_path)

        return generated_files
