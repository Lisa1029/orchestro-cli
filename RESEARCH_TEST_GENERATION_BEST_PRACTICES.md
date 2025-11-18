# Test Generation Research: Best Practices & Implementation Strategy

**Project**: Orchestro CLI Test Generation
**Date**: 2025-11-16
**Phase**: SENSE - Research & Analysis

---

## Executive Summary

This document synthesizes research on best practices for automated test generation targeting Textual TUI applications. The goal is to create a "Playwright Codegen for Textual" that intelligently generates Orchestro CLI test scenarios from live application interaction.

**Key Findings**:
- Python AST analysis provides robust code introspection capabilities
- Textual has well-defined patterns for screens, actions, and bindings
- ML-based test prioritization can significantly improve coverage
- Heuristic scoring is more practical than full ML for initial implementation
- File-based trigger system (already in Orchestro) is ideal for TUI testing

---

## 1. Python AST Analysis

### 1.1 Core Libraries Comparison

| Library | Strengths | Weaknesses | Use Case |
|---------|-----------|------------|----------|
| **ast** (stdlib) | Built-in, fast, reliable | Low-level, verbose API | Basic parsing, node extraction |
| **astroid** | Type inference, cross-file analysis | Heavier, slower | Complex analysis, imports |
| **parso** | Error-tolerant, partial parsing | Less mature ecosystem | Incomplete code analysis |
| **LibCST** | Preserves formatting, lossless | More complex API | Code transformation |

**Recommendation**: Use **ast** for initial implementation with **astroid** for import resolution.

### 1.2 AST Traversal Patterns

#### Pattern 1: Extract All Class Definitions

```python
import ast
from typing import List, Dict, Any

class ClassExtractor(ast.NodeVisitor):
    """Extract all class definitions with their methods and bases."""
    
    def __init__(self):
        self.classes: List[Dict[str, Any]] = []
        self.current_class = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definition."""
        class_info = {
            'name': node.name,
            'lineno': node.lineno,
            'bases': [self._get_name(base) for base in node.bases],
            'decorators': [self._get_name(dec) for dec in node.decorator_list],
            'methods': [],
            'attributes': []
        }
        
        # Visit class body
        prev_class = self.current_class
        self.current_class = class_info
        self.generic_visit(node)
        self.current_class = prev_class
        
        self.classes.append(class_info)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract method definitions."""
        if self.current_class:
            method_info = {
                'name': node.name,
                'lineno': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'decorators': [self._get_name(dec) for dec in node.decorator_list],
                'returns': self._get_name(node.returns) if node.returns else None
            }
            self.current_class['methods'].append(method_info)
    
    def _get_name(self, node):
        """Safely extract name from AST node."""
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        if isinstance(node, ast.Constant):
            return node.value
        return ast.unparse(node) if hasattr(ast, 'unparse') else None

# Usage
def extract_classes(code: str) -> List[Dict[str, Any]]:
    tree = ast.parse(code)
    extractor = ClassExtractor()
    extractor.visit(tree)
    return extractor.classes
```

#### Pattern 2: Find Method Calls

```python
class MethodCallCollector(ast.NodeVisitor):
    """Collect all method calls with context."""
    
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.context_stack = []
    
    def visit_Call(self, node: ast.Call):
        """Extract method call information."""
        call_info = {
            'lineno': node.lineno,
            'col_offset': node.col_offset,
            'function': self._get_call_name(node.func),
            'args': [ast.unparse(arg) for arg in node.args],
            'kwargs': {kw.arg: ast.unparse(kw.value) for kw in node.keywords},
            'context': self.context_stack[-1] if self.context_stack else None
        }
        self.calls.append(call_info)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function context."""
        self.context_stack.append({
            'type': 'function',
            'name': node.name,
            'lineno': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class context."""
        self.context_stack.append({
            'type': 'class',
            'name': node.name,
            'lineno': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()
    
    def _get_call_name(self, node):
        """Extract callable name from Call node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = self._get_call_name(node.value)
            return f"{base}.{node.attr}"
        return ast.unparse(node)
```

#### Pattern 3: Decorator Analysis

