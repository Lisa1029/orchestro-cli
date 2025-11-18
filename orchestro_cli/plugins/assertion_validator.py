"""Assertion validator plugin for inline assertions.

This plugin provides backward-compatible integration of inline assertions
with the existing validation system.
"""

from typing import Any, Dict, List

from ..interfaces.validator_plugin import BaseValidator, ValidationContext, ValidationResult
from ..assertions.models import Assertion, AssertionType
from ..assertions.engine import AssertionEngine


class AssertionValidator(BaseValidator):
    """Validator plugin for inline assertions.

    Handles assertion-based validations and maintains backward compatibility
    with legacy validation formats.

    Supported assertion types:
    - expect_output: Exact output match
    - expect_code: Exit code match
    - expect_contains: Output contains text
    - expect_regex: Regex pattern match
    - expect_lines: Line count match
    - expect_not_contains: Output does not contain text
    - expect_json: JSON structure validation
    """

    def __init__(self):
        """Initialize assertion validator."""
        super().__init__("assertion")
        self.engine = AssertionEngine(fail_fast=False, verbose=False)

    def can_handle(self, validation_type: str) -> bool:
        """Check if this validator handles the type.

        Args:
            validation_type: Type from validation spec

        Returns:
            True if this is an assertion type
        """
        assertion_types = {
            "assertion",
            "expect_output",
            "expect_code",
            "expect_contains",
            "expect_regex",
            "expect_lines",
            "expect_not_contains",
            "expect_json",
        }
        return validation_type in assertion_types

    def validate(
        self,
        validation_spec: Dict[str, Any],
        context: ValidationContext
    ) -> ValidationResult:
        """Execute the assertion validation.

        Args:
            validation_spec: Validation configuration from YAML
            context: Validation context with state

        Returns:
            ValidationResult with pass/fail and details
        """
        validation_type = validation_spec.get("type", "assertion")
        expected = validation_spec.get("expected")
        actual = validation_spec.get("actual")

        if expected is None:
            return ValidationResult(
                passed=False,
                validator_type=self.validator_type,
                message="Missing 'expected' field in assertion",
            )

        # Map validation type to assertion type
        assertion_type_map = {
            "expect_output": AssertionType.OUTPUT,
            "expect_code": AssertionType.CODE,
            "expect_contains": AssertionType.CONTAINS,
            "expect_regex": AssertionType.REGEX,
            "expect_lines": AssertionType.LINES,
            "expect_not_contains": AssertionType.NOT_CONTAINS,
            "expect_json": AssertionType.JSON,
        }

        assertion_type = assertion_type_map.get(
            validation_type,
            AssertionType.OUTPUT  # Default
        )

        # Create and validate assertion
        assertion = Assertion(
            assertion_type=assertion_type,
            expected=expected,
            actual=actual,
        )

        try:
            result = self.engine.validate(assertion)

            return ValidationResult(
                passed=result.passed,
                validator_type=self.validator_type,
                message=result.error_message or "Assertion passed",
                details={
                    "assertion_type": assertion_type.value,
                    "expected": result.expected_value,
                    "actual": result.actual_value,
                    "diff": result.diff,
                } if not result.passed else None,
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                validator_type=self.validator_type,
                message=f"Assertion validation failed: {e}",
            )

    def validate_spec(self, validation_spec: Dict[str, Any]) -> List[str]:
        """Validate the validation spec during dry-run.

        Args:
            validation_spec: Validation configuration from YAML

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        validation_type = validation_spec.get("type")
        if not validation_type:
            errors.append("Missing 'type' field in assertion validation")
            return errors

        if not self.can_handle(validation_type):
            errors.append(f"Unknown assertion type: {validation_type}")
            return errors

        # Check for required 'expected' field
        if "expected" not in validation_spec:
            errors.append(f"Assertion '{validation_type}' requires 'expected' field")

        # Type-specific validation
        if validation_type == "expect_code":
            expected = validation_spec.get("expected")
            if expected is not None:
                try:
                    int(expected)
                except (ValueError, TypeError):
                    errors.append("expect_code requires integer expected value")

        if validation_type == "expect_lines":
            expected = validation_spec.get("expected")
            if expected is not None:
                try:
                    int(expected)
                except (ValueError, TypeError):
                    errors.append("expect_lines requires integer expected value")

        if validation_type == "expect_json":
            expected = validation_spec.get("expected")
            if expected is not None and not isinstance(expected, (dict, str)):
                errors.append("expect_json requires dict or JSON string")

        return errors


def register(registry):
    """Register the assertion validator plugin.

    Args:
        registry: Plugin registry to register with
    """
    validator = AssertionValidator()
    registry.register_validator_plugin(validator)
