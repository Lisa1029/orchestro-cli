"""Domain models for snapshot testing system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class SnapshotMode(Enum):
    """Snapshot testing modes."""

    VERIFY = "verify"  # Verify outputs match snapshots (CI/CD)
    UPDATE = "update"  # Update existing snapshots
    RECORD = "record"  # Record new snapshots

    def __str__(self) -> str:
        """String representation."""
        return self.value


@dataclass
class CapturedOutput:
    """Represents captured process output.

    Attributes:
        stdout: Standard output text
        stderr: Standard error text
        exit_code: Process exit code
        timestamp: Capture timestamp
        metadata: Additional metadata (e.g., environment, command)
    """

    stdout: str
    stderr: str
    exit_code: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate captured output."""
        if not isinstance(self.stdout, str):
            raise TypeError("stdout must be a string")
        if not isinstance(self.stderr, str):
            raise TypeError("stderr must be a string")
        if not isinstance(self.exit_code, int):
            raise TypeError("exit_code must be an integer")

    @property
    def has_output(self) -> bool:
        """Check if there's any output."""
        return bool(self.stdout or self.stderr)

    @property
    def is_success(self) -> bool:
        """Check if exit code indicates success."""
        return self.exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapturedOutput":
        """Create from dictionary."""
        return cls(
            stdout=data["stdout"],
            stderr=data["stderr"],
            exit_code=data["exit_code"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Snapshot:
    """Represents a stored snapshot.

    Attributes:
        scenario_name: Name of the scenario
        output: Captured output
        created_at: When snapshot was created
        updated_at: Last update timestamp
        checksum: SHA256 checksum for integrity
    """

    scenario_name: str
    output: CapturedOutput
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None

    def __post_init__(self):
        """Validate snapshot."""
        if not self.scenario_name:
            raise ValueError("scenario_name cannot be empty")
        if not isinstance(self.output, CapturedOutput):
            raise TypeError("output must be a CapturedOutput instance")

    @property
    def slug(self) -> str:
        """Get URL-friendly slug from scenario name."""
        import re
        slug = self.scenario_name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_name": self.scenario_name,
            "output": self.output.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Create from dictionary."""
        return cls(
            scenario_name=data["scenario_name"],
            output=CapturedOutput.from_dict(data["output"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            checksum=data.get("checksum"),
        )


@dataclass
class DiffLine:
    """Represents a single line in a diff."""

    line_type: str  # '+', '-', ' ', '@@'
    content: str
    old_line_num: Optional[int] = None
    new_line_num: Optional[int] = None

    @property
    def is_addition(self) -> bool:
        """Check if line is an addition."""
        return self.line_type == "+"

    @property
    def is_deletion(self) -> bool:
        """Check if line is a deletion."""
        return self.line_type == "-"

    @property
    def is_context(self) -> bool:
        """Check if line is context."""
        return self.line_type == " "

    @property
    def is_header(self) -> bool:
        """Check if line is a header."""
        return self.line_type == "@@"


@dataclass
class DiffResult:
    """Result of comparing two outputs.

    Attributes:
        has_diff: Whether there are differences
        similarity_score: Similarity percentage (0-100)
        stdout_diff: Diff lines for stdout
        stderr_diff: Diff lines for stderr
        exit_code_match: Whether exit codes match
        summary: Human-readable summary
    """

    has_diff: bool
    similarity_score: float
    stdout_diff: list[DiffLine] = field(default_factory=list)
    stderr_diff: list[DiffLine] = field(default_factory=list)
    exit_code_match: bool = True
    summary: str = ""

    def __post_init__(self):
        """Validate diff result."""
        if not 0 <= self.similarity_score <= 100:
            raise ValueError("similarity_score must be between 0 and 100")

    @property
    def is_identical(self) -> bool:
        """Check if outputs are identical."""
        return not self.has_diff and self.exit_code_match

    @property
    def has_stdout_diff(self) -> bool:
        """Check if stdout has differences."""
        return any(
            line.is_addition or line.is_deletion for line in self.stdout_diff
        )

    @property
    def has_stderr_diff(self) -> bool:
        """Check if stderr has differences."""
        return any(
            line.is_addition or line.is_deletion for line in self.stderr_diff
        )


@dataclass
class SnapshotResult:
    """Result of snapshot verification.

    Attributes:
        passed: Whether verification passed
        diff_result: Diff result if verification failed
        message: Human-readable message
        snapshot_exists: Whether snapshot existed
        snapshot_path: Path to snapshot directory
    """

    passed: bool
    diff_result: Optional[DiffResult] = None
    message: str = ""
    snapshot_exists: bool = True
    snapshot_path: Optional[str] = None

    @property
    def failed(self) -> bool:
        """Check if verification failed."""
        return not self.passed

    @property
    def has_diff(self) -> bool:
        """Check if there's a diff."""
        return self.diff_result is not None and self.diff_result.has_diff

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "message": self.message,
            "snapshot_exists": self.snapshot_exists,
            "snapshot_path": self.snapshot_path,
            "has_diff": self.has_diff,
            "similarity_score": (
                self.diff_result.similarity_score if self.diff_result else 100.0
            ),
        }