```python
class DecoratorAnalyzer(ast.NodeVisitor):
    """Analyze decorators (critical for Textual @on, @work patterns)."""
    
    def __init__(self):
        self.decorated_functions = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract functions with decorators."""
        if node.decorator_list:
            func_info = {
                'name': node.name,
                'lineno': node.lineno,
                'decorators': []
            }
            
            for dec in node.decorator_list:
                dec_info = self._parse_decorator(dec)
                func_info['decorators'].append(dec_info)
            
            self.decorated_functions.append(func_info)
        
        self.generic_visit(node)
    
    def _parse_decorator(self, node) -> Dict[str, Any]:
        """Parse decorator with arguments."""
        if isinstance(node, ast.Name):
            # Simple decorator: @property
            return {'name': node.id, 'args': [], 'kwargs': {}}
        
        if isinstance(node, ast.Call):
            # Decorator with args: @on(Button.Pressed, "#save")
            return {
                'name': self._get_name(node.func),
                'args': [ast.unparse(arg) for arg in node.args],
                'kwargs': {kw.arg: ast.unparse(kw.value) for kw in node.keywords}
            }
        
        return {'name': ast.unparse(node), 'args': [], 'kwargs': {}}
    
    def _get_name(self, node):
        """Extract decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ast.unparse(node)
```

#### Pattern 4: Import Dependency Tracking

```python
class ImportTracker(ast.NodeVisitor):
    """Track all imports and their usage."""
    
    def __init__(self):
        self.imports: Dict[str, str] = {}  # alias -> module
        self.from_imports: Dict[str, str] = {}  # name -> module
    
    def visit_Import(self, node: ast.Import):
        """Track: import foo, import bar as baz."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track: from foo import Bar, Baz as B."""
        module = node.module or ''
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.from_imports[name] = f"{module}.{alias.name}"
    
    def get_full_name(self, name: str) -> str:
        """Resolve imported name to full module path."""
        if name in self.from_imports:
            return self.from_imports[name]
        if name in self.imports:
            return self.imports[name]
        return name
```

### 1.3 Practical Example: Extract Textual Screens

```python
def extract_textual_screens(file_path: str) -> List[Dict[str, Any]]:
    """Extract all Textual Screen classes from a Python file."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # First pass: find imports
    import_tracker = ImportTracker()
    import_tracker.visit(tree)
    
    # Second pass: find Screen classes
    class_extractor = ClassExtractor()
    class_extractor.visit(tree)
    
    # Filter for Textual screens
    screens = []
    for cls in class_extractor.classes:
        # Check if inherits from Screen
        is_screen = any(
            'Screen' in base or 'ModalScreen' in base 
            for base in cls['bases']
        )
        
        if is_screen:
            screens.append({
                'name': cls['name'],
                'file': file_path,
                'lineno': cls['lineno'],
                'methods': cls['methods'],
                'bindings': extract_bindings(cls),
                'actions': extract_actions(cls)
            })
    
    return screens

def extract_bindings(class_info: Dict) -> List[Dict]:
    """Extract BINDINGS from class definition."""
    # Look for BINDINGS class attribute
    # This requires analyzing ast.Assign nodes in class body
    # Simplified version - real implementation needs class body analysis
    return []

def extract_actions(class_info: Dict) -> List[str]:
    """Extract action_* methods from class."""
    return [
        method['name'][7:]  # Strip 'action_' prefix
        for method in class_info['methods']
        if method['name'].startswith('action_')
    ]
```

---

## 2. Textual Framework Patterns

### 2.1 Screen Class Structure

Textual applications follow predictable patterns:

```python
from textual.app import App
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.widgets import Button, Input, Label
from textual.containers import Container

class MyScreen(Screen):
    """Textual Screen - the primary unit of UI."""
    
    # Pattern 1: BINDINGS - keyboard shortcuts
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save", "Save"),
        Binding("/", "search", "Search"),
        ("escape", "cancel", "Cancel"),  # Also supports tuples
    ]
    
    # Pattern 2: compose() - UI construction
    def compose(self):
        """Build the UI tree."""
        yield Header()
        yield Container(
            Label("Welcome"),
            Input(id="username"),
            Button("Submit", id="submit-btn"),
            id="main-container"
        )
        yield Footer()
    
    # Pattern 3: action_* methods - bound actions
    def action_quit(self):
        """Quit action."""
        self.app.exit()
    
    def action_save(self):
        """Save action."""
        self.save_data()
    
    # Pattern 4: on_* event handlers (decorated)
    @on(Button.Pressed, "#submit-btn")
    def handle_submit(self, event):
        """Handle submit button press."""
        username = self.query_one("#username", Input).value
        self.process_login(username)
    
    @on(Input.Submitted)
    def handle_input_submit(self, event):
        """Handle Enter in any input."""
        self.action_save()
    
    # Pattern 5: @work decorators - async tasks
    @work
    async def save_data(self):
        """Async save operation."""
        await self.app.api.save(self.data)
```

### 2.2 Key Patterns for Test Generation

#### Pattern Detection Matrix

