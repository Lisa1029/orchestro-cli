#!/usr/bin/env python3
"""
Demonstrate Orchestro's Intelligent Test Generation

This script shows the complete workflow:
1. Analyze a Textual TUI app to discover its structure
2. Generate test scenarios automatically
3. (Optional) Execute the generated tests

Usage:
    python examples/demo_intelligence.py [--execute]
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestro_cli.intelligence.indexing import ASTAnalyzer
from orchestro_cli.intelligence.generation import ScenarioGenerator


def print_banner(text: str, char: str = "=") -> None:
    """Print a formatted banner."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"📍 {title}")
    print(f"{'─' * 80}\n")


async def main() -> None:
    """Run the intelligence demo."""
    execute_tests = "--execute" in sys.argv

    print_banner("🧠 Orchestro Intelligence System Demonstration", "=")
    print("This demo shows how Orchestro can automatically analyze a TUI app")
    print("and generate comprehensive test scenarios.\n")

    # Paths
    project_root = Path(__file__).parent.parent
    sample_app_path = project_root / "examples" / "sample_tui_app"
    output_path = project_root / "examples" / "generated_tests"
    knowledge_file = output_path / "app_knowledge.json"

    print(f"📂 Sample App: {sample_app_path}")
    print(f"📂 Output Dir: {output_path}")
    print()

    # Step 1: Analyze the application
    print_section("STEP 1: Analyzing TUI Application")
    print("🔍 Scanning Python files for Textual components...")

    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(sample_app_path)

    print(f"\n✅ Analysis Complete!\n")
    print(f"📊 Discovery Results:")
    print(f"   • Total Screens: {len(knowledge.screens)}")
    print(f"   • Entry Screen: {knowledge.entry_screen}")
    print(f"   • Navigation Paths: {len(knowledge.navigation_paths)}")

    # Display screen details
    print(f"\n🖥️  Discovered Screens:")
    for screen_name, screen in knowledge.screens.items():
        print(f"\n   {screen_name}:")
        print(f"      Class: {screen.class_name}")
        print(f"      File: {screen.file_path.name}")
        print(f"      Keybindings: {len(screen.keybindings)}")

        if screen.keybindings:
            for kb in screen.keybindings:
                print(f"         • {kb.key:10} → {kb.description}")

        print(f"      Widgets: {len(screen.widgets)}")
        widget_types = {}
        for widget in screen.widgets:
            widget_types[widget.widget_type] = widget_types.get(widget.widget_type, 0) + 1

        for widget_type, count in widget_types.items():
            print(f"         • {count}× {widget_type}")

        if screen.navigation_targets:
            print(f"      Navigation Targets: {', '.join(screen.navigation_targets)}")

    # Display navigation paths
    if knowledge.navigation_paths:
        print(f"\n🗺️  Navigation Paths:")
        for path in knowledge.navigation_paths:
            print(f"\n   {path.start_screen} → {path.end_screen} (cost: {path.cost})")
            for step in path.steps:
                print(f"      • {step['type']}: {step['action']} → {step['target']}")

    # Save knowledge to JSON
    print_section("STEP 2: Saving Application Knowledge")
    output_path.mkdir(parents=True, exist_ok=True)
    knowledge_file.write_text(json.dumps(knowledge.to_dict(), indent=2))
    print(f"💾 Saved to: {knowledge_file}")

    # Step 2: Generate test scenarios
    print_section("STEP 3: Generating Test Scenarios")
    print("🎭 Creating test scenarios based on discovered structure...")

    generator = ScenarioGenerator(knowledge)

    # Generate all test types
    print("\n📝 Generating:")
    print("   1. Smoke Test (visit all screens)")
    print("   2. Keybinding Test (verify all shortcuts)")
    print("   3. Navigation Test (test screen transitions)")

    generated_files = generator.generate_all_tests(output_path)

    print(f"\n✅ Generated {len(generated_files)} test files:\n")
    for file_path in generated_files:
        file_size = file_path.stat().st_size
        print(f"   📄 {file_path.name} ({file_size} bytes)")

        # Show preview of first scenario
        if file_path.name == "smoke_test.yaml":
            content = file_path.read_text()
            lines = content.split('\n')
            print("\n   Preview (first 15 lines):")
            for line in lines[:15]:
                print(f"      {line}")
            if len(lines) > 15:
                print(f"      ... ({len(lines) - 15} more lines)")

    # Step 3: Execute tests (optional)
    if execute_tests:
        print_section("STEP 4: Executing Generated Tests")
        print("⚠️  Note: Test execution requires the sample app dependencies")
        print("         Run 'pip install textual' if not already installed\n")

        try:
            import subprocess

            for test_file in generated_files:
                print(f"\n🧪 Running: {test_file.name}")
                print(f"{'─' * 60}")

                # Note: This would need the orchestro CLI to be properly installed
                # For demo purposes, we just show what would be run
                cmd = f"orchestro {test_file} --verbose"
                print(f"Command: {cmd}")
                print("\n(Skipping execution in demo mode)")
                print("To run manually: pip install textual && orchestro " + str(test_file))

        except Exception as e:
            print(f"⚠️  Could not execute tests: {e}")
            print("This is normal if Orchestro is not installed or sample app deps missing")
    else:
        print_section("STEP 4: Test Execution (Skipped)")
        print("💡 To execute the generated tests, run:")
        print(f"   python {__file__} --execute")
        print("\nOr run manually:")
        for test_file in generated_files:
            print(f"   orchestro {test_file}")

    # Summary
    print_banner("✨ Demo Complete!", "=")
    print("The Orchestro Intelligence System successfully:")
    print(f"   ✅ Analyzed {len(knowledge.screens)} screens")
    print(f"   ✅ Discovered {sum(len(s.keybindings) for s in knowledge.screens.values())} keybindings")
    print(f"   ✅ Mapped {len(knowledge.navigation_paths)} navigation paths")
    print(f"   ✅ Generated {len(generated_files)} test scenarios")
    print()
    print("📁 All generated files are in:")
    print(f"   {output_path}")
    print()
    print("🚀 Next Steps:")
    print("   1. Review the generated test scenarios")
    print("   2. Customize scenarios as needed")
    print("   3. Run tests with: orchestro <scenario_file.yaml>")
    print("   4. Integrate into your CI/CD pipeline")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
