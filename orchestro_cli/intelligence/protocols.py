"""Protocol definitions for intelligence modules.

This module defines abstract interfaces (protocols) for pluggable components
in the intelligent test generation system.
"""

from typing import Protocol, Dict, Any, Optional
from pathlib import Path

from orchestro_cli.intelligence.models import AppKnowledge


class IndexSource(Protocol):
    """Protocol for sources that can index and analyze code.

    An IndexSource is responsible for extracting structural knowledge
    from source code, such as classes, methods, bindings, and navigation flows.

    Example implementations:
        - ASTAnalyzer: Analyzes Python AST
        - RuntimeInspector: Uses runtime introspection
        - HybridAnalyzer: Combines static and runtime analysis
    """

    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single source file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Dictionary containing extracted information such as:
                - classes: List of class definitions
                - imports: List of import statements
                - functions: List of function definitions
                - screens: List of screen classes (if applicable)

        Raises:
            FileNotFoundError: If the file doesn't exist
            SyntaxError: If the file contains invalid Python
        """
        ...

    async def analyze_project(self, root_path: Path) -> AppKnowledge:
        """Analyze an entire project directory.

        Args:
            root_path: Path to the project root directory

        Returns:
            AppKnowledge object containing complete application structure

        Raises:
            FileNotFoundError: If the root path doesn't exist
            ValueError: If no valid Python files found
        """
        ...

    def supports_framework(self, framework_name: str) -> bool:
        """Check if this analyzer supports a specific framework.

        Args:
            framework_name: Name of the framework (e.g., 'textual', 'click')

        Returns:
            True if the framework is supported
        """
        ...


class TestGenerator(Protocol):
    """Protocol for test generation strategies.

    A TestGenerator takes application knowledge and generates test scenarios
    in a specific format (e.g., Orchestro YAML, pytest, etc.).
    """

    async def generate_tests(
        self,
        knowledge: AppKnowledge,
        output_dir: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Path]:
        """Generate test scenarios from application knowledge.

        Args:
            knowledge: AppKnowledge object with application structure
            output_dir: Directory where test files should be written
            options: Optional configuration (e.g., coverage_level, test_style)

        Returns:
            Dictionary mapping test names to their file paths

        Raises:
            ValueError: If knowledge is insufficient for test generation
            IOError: If unable to write test files
        """
        ...

    def estimate_coverage(self, knowledge: AppKnowledge) -> float:
        """Estimate test coverage percentage for the given knowledge.

        Args:
            knowledge: AppKnowledge object

        Returns:
            Estimated coverage as a percentage (0.0 to 100.0)
        """
        ...


class InteractionRecorder(Protocol):
    """Protocol for recording live interactions with TUI applications.

    An InteractionRecorder captures user interactions and converts them
    into test scenarios, similar to Playwright's codegen functionality.
    """

    async def start_recording(
        self,
        app_path: Path,
        app_args: Optional[list] = None,
    ) -> None:
        """Start recording interactions with an application.

        Args:
            app_path: Path to the application to run
            app_args: Optional command-line arguments for the app

        Raises:
            RuntimeError: If recording is already active
        """
        ...

    async def stop_recording(self) -> AppKnowledge:
        """Stop recording and return captured knowledge.

        Returns:
            AppKnowledge object with recorded interactions

        Raises:
            RuntimeError: If recording is not active
        """
        ...

    def is_recording(self) -> bool:
        """Check if recording is currently active.

        Returns:
            True if recording is active
        """
        ...


class KnowledgeStore(Protocol):
    """Protocol for storing and retrieving application knowledge.

    A KnowledgeStore persists AppKnowledge objects for reuse across
    test generation sessions.
    """

    async def save(self, knowledge: AppKnowledge, key: str) -> None:
        """Save application knowledge to persistent storage.

        Args:
            knowledge: AppKnowledge object to save
            key: Unique identifier for this knowledge (e.g., app name + version)

        Raises:
            IOError: If unable to write to storage
        """
        ...

    async def load(self, key: str) -> Optional[AppKnowledge]:
        """Load application knowledge from storage.

        Args:
            key: Unique identifier for the knowledge to load

        Returns:
            AppKnowledge object if found, None otherwise
        """
        ...

    async def list_keys(self) -> list[str]:
        """List all stored knowledge keys.

        Returns:
            List of knowledge keys in storage
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete stored knowledge.

        Args:
            key: Unique identifier for the knowledge to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        ...