| Pattern | AST Detection | Test Generation Strategy |
|---------|---------------|--------------------------|
| **BINDINGS** | Class attribute `ast.Assign` with name="BINDINGS" | Generate steps for each keybinding |
| **action_* methods** | `ast.FunctionDef` with name starting "action_" | Test action calls via bindings |
| **@on decorators** | `ast.Call` decorator with func="on" | Test widget interactions |
| **compose() widgets** | `ast.FunctionDef` name="compose" + yield statements | Extract widget IDs for queries |
| **push_screen calls** | `ast.Call` with func="push_screen" | Generate navigation steps |

#### Binding Format Analysis

```python
# BINDINGS can be:
# 1. List of Binding objects
BINDINGS = [
    Binding("q", "quit", "Quit"),
]

# 2. List of tuples
BINDINGS = [
    ("q", "quit", "Quit"),
]

# 3. Mixed
BINDINGS = [
    Binding("s", "save", "Save", show=False),
    ("q", "quit", "Quit"),
]

# AST extraction:
def extract_bindings_from_ast(class_node: ast.ClassDef) -> List[Dict]:
    """Extract BINDINGS from class AST node."""
    bindings = []
    
    for node in class_node.body:
        if isinstance(node, ast.Assign):
            # Check if this is BINDINGS assignment
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "BINDINGS":
                    # Parse the list
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            binding = parse_binding_element(elt)
                            if binding:
                                bindings.append(binding)
    
    return bindings

def parse_binding_element(node) -> Dict:
    """Parse individual binding (Binding object or tuple)."""
    if isinstance(node, ast.Call):
        # Binding("q", "quit", "Quit")
        if len(node.args) >= 2:
            return {
                'key': ast.literal_eval(node.args[0]),
                'action': ast.literal_eval(node.args[1]),
                'description': ast.literal_eval(node.args[2]) if len(node.args) > 2 else None
            }
    
    elif isinstance(node, ast.Tuple):
        # ("q", "quit", "Quit")
        if len(node.elts) >= 2:
            return {
                'key': ast.literal_eval(node.elts[0]),
                'action': ast.literal_eval(node.elts[1]),
                'description': ast.literal_eval(node.elts[2]) if len(node.elts) > 2 else None
            }
    
    return None
```

### 2.3 Navigation Patterns

Textual apps navigate between screens using:

```python
# Push a screen onto the stack
self.app.push_screen(SettingsScreen())
self.push_screen("settings")  # By name if installed

# Pop current screen
self.app.pop_screen()

# Switch to a screen (replace current)
self.app.switch_screen(DashboardScreen())

# Modal screens (return value)
result = await self.app.push_screen_wait(ConfirmDialog())
```

**Test Generation Implication**: Track `push_screen`, `pop_screen`, `switch_screen` calls to build navigation graph.

---

## 3. Test Generation Strategies

### 3.1 Code-to-Test Mapping Heuristics

#### Heuristic 1: Coverage-Based Priority

```python
from dataclasses import dataclass
from typing import List, Set

@dataclass
class TestCase:
    """Represents a potential test case."""
    name: str
    steps: List[str]
    coverage_score: float  # 0-1
    priority: int  # 1-10
    confidence: float  # 0-1

class CoverageCalculator:
    """Calculate test coverage scores."""
    
    def __init__(self):
        self.covered_lines: Set[int] = set()
        self.total_lines: Set[int] = set()
    
    def calculate_screen_coverage(
        self, 
        screen_info: Dict,
        existing_tests: List[TestCase]
    ) -> float:
        """Calculate coverage for a screen."""
        # Lines in screen definition
        screen_lines = set(range(
            screen_info['lineno'],
            screen_info['lineno'] + screen_info['line_count']
        ))
        
        # Lines covered by existing tests
        covered = set()
        for test in existing_tests:
            covered.update(test.covered_lines)
        
        # Coverage ratio
        if not screen_lines:
            return 1.0
        
        return len(covered & screen_lines) / len(screen_lines)
    
    def suggest_tests_for_coverage(
        self,
        screen_info: Dict,
        target_coverage: float = 0.80
    ) -> List[TestCase]:
        """Suggest tests to reach target coverage."""
        current_coverage = self.calculate_screen_coverage(screen_info, [])
        
        if current_coverage >= target_coverage:
            return []
        
        suggestions = []
        
        # Test each binding
        for binding in screen_info.get('bindings', []):
            test = TestCase(
                name=f"test_{screen_info['name']}_binding_{binding['key']}",
                steps=[
                    f"navigate to {screen_info['name']}",
                    f"press key {binding['key']}",
                    f"verify action {binding['action']} executed"
                ],
                coverage_score=0.1,  # Each binding covers ~10% on average
                priority=5,
                confidence=0.9  # High confidence for bindings
            )
            suggestions.append(test)
        
        # Test each widget interaction
        for widget in screen_info.get('widgets', []):
            test = TestCase(
                name=f"test_{screen_info['name']}_widget_{widget['id']}",
                steps=[
                    f"navigate to {screen_info['name']}",
                    f"interact with {widget['type']} #{widget['id']}",
                    "verify state change"
                ],
                coverage_score=0.15,
                priority=7,
                confidence=0.7
            )
            suggestions.append(test)
        
        return suggestions
```

