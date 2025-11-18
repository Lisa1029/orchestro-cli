"""Tests for assertion parsing from YAML."""

import tempfile
from pathlib import Path

import pytest
import yaml

from orchestro_cli.parsing.scenario_parser import ScenarioParser


class TestAssertionParsing:
    """Test parsing inline assertions from YAML."""

    def test_parse_expect_output(self):
        """Test parsing expect_output assertion."""
        yaml_content = """
name: Test Scenario
command: echo hello
steps:
  - send: "echo hello"
  - expect_output: "hello"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            assert len(scenario.steps) == 2
            step = scenario.steps[1]
            assert step.expect_output == "hello"
            assert step.has_assertions
            assert len(step.assertions) == 1
            assert step.assertions[0]["type"] == "output"
        finally:
            path.unlink()

    def test_parse_expect_code(self):
        """Test parsing expect_code assertion."""
        yaml_content = """
name: Test Scenario
command: ls
steps:
  - send: "ls"
  - expect_code: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_code == 0
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_expect_contains(self):
        """Test parsing expect_contains assertion."""
        yaml_content = """
name: Test Scenario
command: echo test
steps:
  - send: "echo test"
  - expect_contains: "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_contains == "test"
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_expect_regex(self):
        """Test parsing expect_regex assertion."""
        yaml_content = """
name: Test Scenario
command: echo 123
steps:
  - send: "echo 123"
  - expect_regex: "^\\\\d+$"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_regex is not None
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_expect_lines(self):
        """Test parsing expect_lines assertion."""
        yaml_content = """
name: Test Scenario
command: cat file.txt
steps:
  - send: "cat file.txt"
  - expect_lines: 5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_lines == 5
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_expect_not_contains(self):
        """Test parsing expect_not_contains assertion."""
        yaml_content = """
name: Test Scenario
command: echo success
steps:
  - send: "echo success"
  - expect_not_contains: "error"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_not_contains == "error"
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_expect_json(self):
        """Test parsing expect_json assertion."""
        yaml_content = """
name: Test Scenario
command: cat data.json
steps:
  - send: "cat data.json"
  - expect_json:
      name: "test"
      value: 42
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_json is not None
            assert step.expect_json["name"] == "test"
            assert step.expect_json["value"] == 42
            assert step.has_assertions
        finally:
            path.unlink()

    def test_parse_multiple_assertions(self):
        """Test parsing multiple assertions on one step."""
        yaml_content = """
name: Test Scenario
command: echo hello
steps:
  - send: "echo hello world"
  - expect_output: "hello world"
    expect_contains: "hello"
    expect_regex: "^hello"
    expect_lines: 1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            step = scenario.steps[1]
            assert step.expect_output == "hello world"
            assert step.expect_contains == "hello"
            assert step.expect_regex == "^hello"
            assert step.expect_lines == 1
            assert step.has_assertions
            assert len(step.assertions) == 4
        finally:
            path.unlink()

    def test_parse_backward_compatibility(self):
        """Test that legacy format still works."""
        yaml_content = """
name: Test Scenario
command: echo test
steps:
  - send: "echo test"
  - expect: "test"
validations:
  - type: path_exists
    path: /tmp/test.txt
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            # Old format still works
            assert len(scenario.steps) == 2
            assert scenario.steps[1].expect == "test"
            assert len(scenario.validations) == 1
            assert scenario.validations[0].type == "path_exists"
        finally:
            path.unlink()

    def test_parse_mixed_old_and_new(self):
        """Test mixing old validations with new inline assertions."""
        yaml_content = """
name: Test Scenario
command: echo test
steps:
  - send: "echo test"
  - expect_output: "test"
validations:
  - type: path_exists
    path: /tmp/test.txt
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            # Both work together
            assert scenario.steps[1].expect_output == "test"
            assert scenario.steps[1].has_assertions
            assert len(scenario.validations) == 1
        finally:
            path.unlink()

    def test_step_without_assertions(self):
        """Test that steps without assertions work normally."""
        yaml_content = """
name: Test Scenario
command: echo test
steps:
  - send: "echo test"
  - note: "This is just a note"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            parser = ScenarioParser()
            scenario = parser.parse_file(path)

            assert not scenario.steps[0].has_assertions
            assert not scenario.steps[1].has_assertions
        finally:
            path.unlink()
