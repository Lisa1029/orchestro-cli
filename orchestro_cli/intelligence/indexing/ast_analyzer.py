"""AST-based analyzer for discovering TUI application structure."""

import ast
from pathlib import Path
from typing import Optional, List
import logging

from orchestro_cli.intelligence.models import (
    AppKnowledge,
    ScreenInfo,
    KeybindingInfo,
    WidgetInfo,
)

logger = logging.getLogger(__name__)


class ASTAnalyzer:
    """Analyzes Python source code to discover TUI application structure.

    This analyzer implements the IndexSource protocol and provides static analysis
    of Textual TUI applications using Python's AST module.

    Example:
        ```python
        analyzer = ASTAnalyzer()
        knowledge = await analyzer.analyze_project(Path("./my_tui_app"))
        print(f"Found {len(knowledge.screens)} screens")
        ```
    """

    def __init__(self):
        self.knowledge: Optional[AppKnowledge] = None

    def supports_framework(self, framework_name: str) -> bool:
        """Check if this analyzer supports a specific framework.

        Args:
            framework_name: Name of the framework (e.g., 'textual')

        Returns:
            True if framework is supported
        """
        return framework_name.lower() == "textual"

    async def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single Python source file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Dictionary containing:
                - screens: List of screen class information
                - imports: List of import statements
                - framework: Detected framework (if any)

        Raises:
            FileNotFoundError: If file doesn't exist
            SyntaxError: If file contains invalid Python syntax
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.debug(f"Analyzing file: {file_path}")

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise

        # Extract information from AST
        result = {
            "file_path": str(file_path),
            "screens": [],
            "imports": [],
            "framework": None,
        }

        # Detect framework
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if self._is_textual_import(node):
                    result["framework"] = "textual"

        # Find screen classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = [
                    base.id if isinstance(base, ast.Name) else str(base)
                    for base in node.bases
                ]

                if any("Screen" in name for name in base_names):
                    result["screens"].append({
                        "name": node.name,
                        "class_name": node.name,
                        "line_number": node.lineno,
                    })

        return result

    def _is_textual_import(self, node) -> bool:
        """Check if an import statement imports from textual."""
        if isinstance(node, ast.Import):
            return any("textual" in alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            return node.module and "textual" in node.module
        return False

    async def analyze_project(self, project_path: Path) -> AppKnowledge:
        """
        Analyze a TUI project to discover screens, keybindings, and navigation.

        Args:
            project_path: Path to the project directory

        Returns:
            AppKnowledge object containing discovered information
        """
        self.knowledge = AppKnowledge(project_path=project_path)

        # Find all Python files
        python_files = list(project_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to analyze")

        if not python_files:
            raise ValueError(f"No Python files found in {project_path}")

        for py_file in python_files:
            await self._analyze_file(py_file)

        # Determine entry screen
        self._determine_entry_screen()

        # Build navigation paths
        self._build_navigation_paths()

        return self.knowledge

    async def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for TUI components."""
        try:
            source = file_path.read_text()
            tree = ast.parse(source, filename=str(file_path))

            # Find all class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    await self._analyze_class(node, file_path)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    async def _analyze_class(self, class_node: ast.ClassDef, file_path: Path) -> None:
        """Analyze a class definition to extract screen information."""
        # Check if this is a Screen subclass
        base_names = [
            base.id if isinstance(base, ast.Name) else str(base)
            for base in class_node.bases
        ]

        if not any("Screen" in name for name in base_names):
            return

        logger.debug(f"Found Screen class: {class_node.name}")

        screen = ScreenInfo(
            name=class_node.name,
            class_name=class_node.name,
            file_path=file_path,
        )

        # Extract keybindings
        screen.keybindings = self._extract_keybindings(class_node)

        # Extract widgets from compose method
        screen.widgets = self._extract_widgets(class_node)

        # Extract method names
        screen.methods = self._extract_methods(class_node)

        # Extract navigation targets
        screen.navigation_targets = self._extract_navigation_targets(class_node)

        self.knowledge.add_screen(screen)

    def _extract_keybindings(self, class_node: ast.ClassDef) -> List[KeybindingInfo]:
        """Extract keybindings from BINDINGS class variable."""
        keybindings = []

        for node in class_node.body:
            # Look for BINDINGS assignment
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "BINDINGS":
                        # Parse the list of Binding objects
                        if isinstance(node.value, ast.List):
                            for binding in node.value.elts:
                                kb = self._parse_binding(binding)
                                if kb:
                                    keybindings.append(kb)

        return keybindings

    def _parse_binding(self, binding_node: ast.expr) -> Optional[KeybindingInfo]:
        """Parse a Binding() call to extract keybinding information."""
        if not isinstance(binding_node, ast.Call):
            return None

        # Extract arguments
        args = binding_node.args
        kwargs = {kw.arg: kw.value for kw in binding_node.keywords}

        if len(args) < 2:
            return None

        # Get key (first arg)
        key = self._get_string_value(args[0])
        # Get action (second arg)
        action = self._get_string_value(args[1])
        # Get description (third arg or 'description' kwarg)
        description = ""
        if len(args) > 2:
            description = self._get_string_value(args[2])
        elif "description" in kwargs:
            description = self._get_string_value(kwargs["description"])

        # Get show flag
        show = True
        if "show" in kwargs:
            show = self._get_bool_value(kwargs["show"])

        if key and action:
            return KeybindingInfo(
                key=key,
                action=action,
                description=description or action,
                show_in_footer=show,
            )

        return None

    def _extract_widgets(self, class_node: ast.ClassDef) -> List[WidgetInfo]:
        """Extract widgets from compose method."""
        widgets = []

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == "compose":
                # Walk through the function body
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Yield):
                        widget = self._parse_widget(stmt.value.value)
                        if widget:
                            widgets.append(widget)

        return widgets

    def _parse_widget(self, widget_node: ast.expr) -> Optional[WidgetInfo]:
        """Parse a widget instantiation to extract widget information."""
        if not isinstance(widget_node, ast.Call):
            return None

        # Get widget type from function name
        widget_type = ""
        if isinstance(widget_node.func, ast.Name):
            widget_type = widget_node.func.id
        elif isinstance(widget_node.func, ast.Attribute):
            widget_type = widget_node.func.attr

        if not widget_type:
            return None

        # Extract widget ID from kwargs
        widget_id = None
        attributes = {}

        for kw in widget_node.keywords:
            if kw.arg == "id":
                widget_id = self._get_string_value(kw.value)
            else:
                # Store other attributes
                value = self._get_value(kw.value)
                if value is not None:
                    attributes[kw.arg] = str(value)

        return WidgetInfo(
            widget_type=widget_type,
            widget_id=widget_id,
            attributes=attributes,
        )

    def _extract_methods(self, class_node: ast.ClassDef) -> List[str]:
        """Extract method names from class."""
        methods = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)
        return methods

    def _extract_navigation_targets(self, class_node: ast.ClassDef) -> set:
        """Extract navigation targets (screens referenced in methods)."""
        targets = set()

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                # Look for push_screen and pop_screen calls
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Call):
                        # Check for push_screen
                        if isinstance(stmt.func, ast.Attribute):
                            if stmt.func.attr == "push_screen" and stmt.args:
                                screen_name = self._get_string_value(stmt.args[0])
                                if screen_name:
                                    targets.add(screen_name)

        return targets

    def _get_string_value(self, node: ast.expr) -> Optional[str]:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        return None

    def _get_bool_value(self, node: ast.expr) -> bool:
        """Extract boolean value from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        elif isinstance(node, ast.NameConstant):  # Python 3.7 compatibility
            return bool(node.value)
        return True

    def _get_value(self, node: ast.expr) -> Optional[str]:
        """Extract any value from AST node as string."""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, (ast.Str, ast.Num)):
            return str(node.s if isinstance(node, ast.Str) else node.n)
        return None

    def _determine_entry_screen(self) -> None:
        """Determine the entry screen of the application."""
        # Simple heuristic: look for "MainMenu", "Main", or the first screen
        for name in ["MainMenuScreen", "MainScreen", "MenuScreen"]:
            if name in self.knowledge.screens:
                self.knowledge.entry_screen = name
                return

        # Fallback to first screen
        if self.knowledge.screens:
            self.knowledge.entry_screen = next(iter(self.knowledge.screens.keys()))

    def _build_navigation_paths(self) -> None:
        """Build navigation paths between screens."""
        # Simple implementation: direct navigation only
        for screen_name, screen in self.knowledge.screens.items():
            for target in screen.navigation_targets:
                # Create a path for each navigation target
                from orchestro_cli.intelligence.models import NavigationPath
                path = NavigationPath(
                    start_screen=screen_name,
                    end_screen=target,
                )

                # Find the action that leads to this target
                for kb in screen.keybindings:
                    if target.lower() in kb.action.lower() or target.lower() in kb.description.lower():
                        path.add_step("keybinding", kb.key, target)
                        break
                else:
                    # No keybinding found, assume button click
                    path.add_step("button", f"btn-{target.lower()}", target)

                self.knowledge.navigation_paths.append(path)

    def _find_screen_classes(self, tree: ast.Module, file_path: Path) -> List[ScreenInfo]:
        """Find all screen classes in an AST (helper method for external use).

        Args:
            tree: Parsed AST module
            file_path: Path to the source file

        Returns:
            List of ScreenInfo objects
        """
        screens = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # Check if class inherits from a Textual screen base
            base_names = [
                base.id if isinstance(base, ast.Name) else str(base)
                for base in node.bases
            ]

            if not any("Screen" in name for name in base_names):
                continue

            # Create screen info
            screen = ScreenInfo(
                name=node.name,
                class_name=node.name,
                file_path=file_path,
            )

            # Extract keybindings
            screen.keybindings = self._extract_keybindings(node)

            # Extract widgets
            screen.widgets = self._extract_widgets(node)

            # Extract methods
            screen.methods = self._extract_methods(node)

            # Extract navigation targets
            screen.navigation_targets = self._extract_navigation_targets(node)

            screens.append(screen)

        return screens

    def _analyze_compose_method(self, class_node: ast.ClassDef) -> List[WidgetInfo]:
        """Analyze the compose method to extract widget structure (alias for _extract_widgets).

        Args:
            class_node: AST ClassDef node

        Returns:
            List of WidgetInfo objects
        """
        return self._extract_widgets(class_node)