#### Heuristic 2: Interaction Depth Scoring

```python
class InteractionScorer:
    """Score test cases by interaction complexity."""
    
    def score_test(self, test_case: TestCase) -> float:
        """
        Score based on:
        - Number of interactions
        - Depth of navigation
        - State changes
        - Assertions
        """
        score = 0.0
        
        # Base score for each step
        score += len(test_case.steps) * 0.1
        
        # Bonus for navigation
        nav_steps = sum(1 for s in test_case.steps if 'navigate' in s.lower())
        score += nav_steps * 0.2
        
        # Bonus for assertions
        assert_steps = sum(1 for s in test_case.steps if 'verify' in s.lower())
        score += assert_steps * 0.3
        
        # Penalty for too many steps (flaky tests)
        if len(test_case.steps) > 10:
            score *= 0.8
        
        return min(score, 1.0)
```

#### Heuristic 3: Critical Path Identification

```python
class CriticalPathAnalyzer:
    """Identify critical user paths through the application."""
    
    def __init__(self):
        self.navigation_graph: Dict[str, List[str]] = {}
        self.screen_weights: Dict[str, float] = {}
    
    def build_navigation_graph(self, screens: List[Dict]):
        """Build graph from screen analysis."""
        for screen in screens:
            self.navigation_graph[screen['name']] = []
            
            # Find push_screen calls in methods
            for method in screen.get('methods', []):
                for call in method.get('calls', []):
                    if 'push_screen' in call['function']:
                        target = call.get('args', [None])[0]
                        if target:
                            self.navigation_graph[screen['name']].append(target)
    
    def find_critical_paths(self, start_screen: str, max_depth: int = 5) -> List[List[str]]:
        """Find most important navigation paths."""
        paths = []
        
        def dfs(current: str, path: List[str], depth: int):
            if depth >= max_depth:
                paths.append(path.copy())
                return
            
            for next_screen in self.navigation_graph.get(current, []):
                if next_screen not in path:  # Avoid cycles
                    path.append(next_screen)
                    dfs(next_screen, path, depth + 1)
                    path.pop()
        
        dfs(start_screen, [start_screen], 0)
        
        # Score paths by weight
        scored_paths = [
            (path, sum(self.screen_weights.get(s, 1.0) for s in path))
            for path in paths
        ]
        
        # Return top 10 critical paths
        scored_paths.sort(key=lambda x: x[1], reverse=True)
        return [path for path, score in scored_paths[:10]]
```

### 3.2 Priority Scoring Algorithm

```python
class TestPriorityScorer:
    """Comprehensive test priority scoring."""
    
    WEIGHTS = {
        'coverage': 0.30,
        'complexity': 0.20,
        'critical_path': 0.25,
        'error_prone': 0.15,
        'user_value': 0.10
    }
    
    def score_test(
        self,
        test: TestCase,
        screen_info: Dict,
        coverage_data: Dict,
        critical_paths: List[List[str]]
    ) -> float:
        """Calculate comprehensive priority score (0-100)."""
        
        # Coverage score: How much new coverage does this test add?
        coverage_score = self._coverage_score(test, coverage_data)
        
        # Complexity score: More complex = higher priority
        complexity_score = self._complexity_score(test, screen_info)
        
        # Critical path score: Is this on a critical user path?
        critical_score = self._critical_path_score(test, critical_paths)
        
        # Error-prone score: Historical failure rate
        error_score = self._error_prone_score(test, screen_info)
        
        # User value score: Business importance
        value_score = self._user_value_score(test, screen_info)
        
        # Weighted sum
        total = (
            coverage_score * self.WEIGHTS['coverage'] +
            complexity_score * self.WEIGHTS['complexity'] +
            critical_score * self.WEIGHTS['critical_path'] +
            error_score * self.WEIGHTS['error_prone'] +
            value_score * self.WEIGHTS['user_value']
        )
        
        return total * 100  # Scale to 0-100
    
    def _coverage_score(self, test: TestCase, coverage_data: Dict) -> float:
        """Score based on coverage gap."""
        # Higher score if test covers uncovered code
        return 1.0 - coverage_data.get('current_coverage', 0.0)
    
    def _complexity_score(self, test: TestCase, screen_info: Dict) -> float:
        """Score based on cyclomatic complexity."""
        # More complex screens = higher priority
        complexity = screen_info.get('complexity', 1)
        return min(complexity / 10.0, 1.0)
    
    def _critical_path_score(self, test: TestCase, critical_paths: List[List[str]]) -> float:
        """Score based on critical path membership."""
        # Check if test touches critical paths
        test_screens = set(step.split()[2] for step in test.steps if 'navigate' in step)
        
        for path in critical_paths:
            if any(screen in path for screen in test_screens):
                return 1.0
        
        return 0.3  # Some value even if not on critical path
    
    def _error_prone_score(self, test: TestCase, screen_info: Dict) -> float:
        """Score based on historical bugs."""
        # Higher if screen has history of bugs
        bug_count = screen_info.get('historical_bugs', 0)
        return min(bug_count / 5.0, 1.0)
    
    def _user_value_score(self, test: TestCase, screen_info: Dict) -> float:
        """Score based on user-facing value."""
        # Core features > settings > edge cases
        if 'settings' in screen_info['name'].lower():
            return 0.5
        if 'main' in screen_info['name'].lower() or 'dashboard' in screen_info['name'].lower():
            return 1.0
        return 0.7
```

