"""Validation engine for scenario results."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..parsing.models import Validation


@dataclass
class ValidationResult:
    """Result of a validation check."""

    validation: Validation
    passed: bool
    error_message: Optional[str] = None

    @property
    def status_icon(self) -> str:
        """Get status icon for display."""
        return "✓" if self.passed else "❌"


class ValidationEngine:
    """Executes validation rules against scenario results.

    Single Responsibility: Run validations and collect results.
    """

    def __init__(self, base_dir: Optional[Path] = None, verbose: bool = False):
        """Initialize validation engine.

        Args:
            base_dir: Base directory for relative paths (defaults to cwd)
            verbose: Enable verbose logging
        """
        self.base_dir = base_dir or Path.cwd()
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[ValidationEngine] {message}")

    def validate_all(self, validations: List[Validation]) -> List[ValidationResult]:
        """Execute all validations and return results.

        Args:
            validations: List of validation rules

        Returns:
            List of validation results

        Raises:
            AssertionError: If any validation fails
        """
        results: List[ValidationResult] = []

        for validation in validations:
            result = self._validate_single(validation)
            results.append(result)

            if not result.passed:
                raise AssertionError(result.error_message)

        return results

    def _validate_single(self, validation: Validation) -> ValidationResult:
        """Execute a single validation.

        Args:
            validation: Validation rule to execute

        Returns:
            ValidationResult with pass/fail status
        """
        if validation.type == "path_exists":
            return self._validate_path_exists(validation)
        elif validation.type == "file_contains":
            return self._validate_file_contains(validation)
        else:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message=f"Unknown validation type: {validation.type}"
            )

    def _validate_path_exists(self, validation: Validation) -> ValidationResult:
        """Validate that a path exists.

        Args:
            validation: Validation with path field

        Returns:
            ValidationResult
        """
        if not validation.path:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message="path_exists validation requires 'path' field"
            )

        # Resolve path
        target = self._resolve_path(validation.path)

        if target.exists():
            self._log(f"Path exists: {target}")
            return ValidationResult(validation=validation, passed=True)
        else:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message=f"Expected path to exist: {target}"
            )

    def _validate_file_contains(self, validation: Validation) -> ValidationResult:
        """Validate that a file contains specific text.

        Args:
            validation: Validation with path and text fields

        Returns:
            ValidationResult
        """
        if not validation.path:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message="file_contains validation requires 'path' field"
            )

        if validation.text is None:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message="file_contains validation requires 'text' field"
            )

        # Resolve path
        target = self._resolve_path(validation.path)

        if not target.exists():
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message=f"Expected file for content check: {target}"
            )

        # Read file content
        try:
            content = target.read_text(encoding="utf-8")
        except Exception as e:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message=f"Error reading file {target}: {e}"
            )

        # Check if text pattern matches
        if re.search(validation.text, content):
            self._log(f"Text '{validation.text}' found in {target}")
            return ValidationResult(validation=validation, passed=True)
        else:
            return ValidationResult(
                validation=validation,
                passed=False,
                error_message=f"Text '{validation.text}' not found in {target}"
            )

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve path relative to base directory.

        Args:
            path_str: Path string to resolve

        Returns:
            Resolved Path object
        """
        val_path = Path(path_str)

        # If path is absolute or starts with known prefixes, use as-is from cwd
        if val_path.is_absolute() or str(path_str).startswith(("artifacts/", "tmp/", ".")):
            target = Path.cwd() / path_str if not val_path.is_absolute() else val_path
        else:
            target = self.base_dir / path_str

        return target
