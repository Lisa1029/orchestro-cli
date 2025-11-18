"""Validator plugin protocol for custom validation types.

This protocol enables adding new validation types without modifying
the validation engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


@dataclass
class ValidationContext:
    """Context passed to validators during execution."""

    base_dir: Path
    scenario_state: Dict[str, Any]
    verbose: bool = False

    def log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[Validation] {message}")


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    validator_type: str
    message: str
    details: Optional[Dict[str, Any]] = None

    @property
    def error_message(self) -> str:
        """Get formatted error message."""
        if self.passed:
            return ""
        msg = f"Validation '{self.validator_type}' failed: {self.message}"
        if self.details:
            msg += f"\nDetails: {self.details}"
        return msg


class ValidatorPlugin(Protocol):
    """Protocol for custom validation implementations.

    Plugins can add new validation types beyond path_exists and file_contains.

    Examples:
        - HTTPResponseValidator (check API responses)
        - DatabaseStateValidator (verify DB state)
        - ProcessOutputValidator (check process logs)
        - MetricsValidator (verify performance metrics)
        - SecurityValidator (check security constraints)
        - SchemaValidator (validate JSON/YAML structure)
    """

    @property
    def validator_type(self) -> str:
        """Unique identifier for this validator type.

        Returns:
            Validator type name (e.g., 'http_response', 'db_state')
        """
        ...

    def can_handle(self, validation_type: str) -> bool:
        """Check if this plugin handles the given validation type.

        Args:
            validation_type: Type from validation spec

        Returns:
            True if this plugin handles this type
        """
        ...

    def validate(
        self,
        validation_spec: Dict[str, Any],
        context: ValidationContext
    ) -> ValidationResult:
        """Execute the validation.

        Args:
            validation_spec: Validation configuration from YAML
            context: Validation context with base_dir and state

        Returns:
            ValidationResult with pass/fail and details
        """
        ...

    def validate_spec(self, validation_spec: Dict[str, Any]) -> list[str]:
        """Validate the validation spec during dry-run.

        Args:
            validation_spec: Validation configuration from YAML

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


class BaseValidator:
    """Base class for validator implementations (optional convenience)."""

    def __init__(self, validator_type: str):
        """Initialize validator.

        Args:
            validator_type: Unique type identifier
        """
        self._validator_type = validator_type

    @property
    def validator_type(self) -> str:
        """Get validator type."""
        return self._validator_type

    def can_handle(self, validation_type: str) -> bool:
        """Check if this validator handles the type."""
        return validation_type == self._validator_type

    def validate(
        self,
        validation_spec: Dict[str, Any],
        context: ValidationContext
    ) -> ValidationResult:
        """Execute validation (must be implemented by subclass)."""
        raise NotImplementedError

    def validate_spec(self, validation_spec: Dict[str, Any]) -> list[str]:
        """Validate spec (must be implemented by subclass)."""
        raise NotImplementedError