### 3.3 Confidence Metrics

```python
class ConfidenceCalculator:
    """Calculate confidence in generated tests."""
    
    def calculate_confidence(self, test: TestCase, context: Dict) -> float:
        """
        Confidence factors:
        - Pattern clarity (is the code pattern well-understood?)
        - Static analysis completeness
        - Ambiguity in action mapping
        """
        confidence = 1.0
        
        # Reduce confidence for ambiguous patterns
        if any('unknown' in step.lower() for step in test.steps):
            confidence *= 0.5
        
        # Reduce confidence if missing widget IDs
        if any('#' not in step for step in test.steps if 'interact' in step):
            confidence *= 0.7
        
        # Reduce confidence for complex async flows
        if context.get('has_async_operations'):
            confidence *= 0.8
        
        # Increase confidence for simple bindings
        if all('press key' in step or 'navigate' in step for step in test.steps):
            confidence *= 1.2
        
        return min(confidence, 1.0)
```

---

## 4. Similar Tools Analysis

### 4.1 Playwright Codegen

**How it works**:
1. Launches browser with instrumentation
2. Records user interactions (clicks, typing, navigation)
3. Generates test code with selectors
4. Supports multiple languages (Python, JS, Java, C#)

**Key Techniques**:
- **Selector generation**: Prioritizes accessible selectors (data-testid > text > CSS)
- **Action recording**: Captures timing, element states
- **Smart waiting**: Auto-generates wait conditions
- **Screenshot assertions**: Can generate visual comparisons

**Lessons for Orchestro**:
- Use stable identifiers (widget IDs) over fragile selectors
- Generate explicit waits (not implicit sleeps)
- Include screenshot steps for visual verification
- Support multiple output formats (YAML, Python, JSON)

### 4.2 Selenium IDE

**How it works**:
1. Browser extension records interactions
2. Converts to Selenium WebDriver commands
3. Supports playback with debugging
4. Export to code in multiple languages

**Key Techniques**:
- **Command palette**: Simple actions (click, type, assert)
- **Breakpoints**: Debugging support
- **Data-driven testing**: CSV/JSON data sources
- **Control flow**: Loops, conditionals in recordings

**Lessons for Orchestro**:
- Simple command vocabulary maps well to YAML
- Debugging support is critical
- Data-driven scenarios useful for TUI apps
- Control flow can be inferred from code structure

### 4.3 Cypress Studio

**How it works**:
1. In-app recording overlay
2. Records commands with auto-assertions
3. Generates Cypress test code
4. Live editing and replay

**Key Techniques**:
- **Assertion generation**: Auto-suggests assertions based on state
- **Time travel**: Replay at any step
- **Element picker**: Visual selector tool
- **Smart waits**: Automatic retry logic

**Lessons for Orchestro**:
- Auto-generate assertions from state snapshots
- Visual picker for widget IDs (via screenshot overlay?)
- Replay mechanism critical for debugging
- Automatic retry/wait logic

### 4.4 Comparison Matrix

| Feature | Playwright | Selenium IDE | Cypress | Orchestro (Proposed) |
|---------|-----------|--------------|---------|-------------------|
| **Recording** | Browser events | Browser extension | In-app overlay | TUI interaction monitoring |
| **Selector Strategy** | Accessibility first | ID/CSS/XPath | Custom selectors | Widget ID + binding keys |
| **Wait Strategy** | Auto-wait | Explicit waits | Auto-retry | Sentinel patterns + timeouts |
| **Output Format** | Multi-language | Multi-language | JavaScript | YAML (+ Python planned) |
| **Assertions** | Manual + auto | Manual | Auto-suggested | Pattern-based + screenshots |
| **Debugging** | DevTools | Breakpoints | Time travel | Verbose logs + screenshots |

---

## 5. Machine Learning for Testing

### 5.1 Test Case Prioritization (ML Approach)

**Common ML Models**:
- **Logistic Regression**: Simple, interpretable
- **Random Forest**: Good for feature importance
- **Gradient Boosting (XGBoost)**: High accuracy
- **Neural Networks**: Overkill for most projects

**Feature Engineering**:
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from typing import List, Dict

class MLTestPrioritizer:
    """ML-based test prioritization."""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.is_trained = False
    
    def extract_features(self, test: TestCase, context: Dict) -> np.ndarray:
        """Extract features for ML model."""
        features = [
            len(test.steps),  # Test length
            context.get('code_complexity', 0),  # Cyclomatic complexity
            context.get('line_count', 0),  # Lines of code
            context.get('bug_history', 0),  # Historical bugs
            context.get('last_modified_days', 0),  # Code freshness
            float('navigate' in str(test.steps)),  # Has navigation
            float(any('verify' in s for s in test.steps)),  # Has assertions
            context.get('coverage_gap', 0.0),  # Uncovered code %
        ]
        return np.array(features)
    
    def train(self, historical_tests: List[Tuple[TestCase, Dict, bool]]):
        """Train on historical data.
        
        Args:
            historical_tests: List of (test, context, found_bug) tuples
        """
        X = []
        y = []
        
        for test, context, found_bug in historical_tests:
            X.append(self.extract_features(test, context))
            y.append(1 if found_bug else 0)
        
        self.model.fit(np.array(X), np.array(y))
        self.is_trained = True
    
    def predict_priority(self, test: TestCase, context: Dict) -> float:
        """Predict test priority (0-1)."""
        if not self.is_trained:
            # Fall back to heuristic
            return self._heuristic_priority(test, context)
        
        features = self.extract_features(test, context)
        # Probability of finding a bug
        return self.model.predict_proba([features])[0][1]
    
    def _heuristic_priority(self, test: TestCase, context: Dict) -> float:
        """Heuristic fallback when ML not available."""
        score = 0.5  # Base score
        
        # Boost for complexity
        if context.get('code_complexity', 0) > 5:
            score += 0.2
        
        # Boost for recent changes
        if context.get('last_modified_days', 999) < 7:
            score += 0.2
        
        # Boost for historical bugs
        if context.get('bug_history', 0) > 0:
            score += 0.1
        
        return min(score, 1.0)
```

**Recommendation**: **Start with heuristics, add ML later**. Heuristics are easier to debug and explain.

### 5.2 Failure Prediction

**Techniques**:
- **Flakiness detection**: Identify tests that fail intermittently
- **Bug localization**: Predict which code changes break which tests
- **Test smell detection**: Identify anti-patterns in tests

```python
class FlakeinessDetector:
    """Detect flaky tests based on execution history."""
    
    def __init__(self):
        self.execution_history: Dict[str, List[bool]] = {}
    
    def record_execution(self, test_name: str, passed: bool):
        """Record test execution result."""
        if test_name not in self.execution_history:
            self.execution_history[test_name] = []
        self.execution_history[test_name].append(passed)
    
    def calculate_flakiness(self, test_name: str) -> float:
        """Calculate flakiness score (0=stable, 1=very flaky)."""
        history = self.execution_history.get(test_name, [])
        
        if len(history) < 3:
            return 0.0  # Not enough data
        
        # Count transitions (pass->fail or fail->pass)
        transitions = sum(
            1 for i in range(len(history) - 1)
            if history[i] != history[i + 1]
        )
        
        # Flakiness = transitions / possible_transitions
        return transitions / (len(history) - 1)
    
    def is_flaky(self, test_name: str, threshold: float = 0.3) -> bool:
        """Check if test is flaky."""
        return self.calculate_flakiness(test_name) > threshold
```

### 5.3 Auto-Repair Techniques

**Pattern-based repair**:
1. **Timeout adjustment**: Increase timeouts for slow steps
2. **Selector healing**: Update changed widget IDs
3. **Assertion relaxation**: Make assertions less brittle

```python
class TestAutoRepair:
    """Automatically repair broken tests."""
    
    def suggest_repairs(self, test: TestCase, failure: Exception) -> List[Dict]:
        """Suggest repairs for a failed test."""
        suggestions = []
        
        # Timeout failures
        if 'timeout' in str(failure).lower():
            suggestions.append({
                'type': 'increase_timeout',
                'description': 'Increase timeout from 10s to 30s',
                'confidence': 0.8
            })
        
        # Widget not found
        if 'not found' in str(failure).lower() or 'NoMatches' in str(failure):
            suggestions.append({
                'type': 'update_selector',
                'description': 'Widget ID may have changed',
                'confidence': 0.6
            })
        
        # Screenshot mismatch
        if 'screenshot' in str(failure).lower():
            suggestions.append({
                'type': 'update_screenshot_baseline',
                'description': 'UI may have legitimately changed',
                'confidence': 0.5
            })
        
        return suggestions
```

**Recommendation**: Start with **pattern-based repair**, not full ML. It's more predictable.

---

## 6. Implementation Recommendations

### 6.1 Architecture Design

```
orchestro-codegen/
├── analyzer/
│   ├── ast_analyzer.py       # AST-based code analysis
│   ├── textual_analyzer.py   # Textual-specific patterns
│   └── import_resolver.py    # Dependency tracking
├── recorder/
│   ├── interaction_monitor.py  # Live recording (future)
│   └── event_logger.py         # Log TUI events
├── generator/
│   ├── test_generator.py     # Main test generation
│   ├── yaml_builder.py       # Build Orchestro YAML
│   └── templates/            # Test templates
├── scorer/
│   ├── priority_scorer.py    # Heuristic scoring
│   ├── coverage_analyzer.py  # Coverage calculations
│   └── confidence.py         # Confidence metrics
└── cli.py                     # CLI interface
```

### 6.2 Phase 1: Static Analysis (Recommended Start)

**Goal**: Generate tests from code without runtime recording.

**Steps**:
1. Parse Python files with AST
2. Extract Textual screens, bindings, actions
3. Build navigation graph
4. Generate test scenarios for each screen
5. Score and prioritize tests
6. Output Orchestro YAML files

**Example Command**:
```bash
orchestro-codegen analyze ./my_app.py --output tests/ --coverage 0.80
```

**Output**:
```yaml
# tests/test_settings_screen.yaml
name: Settings Screen - Save Settings
description: Auto-generated test for SettingsScreen save action

command: python my_app.py
timeout: 30

steps:
  - screenshot: "01-startup"
    timeout: 10
    note: "Capture initial state"
  
  - send: "s"
    note: "Navigate to settings (keybinding 's')"
  
  - screenshot: "02-settings-screen"
    timeout: 10
  
  - send: "/advanced"
    note: "Enter advanced mode"
  
  - screenshot: "03-advanced-settings"
    timeout: 10

validations:
  - type: path_exists
    path: artifacts/screenshots/01-startup.svg
  - type: path_exists
    path: artifacts/screenshots/02-settings-screen.svg
  - type: path_exists
    path: artifacts/screenshots/03-advanced-settings.svg

# Auto-generated by orchestro-codegen v0.1.0
# Source: my_app.py:SettingsScreen (line 45)
# Confidence: 0.85
# Priority: 78/100
```

### 6.3 Phase 2: Runtime Recording (Future Enhancement)

**Goal**: Record live interactions like Playwright Codegen.

**Approach**:
1. Inject instrumentation into Textual app
2. Log all events (key presses, widget interactions)
3. Track screen transitions
4. Capture screenshots at key moments
5. Generate Orchestro YAML from recording

**Technical Challenges**:
- Textual doesn't have built-in instrumentation
- Need to monkey-patch or use custom App subclass
- Event ordering and timing critical

**Future Command**:
```bash
orchestro-codegen record --app "python my_app.py" --output recording.yaml
# Opens app, records interactions, saves test
```

### 6.4 Recommended Tech Stack

| Component | Library | Rationale |
|-----------|---------|-----------|
| **AST Analysis** | `ast` (stdlib) + `astroid` | Fast, reliable, good type inference |
| **YAML Generation** | `pyyaml` | Already used by Orchestro |
| **CLI** | `click` or `argparse` | Simple, well-documented |
| **Testing** | `pytest` | Industry standard |
| **Code Formatting** | `black` | Consistent style |
| **Type Checking** | `mypy` | Catch bugs early |

### 6.5 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Coverage** | 80%+ | Lines covered by generated tests |
| **Confidence Score** | 0.75+ avg | Average confidence in generated tests |
| **Generation Speed** | <5s per screen | Time to analyze + generate |
| **False Positive Rate** | <10% | Tests that fail on valid code |
| **User Adoption** | 50%+ of devs use it | Usage metrics |

---

## 7. Research Citations & Resources

### 7.1 Python AST Resources

- **Official AST Documentation**: https://docs.python.org/3/library/ast.html
- **Green Tree Snakes (AST Tutorial)**: https://greentreesnakes.readthedocs.io/
- **Astroid Documentation**: https://pylint.pycqa.org/projects/astroid/
- **LibCST**: https://libcst.readthedocs.io/

### 7.2 Textual Framework

- **Textual Documentation**: https://textual.textualize.io/
- **Textual GitHub**: https://github.com/Textualize/textual
- **Rich (underlying library)**: https://rich.readthedocs.io/

### 7.3 Test Generation Research

**Academic Papers**:
1. "Automated Test Case Generation: A Survey" (IEEE, 2021)
2. "Machine Learning for Software Testing" (ACM Computing Surveys, 2020)
3. "Test Case Prioritization: A Systematic Mapping Study" (Information and Software Technology, 2018)

**Industry Approaches**:
- **Facebook's Sapienz**: ML-based Android test generation
- **Google's Bugswarm**: Dataset of real bugs for test research
- **Microsoft's DeepTest**: Deep learning for automated testing

### 7.4 Code Analysis Tools

- **Sourcery**: AI-powered code review
- **Codex (OpenAI)**: Code generation from descriptions
- **GitHub Copilot**: Context-aware code completion
- **Tabnine**: AI code completion

### 7.5 Similar Projects

- **Playwright Codegen**: https://playwright.dev/docs/codegen
- **Selenium IDE**: https://www.selenium.dev/selenium-ide/
- **Cypress Studio**: https://docs.cypress.io/guides/references/cypress-studio
- **Katalon Recorder**: https://www.katalon.com/

---

## 8. Next Steps

### 8.1 Immediate Actions

1. **Prototype AST extractor** for Textual screens (2-3 hours)
2. **Design YAML generation templates** (1-2 hours)
3. **Implement basic priority scorer** (2-3 hours)
4. **Create demo with 2-3 screens** (1 hour)
5. **Validate generated tests** (1 hour)

**Total estimate**: 1-2 days for MVP

### 8.2 Phase 1 Deliverables

- [ ] Static analyzer for Textual apps
- [ ] Test case generator (YAML output)
- [ ] Priority/confidence scoring
- [ ] CLI interface (`orchestro-codegen analyze`)
- [ ] Documentation + examples
- [ ] Test suite (pytest)

### 8.3 Future Enhancements

- [ ] Runtime recording (Playwright-style)
- [ ] ML-based prioritization (with training data)
- [ ] Visual widget picker (screenshot overlay)
- [ ] Multi-language output (Python, JSON)
- [ ] IDE plugin (VSCode extension)
- [ ] CI/CD integration (GitHub Actions)

---

## 9. Risk Analysis

### 9.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **AST limitations** | Medium | Medium | Use astroid for complex cases |
| **Textual API changes** | Low | High | Version pin, monitor releases |
| **Flaky generated tests** | High | Medium | Add confidence scores, manual review |
| **Performance at scale** | Medium | Low | Optimize AST parsing, cache results |

### 9.2 Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Low adoption** | Medium | High | Focus on UX, documentation |
| **Generated tests too basic** | Medium | Medium | Allow customization, templates |
| **Maintenance burden** | Low | Medium | Keep codebase simple, well-tested |

---

## 10. Conclusion

**Key Takeaways**:

1. **AST analysis is mature and practical** - The `ast` module + `astroid` provide everything needed for static analysis.

2. **Textual has predictable patterns** - BINDINGS, actions, compose() follow conventions that are easy to extract.

3. **Heuristic scoring is sufficient for MVP** - Don't over-engineer with ML initially. Priority/confidence heuristics will get 80% of value.

4. **Playwright/Cypress patterns apply to TUI** - The recording → code generation → playback pattern translates well.

5. **Start with static analysis, add recording later** - Phase 1 (static) is achievable in days. Phase 2 (recording) is a larger lift.

**Recommended Approach**: Build a **static analyzer** that generates Orchestro YAML tests from Textual code. Focus on:
- Extracting screens, bindings, actions
- Generating comprehensive test scenarios
- Scoring by priority/confidence
- Clean YAML output with comments

This aligns perfectly with Orchestro's existing file-based trigger system and screenshot capabilities.

---

**Document Version**: 1.0  
**Author**: Research Specialist Agent  
**Date**: 2025-11-16  
**Status**: Ready for PLAN phase
