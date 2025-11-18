"""Domain models for scenarios."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class Step:
    """Represents a single step in a scenario."""

    expect: Optional[str] = None
    send: Optional[str] = None
    control: Optional[str] = None
    note: Optional[str] = None
    timeout: Optional[float] = None
    raw: bool = False
    screenshot: Optional[str] = None
    # Inline assertions
    expect_output: Optional[str] = None
    expect_code: Optional[int] = None
    expect_contains: Optional[str] = None
    expect_regex: Optional[str] = None
    expect_lines: Optional[int] = None
    expect_not_contains: Optional[str] = None
    expect_json: Optional[Dict[str, Any]] = None
    # Metadata for inline assertions
    assertions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def step_type(self) -> str:
        """Identify the primary step type."""
        if self.expect:
            return "expect"
        elif self.send is not None:
            return "send"
        elif self.control:
            return "control"
        elif self.screenshot:
            return "screenshot"
        else:
            return "note"

    @property
    def has_assertions(self) -> bool:
        """Check if step has inline assertions."""
        return (
            self.expect_output is not None
            or self.expect_code is not None
            or self.expect_contains is not None
            or self.expect_regex is not None
            or self.expect_lines is not None
            or self.expect_not_contains is not None
            or self.expect_json is not None
            or len(self.assertions) > 0
        )


@dataclass
class Validation:
    """Represents a validation rule."""

    type: str
    path: Optional[str] = None
    text: Optional[str] = None
    description: Optional[str] = None

    def validate_completeness(self) -> None:
        """Validate that required fields are present."""
        if self.type == "path_exists" and not self.path:
            raise ValueError("path_exists validation requires 'path' field")
        if self.type == "file_contains":
            if not self.path:
                raise ValueError("file_contains validation requires 'path' field")
            if self.text is None:
                raise ValueError("file_contains validation requires 'text' field")


@dataclass
class Scenario:
    """Immutable scenario representation."""

    name: str
    command: Any  # Can be string or list
    steps: list[Step]
    validations: list[Validation]
    timeout: float = 30.0
    description: Optional[str] = None
    env: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Validate scenario after initialization."""
        if not self.command:
            raise ValueError("Scenario must have a command")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

    @property
    def id(self) -> str:
        """Unique scenario identifier."""
        return f"{self.name.lower().replace(' ', '_')}_{id(self)}"

    @property
    def step_count(self) -> int:
        """Number of steps in scenario."""
        return len(self.steps)

    @property
    def validation_count(self) -> int:
        """Number of validations in scenario."""
        return len(self.validations)
