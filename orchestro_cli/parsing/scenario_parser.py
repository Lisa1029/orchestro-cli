"""Scenario parser - responsible ONLY for parsing YAML into domain objects."""

from pathlib import Path
from typing import Dict, Any, List
import yaml

from .models import Scenario, Step, Validation


class ScenarioParser:
    """Parses YAML scenario files into domain objects.

    Single Responsibility: Convert YAML → Scenario objects
    """

    def parse_file(self, path: Path) -> Scenario:
        """Parse YAML file into Scenario object.

        Args:
            path: Path to YAML scenario file

        Returns:
            Parsed Scenario object

        Raises:
            FileNotFoundError: If scenario file doesn't exist
            yaml.YAMLError: If YAML is malformed
            ValueError: If scenario structure is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return self._build_scenario(data)

    def _build_scenario(self, data: Dict[str, Any]) -> Scenario:
        """Build scenario from parsed YAML data."""
        return Scenario(
            name=data.get('name', 'Unnamed Scenario'),
            description=data.get('description'),
            command=data.get('command'),
            timeout=float(data.get('timeout', 30)),
            env=data.get('env', {}),
            steps=self._parse_steps(data.get('steps', [])),
            validations=self._parse_validations(data.get('validations', []))
        )

    def _parse_steps(self, raw_steps: List[Dict]) -> List[Step]:
        """Parse step definitions from YAML.

        Supports both 'expect' and 'pattern' keys for backward compatibility.
        Also parses inline assertion keywords.
        """
        steps: List[Step] = []
        for raw in raw_steps:
            # Support both "expect" and "pattern" for compatibility
            expect_pattern = raw.get("expect") or raw.get("pattern")

            # Parse inline assertions
            assertions = []
            assertion_fields = {
                "expect_output": raw.get("expect_output"),
                "expect_code": raw.get("expect_code"),
                "expect_contains": raw.get("expect_contains"),
                "expect_regex": raw.get("expect_regex"),
                "expect_lines": raw.get("expect_lines"),
                "expect_not_contains": raw.get("expect_not_contains"),
                "expect_json": raw.get("expect_json"),
            }

            # Collect assertion metadata for processing
            for field_name, field_value in assertion_fields.items():
                if field_value is not None:
                    assertions.append({
                        "type": field_name.replace("expect_", ""),
                        "expected": field_value,
                    })

            steps.append(
                Step(
                    expect=expect_pattern,
                    send=raw.get("send"),
                    control=raw.get("control"),
                    note=raw.get("note"),
                    timeout=raw.get("timeout"),
                    raw=bool(raw.get("raw", False)),
                    screenshot=raw.get("screenshot"),
                    # Inline assertions
                    expect_output=raw.get("expect_output"),
                    expect_code=raw.get("expect_code"),
                    expect_contains=raw.get("expect_contains"),
                    expect_regex=raw.get("expect_regex"),
                    expect_lines=raw.get("expect_lines"),
                    expect_not_contains=raw.get("expect_not_contains"),
                    expect_json=raw.get("expect_json"),
                    assertions=assertions,
                )
            )
        return steps

    def _parse_validations(self, raw_validations: List[Dict]) -> List[Validation]:
        """Parse validation definitions from YAML."""
        validations: List[Validation] = []
        for raw in raw_validations:
            validation = Validation(
                type=raw.get("type"),
                path=raw.get("path"),
                text=raw.get("text"),
                description=raw.get("description")
            )
            # Validate completeness
            validation.validate_completeness()
            validations.append(validation)
        return validations
