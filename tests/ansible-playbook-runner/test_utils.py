import os
import tempfile
import pytest
import yaml
from ansible_playbook_runner.utils import (
    sanitize_input,
    parse_extra_vars,
    parse_value,
    validate_playbook,
    format_ansible_result
)

class TestUtils:
    def test_sanitize_input(self):
        """Test sanitizing user input."""
        # Test basic string
        assert sanitize_input("simple_string") == "simple_string"
        
        # Test string with spaces
        assert sanitize_input("string with spaces") == "'string with spaces'"
        
        # Test string with special characters
        assert sanitize_input("string; with; semicolons") == "'string; with; semicolons'"
        
        # Test potential command injection
        dangerous_input = "; rm -rf / #"
        sanitized = sanitize_input(dangerous_input)
        assert "rm" not in sanitized or sanitized.startswith("'") or sanitized.startswith('"')

    def test_parse_extra_vars(self):
        """Test parsing extra variables."""
        # Test basic key=value
        result = parse_extra_vars(["key=value"])
        assert result == {"key": "value"}
        
        # Test multiple values
        result = parse_extra_vars(["key1=value1", "key2=value2"])
        assert result == {"key1": "value1", "key2": "value2"}
        
        # Test different types
        result = parse_extra_vars(["str=hello", "num=42", "bool=true", "null=null"])
        assert result == {"str": "hello", "num": 42, "bool": True, "null": None}
        
        # Test invalid format
        result = parse_extra_vars(["invalid_format", "key=value"])
        assert result == {"key": "value"}

    def test_parse_value(self):
        """Test parsing string values to appropriate types."""
        # Test string
        assert parse_value("hello") == "hello"
        
        # Test integer
        assert parse_value("42") == 42
        
        # Test float
        assert parse_value("3.14") == 3.14
        
        # Test boolean
        assert parse_value("true") is True
        assert parse_value("false") is False
        assert parse_value("yes") is True
        assert parse_value("no") is False
        
        # Test null
        assert parse_value("null") is None
        assert parse_value("none") is None

    def test_validate_playbook(self):
        """Test validating a playbook."""
        # Create a valid playbook file
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as valid_file:
            valid_content = """---
- name: Valid playbook
  hosts: localhost
  tasks:
    - name: Echo something
      debug:
        msg: Hello world
"""
            valid_file.write(valid_content.encode())
            valid_path = valid_file.name
        
        # Create an invalid playbook file
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as invalid_file:
            invalid_content = """---
# This is not a valid playbook, just a string
invalid_content: this is not a list
"""
            invalid_file.write(invalid_content.encode())
            invalid_path = invalid_file.name
        
        try:
            # Test valid playbook
            assert validate_playbook(valid_path) is True
            
            # Test invalid playbook
            assert validate_playbook(invalid_path) is False
            
            # Test non-existent file
            assert validate_playbook("/nonexistent/file.yml") is False
        finally:
            # Clean up
            os.unlink(valid_path)
            os.unlink(invalid_path)

    def test_format_ansible_result(self):
        """Test formatting Ansible results."""
        # Test successful result
        success_result = {
            "status": "successful",
            "rc": 0,
            "success": True,
            "stats": {
                "localhost": {
                    "ok": 2,
                    "changed": 1,
                    "unreachable": 0,
                    "failed": 0
                }
            }
        }
        formatted = format_ansible_result(success_result)
        assert "✅" in formatted
        assert "successful" in formatted
        assert "Return code: 0" in formatted
        assert "localhost" in formatted
        
        # Test failed result
        failed_result = {
            "status": "failed",
            "rc": 1,
            "success": False,
            "stats": {
                "localhost": {
                    "ok": 1,
                    "changed": 0,
                    "unreachable": 0,
                    "failed": 1
                }
            }
        }
        formatted = format_ansible_result(failed_result)
        assert "❌" in formatted
        assert "failed" in formatted
        assert "Return code: 1" in formatted
