"""Tests for inline assertion system."""

import json
import pytest

from orchestro_cli.assertions import AssertionEngine, Assertion, AssertionResult, AssertionType


class TestAssertionModels:
    """Test assertion model classes."""

    def test_assertion_creation(self):
        """Test creating an assertion."""
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="hello",
            actual="hello",
        )
        assert assertion.type_name == "output"
        assert assertion.expected == "hello"

    def test_assertion_result_status_icon(self):
        """Test status icons for pass/fail."""
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="test",
        )

        passed_result = AssertionResult(assertion=assertion, passed=True)
        assert passed_result.status_icon == "✓"

        failed_result = AssertionResult(assertion=assertion, passed=False)
        assert failed_result.status_icon == "❌"

    def test_assertion_result_format_failure(self):
        """Test failure message formatting."""
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="expected",
            line_number=42,
        )

        result = AssertionResult(
            assertion=assertion,
            passed=False,
            error_message="Values do not match",
            expected_value="expected",
            actual_value="actual",
        )

        formatted = result.format_failure()
        assert "❌" in formatted
        assert "output" in formatted
        assert "expected" in formatted
        assert "actual" in formatted
        assert "line 42" in formatted


class TestAssertionEngine:
    """Test assertion engine validation."""

    def test_validate_output_exact_match(self):
        """Test exact output matching."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="hello world",
            actual="hello world",
        )

        result = engine.validate(assertion)
        assert result.passed
        assert result.error_message is None

    def test_validate_output_mismatch(self):
        """Test output mismatch detection."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="hello",
            actual="goodbye",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert result.error_message is not None
        assert result.diff is not None

    def test_validate_code_match(self):
        """Test exit code validation."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.CODE,
            expected=0,
            actual=0,
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_code_mismatch(self):
        """Test exit code mismatch."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.CODE,
            expected=0,
            actual=1,
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "Exit code mismatch" in result.error_message

    def test_validate_contains_found(self):
        """Test contains assertion success."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.CONTAINS,
            expected="world",
            actual="hello world from test",
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_contains_not_found(self):
        """Test contains assertion failure."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.CONTAINS,
            expected="missing",
            actual="hello world",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "does not contain" in result.error_message

    def test_validate_not_contains_success(self):
        """Test not_contains assertion success."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.NOT_CONTAINS,
            expected="error",
            actual="success message",
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_not_contains_failure(self):
        """Test not_contains assertion failure."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.NOT_CONTAINS,
            expected="error",
            actual="error occurred",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "unexpectedly contains" in result.error_message

    def test_validate_regex_match(self):
        """Test regex pattern matching."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.REGEX,
            expected=r"hello \w+",
            actual="hello world",
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_regex_no_match(self):
        """Test regex pattern no match."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.REGEX,
            expected=r"^\d+$",
            actual="not numbers",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "does not match regex" in result.error_message

    def test_validate_regex_invalid_pattern(self):
        """Test invalid regex pattern."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.REGEX,
            expected=r"[invalid(",
            actual="test",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "Invalid regex" in result.error_message

    def test_validate_lines_match(self):
        """Test line count matching."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.LINES,
            expected=3,
            actual="line1\nline2\nline3",
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_lines_mismatch(self):
        """Test line count mismatch."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.LINES,
            expected=5,
            actual="line1\nline2",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "Line count mismatch" in result.error_message

    def test_validate_json_structure_match(self):
        """Test JSON structure validation."""
        engine = AssertionEngine(fail_fast=False)
        expected_json = {"name": "test", "value": 42}
        actual_json = json.dumps(expected_json)

        assertion = Assertion(
            assertion_type=AssertionType.JSON,
            expected=expected_json,
            actual=actual_json,
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_validate_json_structure_mismatch(self):
        """Test JSON structure mismatch."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.JSON,
            expected={"name": "test"},
            actual='{"name": "different"}',
        )

        result = engine.validate(assertion)
        assert not result.passed

    def test_validate_json_invalid(self):
        """Test invalid JSON handling."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.JSON,
            expected={"test": "value"},
            actual="not valid json",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "Invalid JSON" in result.error_message

    def test_fail_fast_mode(self):
        """Test fail-fast mode raises on first failure."""
        engine = AssertionEngine(fail_fast=True)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="hello",
            actual="goodbye",
        )

        with pytest.raises(AssertionError) as exc_info:
            engine.validate(assertion)

        assert "❌" in str(exc_info.value)

    def test_validate_all(self):
        """Test validating multiple assertions."""
        engine = AssertionEngine(fail_fast=False)
        assertions = [
            Assertion(
                assertion_type=AssertionType.OUTPUT,
                expected="test",
                actual="test",
            ),
            Assertion(
                assertion_type=AssertionType.CONTAINS,
                expected="world",
                actual="hello world",
            ),
            Assertion(
                assertion_type=AssertionType.CODE,
                expected=0,
                actual=0,
            ),
        ]

        results = engine.validate_all(assertions)
        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_get_summary(self):
        """Test getting validation summary."""
        engine = AssertionEngine(fail_fast=False)
        assertions = [
            Assertion(AssertionType.OUTPUT, expected="a", actual="a"),
            Assertion(AssertionType.OUTPUT, expected="b", actual="b"),
            Assertion(AssertionType.OUTPUT, expected="c", actual="x"),  # Fail
        ]

        engine.validate_all(assertions)
        summary = engine.get_summary()

        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(2/3)

    def test_has_failures(self):
        """Test failure detection."""
        engine = AssertionEngine(fail_fast=False)

        # No failures
        assertion1 = Assertion(AssertionType.OUTPUT, expected="a", actual="a")
        engine.validate(assertion1)
        assert not engine.has_failures()

        # Add failure
        assertion2 = Assertion(AssertionType.OUTPUT, expected="b", actual="c")
        engine.validate(assertion2)
        assert engine.has_failures()

    def test_clear_results(self):
        """Test clearing results."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(AssertionType.OUTPUT, expected="a", actual="a")
        engine.validate(assertion)

        assert len(engine.get_results()) == 1

        engine.clear_results()
        assert len(engine.get_results()) == 0


class TestAssertionEngineEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_assertion_type(self):
        """Test handling unknown assertion type."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.CUSTOM,  # Not implemented
            expected="test",
            actual="test",
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert "Unknown assertion type" in result.error_message

    def test_output_with_whitespace(self):
        """Test output comparison with whitespace."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="  hello  ",
            actual="hello",
        )

        result = engine.validate(assertion)
        assert result.passed  # Whitespace is stripped

    def test_empty_output(self):
        """Test handling empty output."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="",
            actual="",
        )

        result = engine.validate(assertion)
        assert result.passed

    def test_none_actual_value(self):
        """Test handling None actual value."""
        engine = AssertionEngine(fail_fast=False)
        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected="test",
            actual=None,
        )

        result = engine.validate(assertion)
        assert not result.passed

    def test_multiline_diff(self):
        """Test diff generation for multiline strings."""
        engine = AssertionEngine(fail_fast=False)
        expected = "line1\nline2\nline3"
        actual = "line1\nmodified\nline3"

        assertion = Assertion(
            assertion_type=AssertionType.OUTPUT,
            expected=expected,
            actual=actual,
        )

        result = engine.validate(assertion)
        assert not result.passed
        assert result.diff is not None
        assert "modified" in result.diff
